from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VigenciaConocimiento:
    tipo: str
    revisar_despues_dias: int
    razon: str


class EvaluadorVigencia:

    TERMINOS_MUY_VOLATILES = (
        "hoy",
        "ahora",
        "actual",
        "actualmente",
        "precio",
        "cotización",
        "clima",
        "tiempo",
        "noticia",
        "última noticia",
        "ultima noticia",
        "resultado",
        "marcador",
        "stock",
        "disponible",
    )

    TERMINOS_VOLATILES = (
        "última versión",
        "ultima version",
        "versión actual",
        "version actual",
        "nuevo modelo",
        "nueva versión",
        "nueva version",
        "requisitos actuales",
        "documentación actual",
        "documentacion actual",
    )

    TERMINOS_ESTABLES = (
        "qué es",
        "que es",
        "cómo funciona",
        "como funciona",
        "definición",
        "definicion",
        "concepto",
        "principio",
        "historia",
    )

    def evaluar(
        self,
        consulta: str,
        sintesis: str = "",
    ) -> VigenciaConocimiento:

        texto = (
            consulta
            + " "
            + sintesis
        ).lower()

        if any(
            termino in texto
            for termino
            in self.TERMINOS_MUY_VOLATILES
        ):
            return VigenciaConocimiento(
                tipo="muy_alta",
                revisar_despues_dias=1,
                razon=(
                    "La información puede cambiar "
                    "en horas o días."
                ),
            )

        if any(
            termino in texto
            for termino
            in self.TERMINOS_VOLATILES
        ):
            return VigenciaConocimiento(
                tipo="alta",
                revisar_despues_dias=7,
                razon=(
                    "La información depende de "
                    "versiones o estado actual."
                ),
            )

        if any(
            termino in texto
            for termino
            in self.TERMINOS_ESTABLES
        ):
            return VigenciaConocimiento(
                tipo="baja",
                revisar_despues_dias=180,
                razon=(
                    "Parece conocimiento conceptual "
                    "relativamente estable."
                ),
            )

        return VigenciaConocimiento(
            tipo="media",
            revisar_despues_dias=30,
            razon=(
                "No se detectó una estabilidad "
                "especial."
            ),
        )