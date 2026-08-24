from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .interpretador_visual import (
    InterpretacionVisual,
)


@dataclass
class CriterioVerificacionVisual:
    descripcion: str

    texto_debe_aparecer: str | None = None
    texto_debe_desaparecer: str | None = None

    tipo_elemento_debe_aparecer: str | None = None
    tipo_elemento_debe_desaparecer: str | None = None

    contexto_esperado: str | None = None

    confianza_minima: float = 0.65


@dataclass
class ResultadoVerificacionVisual:
    ok: bool

    cumplido: bool

    mensaje: str = ""

    evidencia: list[str] = field(
        default_factory=list
    )

    error: str | None = None

    datos: dict[str, Any] = field(
        default_factory=dict
    )


class VerificadorVisual:
    """
    Comprueba si una nueva InterpretacionVisual satisface un criterio.

    V1 verifica:
    - aparición/desaparición de texto;
    - aparición/desaparición de tipo de elemento;
    - cambio/estado de contexto de aplicación.

    No asume éxito por el simple hecho de que el click/teclado
    haya retornado ok.
    """

    @staticmethod
    def _corpus(
        interpretacion: InterpretacionVisual,
    ) -> str:

        partes = [
            interpretacion.resumen,
            *interpretacion.observaciones,
        ]

        for elemento in (
            interpretacion.elementos
        ):

            partes.append(
                elemento.descripcion
            )

            if elemento.texto:
                partes.append(
                    elemento.texto
                )

        return "\n".join(
            str(
                parte
            )
            for parte
            in partes
            if parte
        ).lower()

    @staticmethod
    def _tipos(
        interpretacion: InterpretacionVisual,
        confianza_minima: float,
    ) -> set[str]:

        return {
            elemento.tipo.lower()
            for elemento
            in interpretacion.elementos
            if (
                elemento.confianza
                >= confianza_minima
            )
        }

    def verificar(
        self,
        criterio: CriterioVerificacionVisual,
        interpretacion: InterpretacionVisual,
    ) -> ResultadoVerificacionVisual:

        corpus = (
            self._corpus(
                interpretacion
            )
        )

        tipos = (
            self._tipos(
                interpretacion,
                criterio.confianza_minima,
            )
        )

        verificaciones = []
        evidencia = []

        if criterio.texto_debe_aparecer:

            esperado = (
                criterio
                .texto_debe_aparecer
                .lower()
            )

            cumple = (
                esperado in corpus
            )

            verificaciones.append(
                cumple
            )

            evidencia.append(
                (
                    f"Texto '{criterio.texto_debe_aparecer}' "
                    + (
                        "aparece."
                        if cumple
                        else "no aparece."
                    )
                )
            )

        if criterio.texto_debe_desaparecer:

            esperado = (
                criterio
                .texto_debe_desaparecer
                .lower()
            )

            cumple = (
                esperado not in corpus
            )

            verificaciones.append(
                cumple
            )

            evidencia.append(
                (
                    f"Texto '{criterio.texto_debe_desaparecer}' "
                    + (
                        "desapareció."
                        if cumple
                        else "sigue presente."
                    )
                )
            )

        if (
            criterio
            .tipo_elemento_debe_aparecer
        ):

            esperado = (
                criterio
                .tipo_elemento_debe_aparecer
                .lower()
            )

            cumple = (
                esperado in tipos
            )

            verificaciones.append(
                cumple
            )

            evidencia.append(
                (
                    f"Elemento tipo '{esperado}' "
                    + (
                        "aparece."
                        if cumple
                        else "no aparece."
                    )
                )
            )

        if (
            criterio
            .tipo_elemento_debe_desaparecer
        ):

            esperado = (
                criterio
                .tipo_elemento_debe_desaparecer
                .lower()
            )

            cumple = (
                esperado not in tipos
            )

            verificaciones.append(
                cumple
            )

            evidencia.append(
                (
                    f"Elemento tipo '{esperado}' "
                    + (
                        "desapareció."
                        if cumple
                        else "sigue presente."
                    )
                )
            )

        if criterio.contexto_esperado:

            actual = (
                interpretacion
                .contexto_aplicacion
                or ""
            ).lower()

            esperado = (
                criterio
                .contexto_esperado
                .lower()
            )

            cumple = (
                actual == esperado
            )

            verificaciones.append(
                cumple
            )

            evidencia.append(
                (
                    f"Contexto actual='{actual}', "
                    f"esperado='{esperado}'."
                )
            )

        if not verificaciones:

            return ResultadoVerificacionVisual(
                ok=False,
                cumplido=False,
                mensaje=(
                    "El criterio no contiene condiciones verificables."
                ),
                error="criterio_visual_vacio",
            )

        cumplido = all(
            verificaciones
        )

        return ResultadoVerificacionVisual(
            ok=True,
            cumplido=cumplido,
            mensaje=(
                "Criterio visual cumplido."
                if cumplido
                else (
                    "La escena posterior no confirma "
                    "el resultado esperado."
                )
            ),
            evidencia=evidencia,
            datos={
                "confianza_global":
                    interpretacion
                    .confianza_global,

                "contexto":
                    interpretacion
                    .contexto_aplicacion,
            },
        )