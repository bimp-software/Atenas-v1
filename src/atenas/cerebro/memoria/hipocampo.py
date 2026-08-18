from __future__ import annotations

from dataclasses import dataclass

from .filtro_memoria import FiltroMemoria
from .deduplicador import DeduplicadorMemoria


@dataclass
class Experiencia:
    contenido: str

    tipo: str | None = None
    dominio: str | None = None
    subcategoria: str | None = None

    fuente: str = "usuario"

    importancia: float = 0.5
    confianza: float = 0.7
    novedad: float = 0.5

    contexto: str | None = None


class HipocampoDigital:

    def __init__(
        self,
        clasificador,
        consolidador,
        recuperador,
        storage,
    ):
        self.filtro = FiltroMemoria()

        self.clasificador = clasificador
        self.consolidador = consolidador
        self.recuperador = recuperador

        self.storage = storage

        self.deduplicador = (
            DeduplicadorMemoria(
                storage=self.storage
            )
        )

    # =========================================================
    # PROCESAR EXPERIENCIA
    # =========================================================

    def procesar(
        self,
        experiencia: Experiencia,
    ) -> dict:

        # =====================================================
        # 0. NORMALIZAR
        # =====================================================

        contenido = (
            experiencia.contenido
            or ""
        ).strip()

        if not contenido:

            return {
                "guardada": False,
                "duplicada": False,
                "motivo": "contenido_vacio",
            }

        experiencia.contenido = contenido

        # =====================================================
        # 1. FILTRAR
        # =====================================================

        evaluacion = (
            self.filtro.evaluar(
                texto=contenido,
                fuente=experiencia.fuente,
            )
        )

        if not evaluacion.guardar:

            return {
                "guardada": False,
                "duplicada": False,

                "motivo": (
                    evaluacion.motivo
                ),

                "tipo": (
                    evaluacion.tipo
                ),

                "score_filtro": (
                    evaluacion.score
                ),
            }

        # =====================================================
        # 2. BUSCAR DUPLICADO SEMÁNTICO
        # =====================================================

        try:

            duplicacion = (
                self.deduplicador
                .buscar_equivalente(
                    contenido
                )
            )

        except Exception as error:

            print(
                "[ATENAS][HIPOCAMPO][DEDUPLICACION] "
                f"No fue posible evaluar duplicados: {error}"
            )

            duplicacion = None

        # =====================================================
        # 3. SI YA EXISTE, REFORZAR
        # =====================================================

        if (
            duplicacion is not None
            and duplicacion.duplicada
            and duplicacion.memoria_id is not None
        ):

            try:

                memoria_reforzada = (
                    self.storage.semantica
                    .reforzar(
                        memoria_id=(
                            duplicacion.memoria_id
                        ),

                        importancia=(
                            experiencia.importancia
                        ),

                        confianza=(
                            experiencia.confianza
                        ),
                    )
                )

            except Exception as error:

                print(
                    "[ATENAS][HIPOCAMPO][REFUERZO] "
                    f"No fue posible reforzar la memoria: {error}"
                )

                memoria_reforzada = None

            return {
                "guardada": False,
                "duplicada": True,

                "accion": "reforzada",

                "memoria_id": (
                    duplicacion.memoria_id
                ),

                "similitud": (
                    duplicacion.similitud
                ),

                "score_final": (
                    getattr(
                        duplicacion,
                        "score_final",
                        duplicacion.similitud,
                    )
                ),

                "coincidencia_palabras": (
                    getattr(
                        duplicacion,
                        "coincidencia_palabras",
                        0.0,
                    )
                ),

                "memoria": (
                    memoria_reforzada
                ),

                "filtro_tipo": (
                    evaluacion.tipo
                ),

                "filtro_score": (
                    evaluacion.score
                ),

                "filtro_motivo": (
                    evaluacion.motivo
                ),
            }

        # =====================================================
        # 4. CLASIFICAR
        # =====================================================

        clasificacion = (
            self.clasificador
            .clasificar(
                contenido
            )
        )

        experiencia.tipo = (
            getattr(
                clasificacion,
                "tipo",
                None,
            )
        )

        experiencia.dominio = (
            getattr(
                clasificacion,
                "dominio",
                None,
            )
        )

        # Soporta tanto:
        # clasificacion.subcategoria
        #
        # como:
        # clasificacion.categoria

        experiencia.subcategoria = (
            getattr(
                clasificacion,
                "subcategoria",
                None,
            )
            or getattr(
                clasificacion,
                "categoria",
                None,
            )
        )

        # =====================================================
        # 5. AJUSTAR IMPORTANCIA
        # =====================================================

        experiencia.importancia = max(
            float(
                experiencia.importancia
                or 0.5
            ),
            float(
                evaluacion.score
                or 0.0
            ),
        )

        # =====================================================
        # 6. CONSOLIDAR MEMORIA NUEVA
        # =====================================================

        resultado = (
            self.consolidador
            .consolidar(
                experiencia
            )
        )

        # =====================================================
        # 7. ENRIQUECER RESULTADO
        # =====================================================

        if isinstance(
            resultado,
            dict,
        ):

            resultado[
                "duplicada"
            ] = False

            resultado[
                "filtro_tipo"
            ] = evaluacion.tipo

            resultado[
                "filtro_score"
            ] = evaluacion.score

            resultado[
                "filtro_motivo"
            ] = evaluacion.motivo

            # Si encontramos una memoria parecida
            # pero no suficiente para considerarla duplicada,
            # dejamos esa información para depuración.

            if duplicacion is not None:

                resultado[
                    "mejor_similitud_previa"
                ] = duplicacion.similitud

                resultado[
                    "score_deduplicacion"
                ] = getattr(
                    duplicacion,
                    "score_final",
                    duplicacion.similitud,
                )

                resultado[
                    "coincidencia_palabras"
                ] = getattr(
                    duplicacion,
                    "coincidencia_palabras",
                    0.0,
                )

        return resultado

    # =========================================================
    # RECORDAR
    # =========================================================

    def recordar(
        self,
        consulta: str,
    ):

        consulta = (
            consulta
            or ""
        ).strip()

        if not consulta:
            return []

        return (
            self.recuperador
            .buscar(
                consulta
            )
        )