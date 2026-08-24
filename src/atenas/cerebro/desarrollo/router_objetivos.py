from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .proyectos_internos import (
    ObjetivoProyecto,
)


class TipoTrabajoObjetivo(str, Enum):
    ANALISIS = "analisis"
    PROGRAMACION = "programacion"


@dataclass
class ClasificacionObjetivo:
    tipo: TipoTrabajoObjetivo
    confianza: float
    motivo: str


class RouterObjetivosProyecto:
    """
    Decide si un objetivo conviene resolverlo como trabajo
    intelectual o como solución de código pequeña.
    """

    PALABRAS_PROGRAMACION = {
        "crear módulo",
        "crear modulo",
        "implementar",
        "programar",
        "código",
        "codigo",
        "script",
        "controlador",
        "api",
        "endpoint",
        "interfaz técnica",
        "interfaz tecnica",
        "clase",
        "función",
        "funcion",
        "archivo",
        "prototipo",
        "firmware",
        "html",
        "javascript",
        "python",
        "arduino",
        "esp32",
    }

    PALABRAS_ANALISIS = {
        "analizar",
        "investigar",
        "diseñar arquitectura",
        "disenar arquitectura",
        "planificar",
        "documentar",
        "definir requisitos",
        "evaluar",
        "comparar",
        "estrategia",
    }

    def clasificar(
        self,
        objetivo: ObjetivoProyecto,
    ) -> ClasificacionObjetivo:

        texto = (
            objetivo.descripcion
            .strip()
            .lower()
        )

        score_codigo = sum(
            1
            for palabra
            in self.PALABRAS_PROGRAMACION
            if palabra in texto
        )

        score_analisis = sum(
            1
            for palabra
            in self.PALABRAS_ANALISIS
            if palabra in texto
        )

        if score_codigo > score_analisis:

            return ClasificacionObjetivo(
                tipo=(
                    TipoTrabajoObjetivo
                    .PROGRAMACION
                ),
                confianza=min(
                    0.95,
                    0.70
                    + score_codigo
                    * 0.08,
                ),
                motivo=(
                    "El objetivo contiene señales "
                    "claras de implementación."
                ),
            )

        return ClasificacionObjetivo(
            tipo=(
                TipoTrabajoObjetivo
                .ANALISIS
            ),
            confianza=min(
                0.95,
                0.72
                + score_analisis
                * 0.06,
            ),
            motivo=(
                "El objetivo puede resolverse "
                "primero como análisis o diseño."
            ),
        )