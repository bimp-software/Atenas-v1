from __future__ import annotations

from src.atenas.memoria.store_manager import StorageManager
from .clasificador import ClasificadorMemoria


class RecuperadorMemoria:
    """
    Recuperador de memoria de ATENAS.

    Combina:
    - memoria semántica textual;
    - memoria episódica;
    - memoria vectorial;
    - grafo de conocimiento.

    Después ordena los recuerdos por relevancia antes
    de entregarlos al modelo de lenguaje.
    """

    def __init__(
        self,
        storage: StorageManager | None = None,
    ):
        self.storage = (
            storage
            or StorageManager()
        )

        self.clasificador = (
            ClasificadorMemoria()
        )

    # =========================================================
    # BUSCAR
    # =========================================================

    def buscar(
        self,
        consulta: str,
        limite: int = 8,
    ) -> list[dict]:

        consulta = consulta.strip()

        if not consulta:
            return []

        clasificacion = (
            self.clasificador.clasificar(
                consulta
            )
        )

        resultados: list[dict] = []

        # =====================================================
        # 1. MEMORIA SEMÁNTICA DEL DOMINIO
        # =====================================================

        if clasificacion.dominio not in {
            "general",
            "experiencias",
        }:

            memorias_dominio = (
                self.storage.semantica.buscar(
                    consulta=consulta,
                    dominio=clasificacion.dominio,
                    limite=limite,
                )
            )

            for memoria in memorias_dominio:

                memoria["_tipo_memoria"] = (
                    "semantica"
                )

                memoria["_tipo_recuperacion"] = (
                    "textual"
                )

                resultados.append(
                    memoria
                )

        # =====================================================
        # 2. MEMORIA SEMÁNTICA GENERAL
        # =====================================================

        generales = (
            self.storage.semantica.buscar(
                consulta=consulta,
                limite=limite,
            )
        )

        ids_existentes = {
            (
                memoria.get(
                    "_tipo_memoria",
                    "semantica",
                ),
                memoria.get("id"),
            )
            for memoria in resultados
        }

        for memoria in generales:

            identificador = (
                "semantica",
                memoria["id"],
            )

            if identificador in ids_existentes:
                continue

            memoria["_tipo_memoria"] = (
                "semantica"
            )

            memoria["_tipo_recuperacion"] = (
                "textual"
            )

            resultados.append(
                memoria
            )

            ids_existentes.add(
                identificador
            )

        # =====================================================
        # 3. MEMORIA EPISÓDICA
        # =====================================================

        episodios = (
            self.storage.episodica.buscar(
                consulta,
                limite=3,
            )
        )

        for episodio in episodios:

            identificador = (
                "episodica",
                episodio["id"],
            )

            if identificador in ids_existentes:
                continue

            episodio["_tipo_memoria"] = (
                "episodica"
            )

            episodio["_tipo_recuperacion"] = (
                "textual"
            )

            resultados.append(
                episodio
            )

            ids_existentes.add(
                identificador
            )

        # =====================================================
        # 4. MEMORIA VECTORIAL
        # =====================================================

        try:

            resultados_vectoriales = (
                self.storage.vectores.buscar(
                    consulta=consulta,
                    limite=limite,
                    similitud_minima=0.35,
                )
            )

            for memoria_vectorial in (
                resultados_vectoriales
            ):

                identificador = (
                    memoria_vectorial[
                        "memoria_tipo"
                    ],
                    memoria_vectorial[
                        "memoria_id"
                    ],
                )

                # -------------------------------------------------
                # SI LA MEMORIA YA ESTABA EN LOS RESULTADOS
                # -------------------------------------------------

                if identificador in ids_existentes:

                    self._actualizar_similitud_existente(
                        resultados,
                        identificador,
                        memoria_vectorial[
                            "similitud_semantica"
                        ],
                    )

                    continue

                # -------------------------------------------------
                # MEMORIA ENCONTRADA SOLAMENTE POR SIGNIFICADO
                # -------------------------------------------------

                resultados.append({
                    "id": (
                        memoria_vectorial[
                            "memoria_id"
                        ]
                    ),

                    "contenido": (
                        memoria_vectorial[
                            "contenido"
                        ]
                    ),

                    "dominio": (
                        memoria_vectorial[
                            "dominio"
                        ]
                    ),

                    "categoria": (
                        memoria_vectorial[
                            "categoria"
                        ]
                    ),

                    "importancia": (
                        memoria_vectorial[
                            "importancia"
                        ]
                    ),

                    "confianza": (
                        memoria_vectorial[
                            "confianza"
                        ]
                    ),

                    "relevancia": (
                        memoria_vectorial[
                            "similitud_semantica"
                        ]
                    ),

                    "similitud_semantica": (
                        memoria_vectorial[
                            "similitud_semantica"
                        ]
                    ),

                    "_tipo_memoria": (
                        memoria_vectorial[
                            "memoria_tipo"
                        ]
                    ),

                    "_tipo_recuperacion": (
                        "vectorial"
                    ),
                })

                ids_existentes.add(
                    identificador
                )

        except Exception as error:

            print(
                "[ATENAS][RECUPERADOR][VECTOR] "
                "No se pudo realizar la búsqueda "
                f"semántica: {error}"
            )

        # =====================================================
        # 5. ORDENAR POR IMPORTANCIA / SEMÁNTICA
        # =====================================================

        resultados.sort(
            key=self._score_memoria,
            reverse=True,
        )

        # =====================================================
        # 6. LIMITAR
        # =====================================================

        return resultados[:limite]

    # =========================================================
    # ACTUALIZAR SIMILITUD DE UNA MEMORIA YA ENCONTRADA
    # =========================================================

    @staticmethod
    def _actualizar_similitud_existente(
        resultados: list[dict],
        identificador: tuple,
        similitud: float,
    ) -> None:
        """
        Si una memoria fue encontrada tanto por búsqueda textual
        como vectorial, no la duplicamos.

        En cambio, agregamos la puntuación vectorial al recuerdo
        que ya estaba presente.
        """

        tipo_buscado, id_buscado = identificador

        for memoria in resultados:

            tipo_memoria = memoria.get(
                "_tipo_memoria",
                "semantica",
            )

            memoria_id = memoria.get(
                "id"
            )

            if (
                tipo_memoria == tipo_buscado
                and memoria_id == id_buscado
            ):

                memoria[
                    "similitud_semantica"
                ] = similitud

                memoria[
                    "_tipo_recuperacion"
                ] = "hibrida"

                return

    # =========================================================
    # SCORE DE MEMORIA
    # =========================================================

    @staticmethod
    def _score_memoria(
        memoria: dict,
    ) -> float:
        """
        Calcula la puntuación global de un recuerdo.

        Por ahora utiliza:
        - similitud semántica;
        - relevancia;
        - importancia;
        - confianza;
        - frecuencia de uso.
        """

        importancia = float(
            memoria.get(
                "importancia",
                0.5,
            )
            or 0.5
        )

        confianza = float(
            memoria.get(
                "confianza",
                0.5,
            )
            or 0.5
        )

        relevancia = float(
            memoria.get(
                "relevancia",
                0.5,
            )
            or 0.5
        )

        veces_usado = int(
            memoria.get(
                "veces_usado",
                0,
            )
            or 0
        )

        similitud = float(
            memoria.get(
                "similitud_semantica",
                0.0,
            )
            or 0.0
        )

        frecuencia = min(
            veces_usado / 10,
            1.0,
        )

        score = (
            similitud * 0.40
            + relevancia * 0.25
            + importancia * 0.15
            + confianza * 0.15
            + frecuencia * 0.05
        )

        return float(score)

    # =========================================================
    # CONTEXTO PARA QWEN
    # =========================================================

    def contexto_para_llm(
        self,
        consulta: str,
        limite: int = 6,
    ) -> str:

        consulta = consulta.strip()

        if not consulta:
            return ""

        # =====================================================
        # MEMORIAS
        # =====================================================

        memorias = self.buscar(
            consulta,
            limite=limite,
        )

        lineas_memoria = []

        for memoria in memorias:

            contenido = (
                memoria.get("contenido")
                or memoria.get("descripcion")
            )

            if not contenido:
                continue

            tipo = memoria.get(
                "_tipo_memoria",
                "memoria",
            )

            dominio = memoria.get(
                "dominio"
            )

            recuperacion = memoria.get(
                "_tipo_recuperacion"
            )

            if dominio:

                linea = (
                    f"- [{tipo} / {dominio}] "
                    f"{contenido}"
                )

            else:

                linea = (
                    f"- [{tipo}] "
                    f"{contenido}"
                )

            # Esto es útil para depuración.
            # Qwen sabrá de dónde vino el recuerdo.

            if recuperacion:
                linea += (
                    f" [recuperación: "
                    f"{recuperacion}]"
                )

            lineas_memoria.append(
                linea
            )

        # =====================================================
        # GRAFO DE CONOCIMIENTO
        # =====================================================

        contexto_grafo = ""

        try:

            contexto_grafo = (
                self.storage.grafo
                .contexto_para_llm(
                    consulta
                )
            )

        except Exception as error:

            print(
                "[ATENAS][RECUPERADOR][GRAFO] "
                "No fue posible consultar "
                f"el grafo: {error}"
            )

        # =====================================================
        # CONSTRUIR BLOQUES
        # =====================================================

        bloques = []

        if lineas_memoria:

            bloques.append(
                "MEMORIAS RELEVANTES DE ATENAS:\n"
                + "\n".join(
                    lineas_memoria
                )
            )

        if contexto_grafo:

            bloques.append(
                contexto_grafo
            )


        if not bloques:
            return ""

        return (
            "\n\n".join(bloques)
            + "\n\n"
            "INSTRUCCIONES DE RECUPERACIÓN:\n"
            "- Utiliza esta información solamente cuando "
            "sea relevante para responder.\n"
            "- No inventes recuerdos.\n"
            "- No inventes relaciones que no estén "
            "respaldadas por la memoria o el grafo.\n"
            "- Una memoria recuperada por similitud "
            "vectorial puede estar relacionada por "
            "significado aunque utilice palabras distintas.\n"
            "- Si los recuerdos son contradictorios, "
            "no asumas cuál es correcto; expresa la "
            "incertidumbre."
        )