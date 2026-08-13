from __future__ import annotations

from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from .database import Database

_MODELOS_CARGADOS = {}

class VectorStore:
    """
    Memoria vectorial semántica de ATENAS.

    Convierte recuerdos en embeddings y permite buscar
    memorias por significado, aunque no compartan exactamente
    las mismas palabras.

    Los metadatos se guardan en SQLite.
    Los embeddings se guardan como archivos .npy.
    """

    MODELO_DEFAULT = (
        "sentence-transformers/"
        "paraphrase-multilingual-MiniLM-L12-v2"
    )

    def __init__(
        self,
        db: Database | None = None,
        ruta_vectores: str = "data/vectors",
        modelo: str | None = None,
    ):
        self.db = db or Database()

        self.ruta_vectores = Path(
            ruta_vectores
        )

        self.ruta_vectores.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.nombre_modelo = (
            modelo
            or self.MODELO_DEFAULT
        )

        # =========================================================
        # MODELO COMPARTIDO
        # =========================================================

        if self.nombre_modelo in _MODELOS_CARGADOS:

            self.modelo = _MODELOS_CARGADOS[
                self.nombre_modelo
            ]

            print(
                "[ATENAS][VECTOR] "
                "Usando modelo semántico ya cargado."
            )

        else:

            print(
                "[ATENAS][VECTOR] "
                "Cargando modelo semántico..."
            )

            self.modelo = SentenceTransformer(
                self.nombre_modelo
            )

            _MODELOS_CARGADOS[
                self.nombre_modelo
            ] = self.modelo

            print(
                "[ATENAS][VECTOR] "
                "Modelo semántico disponible."
            )
    # =========================================================
    # EMBEDDING
    # =========================================================

    def generar_embedding(
        self,
        texto: str,
    ) -> np.ndarray:

        texto = texto.strip()

        if not texto:
            raise ValueError(
                "No se puede generar un embedding "
                "de un texto vacío."
            )

        vector = self.modelo.encode(
            texto,
            convert_to_numpy=True,
        )

        vector = np.asarray(
            vector,
            dtype=np.float32,
        )

        # Normalización L2.
        # Así el producto punto equivale a similitud coseno.

        norma = np.linalg.norm(
            vector
        )

        if norma > 0:
            vector = vector / norma

        return vector

    # =========================================================
    # RUTA
    # =========================================================

    def _ruta_vector(
        self,
        memoria_tipo: str,
        memoria_id: int,
    ) -> Path:

        nombre = (
            f"{memoria_tipo}_"
            f"{memoria_id}.npy"
        )

        return (
            self.ruta_vectores
            / nombre
        )

    # =========================================================
    # GUARDAR
    # =========================================================

    def guardar(
        self,
        memoria_tipo: str,
        memoria_id: int,
        contenido: str,
        dominio: str = "general",
        categoria: str = "general",
        importancia: float = 0.5,
        confianza: float = 0.7,
    ) -> int:

        contenido = contenido.strip()

        if not contenido:
            raise ValueError(
                "La memoria vectorial no puede "
                "guardar contenido vacío."
            )

        # -----------------------------------------------------
        # GENERAR EMBEDDING
        # -----------------------------------------------------

        vector = self.generar_embedding(
            contenido
        )

        # -----------------------------------------------------
        # GUARDAR VECTOR
        # -----------------------------------------------------

        ruta = self._ruta_vector(
            memoria_tipo,
            memoria_id,
        )

        np.save(
            ruta,
            vector,
        )

        # -----------------------------------------------------
        # REGISTRAR METADATOS
        # -----------------------------------------------------

        with self.db.conexion() as conn:

            existente = conn.execute("""
                SELECT id
                FROM vector_memories

                WHERE memoria_tipo = ?
                  AND memoria_id = ?

                LIMIT 1
            """, (
                memoria_tipo,
                memoria_id,
            )).fetchone()

            if existente:

                vector_id = int(
                    existente["id"]
                )

                conn.execute("""
                    UPDATE vector_memories

                    SET
                        contenido = ?,
                        dominio = ?,
                        categoria = ?,
                        vector_path = ?,
                        modelo = ?,
                        dimensiones = ?,
                        importancia = ?,
                        confianza = ?,
                        actualizado_en =
                            CURRENT_TIMESTAMP

                    WHERE id = ?
                """, (
                    contenido,
                    dominio,
                    categoria,
                    str(ruta),
                    self.nombre_modelo,
                    int(vector.shape[0]),
                    importancia,
                    confianza,
                    vector_id,
                ))

                return vector_id

            cursor = conn.execute("""
                INSERT INTO vector_memories (
                    memoria_tipo,
                    memoria_id,
                    contenido,
                    dominio,
                    categoria,
                    vector_path,
                    modelo,
                    dimensiones,
                    importancia,
                    confianza
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memoria_tipo,
                memoria_id,
                contenido,
                dominio,
                categoria,
                str(ruta),
                self.nombre_modelo,
                int(vector.shape[0]),
                importancia,
                confianza,
            ))

            return int(
                cursor.lastrowid
            )

    # =========================================================
    # CARGAR VECTOR
    # =========================================================

    @staticmethod
    def _cargar_vector(
        ruta: str,
    ) -> np.ndarray | None:

        path = Path(
            ruta
        )

        if not path.exists():
            return None

        try:

            vector = np.load(
                path
            )

            return np.asarray(
                vector,
                dtype=np.float32,
            )

        except Exception as error:

            print(
                "[ATENAS][VECTOR] "
                f"No se pudo cargar {ruta}: "
                f"{error}"
            )

            return None

    # =========================================================
    # SIMILITUD
    # =========================================================

    @staticmethod
    def similitud_coseno(
        vector_a: np.ndarray,
        vector_b: np.ndarray,
    ) -> float:

        if (
            vector_a.size == 0
            or vector_b.size == 0
        ):
            return 0.0

        # Como los vectores ya están normalizados,
        # basta el producto punto.

        similitud = np.dot(
            vector_a,
            vector_b,
        )

        return float(
            np.clip(
                similitud,
                -1.0,
                1.0,
            )
        )

    # =========================================================
    # BUSCAR SEMÁNTICAMENTE
    # =========================================================

    def buscar(
        self,
        consulta: str,
        limite: int = 8,
        similitud_minima: float = 0.35,
        dominio: str | None = None,
    ) -> list[dict]:

        consulta = consulta.strip()

        if not consulta:
            return []

        vector_consulta = (
            self.generar_embedding(
                consulta
            )
        )

        # -----------------------------------------------------
        # RECUPERAR ÍNDICE
        # -----------------------------------------------------

        with self.db.conexion() as conn:

            if dominio:

                rows = conn.execute("""
                    SELECT *
                    FROM vector_memories

                    WHERE LOWER(dominio)
                          = LOWER(?)
                """, (
                    dominio,
                )).fetchall()

            else:

                rows = conn.execute("""
                    SELECT *
                    FROM vector_memories
                """).fetchall()

        resultados = []

        # -----------------------------------------------------
        # COMPARAR
        # -----------------------------------------------------

        for row in rows:

            memoria = dict(row)

            vector_memoria = (
                self._cargar_vector(
                    memoria[
                        "vector_path"
                    ]
                )
            )

            if vector_memoria is None:
                continue

            # Por seguridad, no comparar
            # vectores de dimensiones diferentes.

            if (
                vector_memoria.shape
                != vector_consulta.shape
            ):
                continue

            similitud = (
                self.similitud_coseno(
                    vector_consulta,
                    vector_memoria,
                )
            )

            if (
                similitud
                < similitud_minima
            ):
                continue

            memoria[
                "similitud_semantica"
            ] = similitud

            memoria[
                "_tipo_recuperacion"
            ] = "vectorial"

            resultados.append(
                memoria
            )

        # -----------------------------------------------------
        # ORDENAR
        # -----------------------------------------------------

        resultados.sort(
            key=lambda item: (
                item[
                    "similitud_semantica"
                ]
            ),
            reverse=True,
        )

        return resultados[:limite]

    # =========================================================
    # OBTENER POR MEMORIA
    # =========================================================

    def obtener_por_memoria(
        self,
        memoria_tipo: str,
        memoria_id: int,
    ) -> dict | None:

        with self.db.conexion() as conn:

            row = conn.execute("""
                SELECT *
                FROM vector_memories

                WHERE memoria_tipo = ?
                  AND memoria_id = ?

                LIMIT 1
            """, (
                memoria_tipo,
                memoria_id,
            )).fetchone()

        return (
            dict(row)
            if row
            else None
        )

    # =========================================================
    # ELIMINAR
    # =========================================================

    def eliminar(
        self,
        memoria_tipo: str,
        memoria_id: int,
    ) -> bool:

        memoria = (
            self.obtener_por_memoria(
                memoria_tipo,
                memoria_id,
            )
        )

        if not memoria:
            return False

        ruta = Path(
            memoria["vector_path"]
        )

        if ruta.exists():

            try:
                ruta.unlink()

            except Exception as error:

                print(
                    "[ATENAS][VECTOR] "
                    f"No fue posible eliminar "
                    f"{ruta}: {error}"
                )

        with self.db.conexion() as conn:

            conn.execute("""
                DELETE FROM vector_memories

                WHERE memoria_tipo = ?
                  AND memoria_id = ?
            """, (
                memoria_tipo,
                memoria_id,
            ))

        return True

    # =========================================================
    # ESTADÍSTICAS
    # =========================================================

    def estadisticas(
        self,
    ) -> dict:

        with self.db.conexion() as conn:

            row = conn.execute("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(
                        DISTINCT dominio
                    ) AS dominios

                FROM vector_memories
            """).fetchone()

        return {
            "total": int(
                row["total"]
                or 0
            ),
            "dominios": int(
                row["dominios"]
                or 0
            ),
            "modelo": self.nombre_modelo,
        }

    # =========================================================
    # INDEXAR MEMORIAS EXISTENTES
    # =========================================================

    def indexar_existentes(self) -> dict:
        """
        Crea embeddings para memorias semánticas y episódicas
        que ya existían antes de activar VectorStore.
        """

        creadas = 0
        existentes = 0
        errores = 0

        # =====================================================
        # MEMORIAS SEMÁNTICAS
        # =====================================================

        with self.db.conexion() as conn:
            memorias_semanticas = conn.execute("""
                SELECT *
                FROM memoria_semantica
                WHERE activa = 1
            """).fetchall()

        for row in memorias_semanticas:
            memoria = dict(row)

            ya_existe = self.obtener_por_memoria(
                "semantica",
                memoria["id"],
            )

            if ya_existe:
                existentes += 1
                continue

            try:
                self.guardar(
                    memoria_tipo="semantica",
                    memoria_id=memoria["id"],
                    contenido=memoria["contenido"],
                    dominio=memoria["dominio"] or "general",
                    categoria=memoria["categoria"] or "general",
                    importancia=memoria["importancia"] or 0.5,
                    confianza=memoria["confianza"] or 0.7,
                )

                creadas += 1

            except Exception as error:
                errores += 1

                print(
                    "[ATENAS][VECTOR] "
                    f"Error indexando memoria semántica "
                    f"{memoria['id']}: {error}"
                )

        # =====================================================
        # MEMORIAS EPISÓDICAS
        # =====================================================

        with self.db.conexion() as conn:
            memorias_episodicas = conn.execute("""
                SELECT *
                FROM memoria_episodica
            """).fetchall()

        for row in memorias_episodicas:
            memoria = dict(row)

            ya_existe = self.obtener_por_memoria(
                "episodica",
                memoria["id"],
            )

            if ya_existe:
                existentes += 1
                continue

            try:
                self.guardar(
                    memoria_tipo="episodica",
                    memoria_id=memoria["id"],
                    contenido=memoria["descripcion"],
                    dominio="experiencias",
                    categoria="episodio",
                    importancia=memoria["importancia"] or 0.5,
                    confianza=memoria["confianza"] or 0.7,
                )

                creadas += 1

            except Exception as error:
                errores += 1

                print(
                    "[ATENAS][VECTOR] "
                    f"Error indexando memoria episódica "
                    f"{memoria['id']}: {error}"
                )

        return {
            "creadas": creadas,
            "existentes": existentes,
            "errores": errores,
        }