from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class EstadoPropuesta(str, Enum):
    PENDIENTE = "pendiente"
    VALIDADA = "validada"
    APLICADA = "aplicada"
    RECHAZADA = "rechazada"
    DESCARTADA = "descartada"
    FALLIDA = "fallida"
    OBSOLETA = "obsoleta"


@dataclass
class PropuestaPersistida:
    id: str

    archivo: str
    tipo_hallazgo: str
    descripcion: str

    razon: str

    diff: str
    contenido_nuevo: str

    hash_original: str | None

    severidad: float
    confianza: float

    riesgo: str

    requiere_confirmacion: bool

    estado: EstadoPropuesta

    creada_en: str
    actualizada_en: str

    cambio_id: str | None = None

    metadata: dict[str, Any] | None = None


class RegistroPropuestasMejora:
    """
    Persistencia de propuestas de automejora.

    Guarda además el hash del archivo original usado para crear
    la propuesta. Esto permite detectar propuestas obsoletas
    después de reiniciar ATENAS.
    """

    def __init__(
        self,
        db_path: str | Path,
    ):
        self.db_path = Path(
            db_path
        ).resolve()

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._crear_tabla()
        self._migrar_esquema()

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _ahora() -> str:

        return (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

    @staticmethod
    def hash_contenido(
        contenido: str,
    ) -> str:

        return hashlib.sha256(
            contenido.encode(
                "utf-8"
            )
        ).hexdigest()

    def _conexion(
        self,
    ) -> sqlite3.Connection:

        conn = sqlite3.connect(
            str(
                self.db_path
            ),
            timeout=10.0,
        )

        conn.row_factory = (
            sqlite3.Row
        )

        return conn

    # =========================================================
    # ESQUEMA
    # =========================================================

    def _crear_tabla(
        self,
    ) -> None:

        with closing(
            self._conexion()
        ) as conn:

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS propuestas_mejora (
                    id TEXT PRIMARY KEY,
                    archivo TEXT NOT NULL,
                    tipo_hallazgo TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    razon TEXT NOT NULL,
                    diff TEXT NOT NULL,
                    contenido_nuevo TEXT NOT NULL,
                    hash_original TEXT,
                    severidad REAL NOT NULL,
                    confianza REAL NOT NULL,
                    riesgo TEXT NOT NULL,
                    requiere_confirmacion INTEGER NOT NULL,
                    estado TEXT NOT NULL,
                    creada_en TEXT NOT NULL,
                    actualizada_en TEXT NOT NULL,
                    cambio_id TEXT,
                    metadata_json TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_propuestas_estado
                ON propuestas_mejora(estado)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_propuestas_archivo
                ON propuestas_mejora(archivo)
                """
            )

            conn.commit()

    def _migrar_esquema(
        self,
    ) -> None:
        """
        Hace compatible una base creada por la versión anterior,
        que todavía no tenía hash_original.
        """

        with closing(
            self._conexion()
        ) as conn:

            columnas = {
                fila["name"]
                for fila in conn.execute(
                    "PRAGMA table_info(propuestas_mejora)"
                ).fetchall()
            }

            if (
                "hash_original"
                not in columnas
            ):

                conn.execute(
                    """
                    ALTER TABLE propuestas_mejora
                    ADD COLUMN hash_original TEXT
                    """
                )

            conn.commit()

    # =========================================================
    # CONVERTIR
    # =========================================================

    @staticmethod
    def _fila_a_propuesta(
        fila: sqlite3.Row,
    ) -> PropuestaPersistida:

        metadata = None

        if fila["metadata_json"]:

            try:

                metadata = json.loads(
                    fila[
                        "metadata_json"
                    ]
                )

            except Exception:

                metadata = {
                    "raw": fila[
                        "metadata_json"
                    ]
                }

        return PropuestaPersistida(
            id=fila["id"],

            archivo=fila["archivo"],

            tipo_hallazgo=(
                fila["tipo_hallazgo"]
            ),

            descripcion=(
                fila["descripcion"]
            ),

            razon=fila["razon"],

            diff=fila["diff"],

            contenido_nuevo=(
                fila[
                    "contenido_nuevo"
                ]
            ),

            hash_original=(
                fila["hash_original"]
            ),

            severidad=float(
                fila["severidad"]
            ),

            confianza=float(
                fila["confianza"]
            ),

            riesgo=fila["riesgo"],

            requiere_confirmacion=bool(
                fila[
                    "requiere_confirmacion"
                ]
            ),

            estado=EstadoPropuesta(
                fila["estado"]
            ),

            creada_en=(
                fila["creada_en"]
            ),

            actualizada_en=(
                fila["actualizada_en"]
            ),

            cambio_id=(
                fila["cambio_id"]
            ),

            metadata=metadata,
        )

    # =========================================================
    # GUARDAR
    # =========================================================

    def guardar(
        self,
        propuesta,
        metadata: dict[str, Any] | None = None,
    ) -> PropuestaPersistida:

        if (
            propuesta is None
            or not getattr(
                propuesta,
                "ok",
                False,
            )
            or getattr(
                propuesta,
                "cambio",
                None,
            )
            is None
        ):

            raise ValueError(
                "Solo se pueden persistir "
                "propuestas válidas."
            )

        hallazgo = propuesta.hallazgo
        cambio = propuesta.cambio
        verificacion = (
            propuesta.verificacion
        )

        riesgo = "desconocido"
        requiere_confirmacion = True

        if verificacion is not None:

            riesgo_obj = getattr(
                verificacion,
                "riesgo",
                None,
            )

            riesgo = (
                getattr(
                    riesgo_obj,
                    "value",
                    None,
                )
                or str(
                    riesgo_obj
                )
            )

            requiere_confirmacion = bool(
                getattr(
                    verificacion,
                    "requiere_confirmacion",
                    True,
                )
            )

        hash_original = getattr(
            cambio,
            "hash_original",
            None,
        )

        if not hash_original:

            contenido_original = getattr(
                cambio,
                "contenido_original",
                None,
            )

            if isinstance(
                contenido_original,
                str,
            ):

                hash_original = (
                    self.hash_contenido(
                        contenido_original
                    )
                )

        propuesta_id = str(
            uuid.uuid4()
        )

        ahora = self._ahora()

        registro = PropuestaPersistida(
            id=propuesta_id,
            archivo=hallazgo.archivo,
            tipo_hallazgo=(
                hallazgo.tipo.value
            ),
            descripcion=(
                hallazgo.descripcion
            ),
            razon=(
                getattr(
                    cambio,
                    "razon",
                    "",
                )
                or propuesta.mensaje
            ),
            diff=cambio.diff,
            contenido_nuevo=(
                cambio.contenido_nuevo
            ),
            hash_original=(
                hash_original
            ),
            severidad=float(
                hallazgo.severidad
            ),
            confianza=float(
                hallazgo.confianza
            ),
            riesgo=riesgo,
            requiere_confirmacion=(
                requiere_confirmacion
            ),
            estado=(
                EstadoPropuesta.VALIDADA
            ),
            creada_en=ahora,
            actualizada_en=ahora,
            metadata=(
                metadata
                or {}
            ),
        )

        with closing(
            self._conexion()
        ) as conn:

            conn.execute(
                """
                INSERT INTO propuestas_mejora (
                    id,
                    archivo,
                    tipo_hallazgo,
                    descripcion,
                    razon,
                    diff,
                    contenido_nuevo,
                    hash_original,
                    severidad,
                    confianza,
                    riesgo,
                    requiere_confirmacion,
                    estado,
                    creada_en,
                    actualizada_en,
                    cambio_id,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    registro.id,
                    registro.archivo,
                    registro.tipo_hallazgo,
                    registro.descripcion,
                    registro.razon,
                    registro.diff,
                    registro.contenido_nuevo,
                    registro.hash_original,
                    registro.severidad,
                    registro.confianza,
                    registro.riesgo,
                    int(
                        registro
                        .requiere_confirmacion
                    ),
                    registro.estado.value,
                    registro.creada_en,
                    registro.actualizada_en,
                    None,
                    json.dumps(
                        registro.metadata,
                        ensure_ascii=False,
                        default=str,
                    ),
                ),
            )

            conn.commit()

        return registro

    # =========================================================
    # CONSULTAS
    # =========================================================

    def obtener(
        self,
        propuesta_id: str,
    ) -> PropuestaPersistida | None:

        with closing(
            self._conexion()
        ) as conn:

            fila = conn.execute(
                """
                SELECT *
                FROM propuestas_mejora
                WHERE id = ?
                LIMIT 1
                """,
                (
                    propuesta_id,
                ),
            ).fetchone()

        if fila is None:
            return None

        return self._fila_a_propuesta(
            fila
        )

    def listar(
        self,
        estado: EstadoPropuesta | None = None,
        limite: int = 100,
    ) -> list[PropuestaPersistida]:

        limite = max(
            1,
            int(limite),
        )

        sql = """
            SELECT *
            FROM propuestas_mejora
        """

        parametros: list[Any] = []

        if estado is not None:

            sql += """
                WHERE estado = ?
            """

            parametros.append(
                estado.value
            )

        sql += """
            ORDER BY creada_en DESC
            LIMIT ?
        """

        parametros.append(
            limite
        )

        with closing(
            self._conexion()
        ) as conn:

            filas = conn.execute(
                sql,
                tuple(
                    parametros
                ),
            ).fetchall()

        return [
            self._fila_a_propuesta(
                fila
            )
            for fila in filas
        ]

    def pendientes(
        self,
        limite: int = 50,
    ) -> list[PropuestaPersistida]:

        return self.listar(
            estado=(
                EstadoPropuesta.VALIDADA
            ),
            limite=limite,
        )

    # =========================================================
    # ESTADOS
    # =========================================================

    def marcar_estado(
        self,
        propuesta_id: str,
        estado: EstadoPropuesta,
        cambio_id: str | None = None,
    ) -> PropuestaPersistida:

        ahora = self._ahora()

        with closing(
            self._conexion()
        ) as conn:

            cursor = conn.execute(
                """
                UPDATE propuestas_mejora
                SET
                    estado = ?,
                    actualizada_en = ?,
                    cambio_id = COALESCE(?, cambio_id)
                WHERE id = ?
                """,
                (
                    estado.value,
                    ahora,
                    cambio_id,
                    propuesta_id,
                ),
            )

            conn.commit()

            if cursor.rowcount == 0:

                raise KeyError(
                    "Propuesta no encontrada: "
                    f"{propuesta_id}"
                )

        propuesta = self.obtener(
            propuesta_id
        )

        assert propuesta is not None

        return propuesta

    def marcar_aplicada(
        self,
        propuesta_id: str,
        cambio_id: str,
    ) -> PropuestaPersistida:

        return self.marcar_estado(
            propuesta_id,
            EstadoPropuesta.APLICADA,
            cambio_id=cambio_id,
        )

    def marcar_obsoleta(
        self,
        propuesta_id: str,
    ) -> PropuestaPersistida:

        return self.marcar_estado(
            propuesta_id,
            EstadoPropuesta.OBSOLETA,
        )

    def marcar_fallida(
        self,
        propuesta_id: str,
    ) -> PropuestaPersistida:

        return self.marcar_estado(
            propuesta_id,
            EstadoPropuesta.FALLIDA,
        )

    def rechazar(
        self,
        propuesta_id: str,
    ) -> PropuestaPersistida:

        return self.marcar_estado(
            propuesta_id,
            EstadoPropuesta.RECHAZADA,
        )

    def descartar(
        self,
        propuesta_id: str,
    ) -> PropuestaPersistida:

        return self.marcar_estado(
            propuesta_id,
            EstadoPropuesta.DESCARTADA,
        )

    # =========================================================
    # CONTEXTO
    # =========================================================

    def contexto_para_llm(
        self,
        limite: int = 10,
    ) -> str:

        pendientes = (
            self.pendientes(
                limite=limite
            )
        )

        if not pendientes:

            return (
                "PROPUESTAS DE AUTOMEJORA "
                "PENDIENTES:\n"
                "- Ninguna."
            )

        lineas = [
            "PROPUESTAS DE AUTOMEJORA PENDIENTES:"
        ]

        for propuesta in pendientes:

            lineas.append(
                (
                    f"- {propuesta.id} | "
                    f"{propuesta.tipo_hallazgo} | "
                    f"{propuesta.archivo} | "
                    f"riesgo={propuesta.riesgo} | "
                    f"confirmación="
                    f"{'sí' if propuesta.requiere_confirmacion else 'no'}"
                )
            )

            lineas.append(
                "  "
                + propuesta.descripcion
            )

        return "\n".join(
            lineas
        )
