from __future__ import annotations

from src.atenas.memoria.store_manager import (
    StorageManager,
)

from src.atenas.herramientas.internet.buscar_web import (
    buscar_web,
)

from .detector_desconocimiento import (
    DetectorDesconocimiento,
)

from .clasificador_consulta import (
    ClasificadorConsulta,
)


class Investigador:

    def __init__(self,storage: StorageManager,):
        self.storage = storage
        self.detector = (DetectorDesconocimiento())
        self.clasificador_consulta = (ClasificadorConsulta())

    def evaluar_consulta(
        self,
        consulta: str,
    ) -> dict:

        clasificacion_consulta = (
            self.clasificador_consulta.clasificar(
                consulta
            )
        )

        if not clasificacion_consulta.permite_internet:

            return {
                "necesita_investigar": False,
                "incertidumbre": 0.0,
                "mejor_similitud": 0.0,
                "cobertura_conceptual": 1.0,
                "terminos_encontrados": [],
                "terminos_desconocidos": [],
                "motivos": [
                    clasificacion_consulta.motivo
                ],
                "tipo_consulta":
                    clasificacion_consulta.tipo,
                "internet_permitido": False,
            }

        consulta = consulta.strip()

        if not consulta:

            return {
                "necesita_investigar": False,
                "incertidumbre": 0.0,
                "memorias": [],
                "relaciones": [],
            }

        # =====================================================
        # MEMORIA VECTORIAL
        # =====================================================

        try:

            memorias = (
                self.storage.vectores.buscar(
                    consulta=consulta,
                    limite=5,
                    similitud_minima=0.25,
                )
            )

        except Exception:

            memorias = []

        # =====================================================
        # GRAFO
        # =====================================================

        try:

            relaciones = (
                self.storage.grafo
                .buscar_relacionado(
                    consulta,
                    limite=10,
                )
            )

        except Exception:

            relaciones = []

        resultado = self.detector.evaluar(
            consulta=consulta,
            memorias=memorias,
            relaciones=relaciones,
        )

        resultado["memorias"] = memorias
        resultado["relaciones"] = relaciones

        resultado["tipo_consulta"] = (
            clasificacion_consulta.tipo
        )

        resultado["internet_permitido"] = (
            clasificacion_consulta.permite_internet
        )

        return resultado

    # =========================================================
    # INVESTIGAR
    # =========================================================

    def investigar(
        self,
        consulta: str,
        limite: int = 5,
        forzar: bool = False,
    ) -> dict:

        consulta = consulta.strip()

        if not consulta:

            return {
                "ok": False,
                "investigo": False,
                "error": "consulta_vacia",
                "resultados": [],
            }

        # =====================================================
        # CLASIFICAR CONSULTA
        # =====================================================

        clasificacion = (
            self.clasificador_consulta
            .clasificar(
                consulta
            )
        )

        # =====================================================
        # INTERNET NO CORRESPONDE
        # =====================================================

        if (
            not forzar
            and not clasificacion.permite_internet
        ):

            return {
                "ok": True,
                "investigo": False,
                "motivo": clasificacion.motivo,
                "tipo_consulta": clasificacion.tipo,
                "resultados": [],
            }

        # =====================================================
        # EVALUAR CONOCIMIENTO LOCAL
        # =====================================================

        evaluacion = (
            self.evaluar_consulta(
                consulta
            )
        )

        # =====================================================
        # ATENAS YA SABE SUFICIENTE
        # =====================================================

        if (
            not forzar
            and not evaluacion.get(
                "necesita_investigar",
                False,
            )
        ):

            return {
                "ok": True,
                "investigo": False,
                "motivo": (
                    "ATENAS parece tener "
                    "información local suficiente."
                ),
                "evaluacion": evaluacion,
                "resultados": [],
            }

        # =====================================================
        # INVESTIGACIÓN WEB
        # =====================================================

        resultado_web = buscar_web(
            consulta=consulta,
            limite=limite,
        )

        return {
            "ok": resultado_web.get(
                "ok",
                False,
            ),

            "investigo": True,

            "forzada": forzar,

            "tipo_consulta": (
                clasificacion.tipo
            ),

            "evaluacion": evaluacion,

            "resultados": resultado_web.get(
                "resultados",
                [],
            ),

            "error": resultado_web.get(
                "error"
            ),

            "mensaje": resultado_web.get(
                "mensaje"
            ),
        }