from __future__ import annotations

from src.atenas.cerebro.memoria.hipocampo import (
    HipocampoDigital,
    Experiencia,
)

from src.atenas.memoria.store_manager import (
    StorageManager,
)

from .vigencia import EvaluadorVigencia

class ConsolidadorInvestigacion:
    """
    Convierte una investigación web útil en conocimiento
    persistente de ATENAS.

    Guarda:
    - la síntesis como memoria;
    - sus fuentes y consulta original;
    - confianza;
    - historial de investigación.
    """

    def __init__(
        self,
        storage: StorageManager,
        hipocampo: HipocampoDigital,
    ):
        self.storage = storage
        self.hipocampo = hipocampo

        self.evaluador_vigencia = (
            EvaluadorVigencia()
        )

    # =========================================================
    # CONSOLIDAR
    # =========================================================

    def consolidar(
        self,
        consulta: str,
        sintesis: str,
        fuentes: list[dict],
        confianza: float = 0.80,
    ) -> dict:

        consulta = consulta.strip()
        sintesis = sintesis.strip()

        if not sintesis:

            return {
                "guardada": False,
                "motivo": "sintesis_vacia",
            }

        # =====================================================
        # FUENTES
        # =====================================================

        urls = [
            fuente.get("url", "")
            for fuente in fuentes
            if fuente.get("url")
        ]

        contexto = (
            "Investigación web realizada por ATENAS.\n"
            f"Consulta original: {consulta}\n"
            f"Fuentes consultadas: {len(urls)}"
        )

        # =====================================================
        # HIPOCAMPO
        # =====================================================

        experiencia = Experiencia(
            contenido=sintesis,
            fuente="internet",
            importancia=0.70,
            confianza=confianza,
            contexto=contexto,
        )

        resultado_memoria = (
            self.hipocampo.procesar(
                experiencia
            )
        )

        # Intentamos obtener el ID si el Hipocampo lo devuelve.
        memoria_id = None

        if isinstance(
            resultado_memoria,
            dict,
        ):

            memoria_id = (
                resultado_memoria.get(
                    "memoria_id"
                )
                or resultado_memoria.get(
                    "id"
                )
            )

        vigencia = (
            self.evaluador_vigencia.evaluar(
                consulta=consulta,
                sintesis=sintesis,
            )
        )

        # =====================================================
        # REGISTRAR INVESTIGACIÓN
        # =====================================================

        investigacion_id = (
            self.storage.investigaciones.guardar(
                consulta=consulta,
                sintesis=sintesis,
                fuentes=fuentes,
                confianza=confianza,
                memoria_id=memoria_id,

                tipo_vigencia=vigencia.tipo,

                revisar_despues_dias=(
                    vigencia.revisar_despues_dias
                ),
            )
        )

        return {
            "guardada": True,
            "investigacion_id": investigacion_id,
            "memoria_id": memoria_id,
            "resultado_memoria":
                resultado_memoria,
            "fuentes": len(fuentes),
            "vigencia": vigencia.tipo,
            "revisar_despues_dias":
                vigencia.revisar_despues_dias,
            "razon_vigencia":
                vigencia.razon,
        }