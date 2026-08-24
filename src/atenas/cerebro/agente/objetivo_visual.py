from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .interpretador_visual import ElementoVisual, InterpretacionVisual


class TipoObjetivoVisual(str, Enum):
    LOCALIZAR = "localizar"
    ACTIVAR = "activar"
    ESCRIBIR = "escribir"
    OBSERVAR = "observar"


@dataclass
class ObjetivoVisual:
    tipo: TipoObjetivoVisual
    descripcion: str
    selector_tipo: str | None = None
    selector_texto: str | None = None
    confianza_minima: float = 0.70
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResultadoObjetivoVisual:
    ok: bool
    objetivo: ObjetivoVisual
    elemento: ElementoVisual | None = None
    candidatos: list[ElementoVisual] = field(default_factory=list)
    mensaje: str = ""
    error: str | None = None


class ResolutorObjetivoVisual:
    """
    Localiza el elemento que mejor satisface un objetivo semántico.
    No ejecuta ninguna interacción.
    """

    @staticmethod
    def _score(
        elemento: ElementoVisual,
        objetivo: ObjetivoVisual,
    ) -> float:
        score = elemento.confianza * 0.55

        if (
            objetivo.selector_tipo
            and elemento.tipo.lower()
            == objetivo.selector_tipo.lower()
        ):
            score += 0.25

        if objetivo.selector_texto:
            buscado = objetivo.selector_texto.lower().strip()
            corpus = (
                f"{elemento.descripcion} {elemento.texto or ''}"
            ).lower()
            if buscado in corpus:
                score += 0.20

        return min(1.0, score)

    def resolver(
        self,
        objetivo: ObjetivoVisual,
        interpretacion: InterpretacionVisual,
    ) -> ResultadoObjetivoVisual:
        candidatos: list[ElementoVisual] = []

        for elemento in interpretacion.elementos:
            score = self._score(elemento, objetivo)
            if score < objetivo.confianza_minima:
                continue

            candidatos.append(
                ElementoVisual(
                    tipo=elemento.tipo,
                    descripcion=elemento.descripcion,
                    confianza=score,
                    x_relativo=elemento.x_relativo,
                    y_relativo=elemento.y_relativo,
                    ancho_relativo=elemento.ancho_relativo,
                    alto_relativo=elemento.alto_relativo,
                    texto=elemento.texto,
                    accion_sugerida=elemento.accion_sugerida,
                    metadata=dict(elemento.metadata),
                )
            )

        candidatos.sort(key=lambda x: x.confianza, reverse=True)

        if not candidatos:
            return ResultadoObjetivoVisual(
                ok=False,
                objetivo=objetivo,
                error="objetivo_visual_no_resuelto",
                mensaje=(
                    "No se encontró un elemento visual con confianza suficiente."
                ),
            )

        return ResultadoObjetivoVisual(
            ok=True,
            objetivo=objetivo,
            elemento=candidatos[0],
            candidatos=candidatos,
            mensaje="Objetivo visual resuelto.",
        )