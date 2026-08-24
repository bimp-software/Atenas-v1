from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .objetivo_visual import ResultadoObjetivoVisual


class TipoAccionGUI(str, Enum):
    MOVER = "mover"
    CLICK = "click"
    DOBLE_CLICK = "doble_click"
    ESCRIBIR = "escribir"
    COMBINACION = "combinacion"
    OBSERVAR = "observar"


@dataclass
class AccionGUIPlanificada:
    tipo: TipoAccionGUI
    ventana: str | None = None
    x_relativo: float | None = None
    y_relativo: float | None = None
    texto: str | None = None
    teclas: list[str] = field(default_factory=list)
    requiere_confirmacion: bool = True
    motivo: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResultadoPlanGUI:
    ok: bool
    accion: AccionGUIPlanificada | None = None
    mensaje: str = ""
    error: str | None = None


class PlanificadorGUI:
    """
    Convierte objetivos visuales resueltos a acciones GUI estructuradas.
    No ejecuta mouse ni teclado.
    """

    def planificar_click(
        self,
        resultado_objetivo: ResultadoObjetivoVisual,
        ventana: str | None,
        doble: bool = False,
    ) -> ResultadoPlanGUI:
        if (
            not resultado_objetivo.ok
            or resultado_objetivo.elemento is None
        ):
            return ResultadoPlanGUI(ok=False, error="sin_elemento_visual")

        elemento = resultado_objetivo.elemento

        if (
            elemento.x_relativo is None
            or elemento.y_relativo is None
        ):
            return ResultadoPlanGUI(
                ok=False,
                error="elemento_sin_coordenadas",
            )

        return ResultadoPlanGUI(
            ok=True,
            accion=AccionGUIPlanificada(
                tipo=(
                    TipoAccionGUI.DOBLE_CLICK
                    if doble
                    else TipoAccionGUI.CLICK
                ),
                ventana=ventana,
                x_relativo=elemento.x_relativo,
                y_relativo=elemento.y_relativo,
                requiere_confirmacion=True,
                motivo=(
                    "El elemento visual fue localizado con confianza suficiente."
                ),
                metadata={
                    "elemento": elemento.descripcion,
                    "confianza": elemento.confianza,
                },
            ),
            mensaje="Acción GUI planificada.",
        )

    def planificar_escritura(
        self,
        ventana: str,
        texto: str,
    ) -> ResultadoPlanGUI:
        return ResultadoPlanGUI(
            ok=True,
            accion=AccionGUIPlanificada(
                tipo=TipoAccionGUI.ESCRIBIR,
                ventana=ventana,
                texto=texto,
                requiere_confirmacion=True,
                motivo=(
                    "La escritura GUI puede producir efectos externos."
                ),
            ),
            mensaje="Escritura GUI planificada.",
        )