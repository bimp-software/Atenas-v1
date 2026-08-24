from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .accion_gui import (
    AccionGUIPlanificada,
)

from .ejecutor_gui import (
    EjecutorGUI,
    ResultadoEjecucionGUI,
)

from .interpretador_visual import (
    InterpretadorVisual,
    InterpretacionVisual,
)

from .percepcion_visual import (
    PercepcionVisual,
)

from .verificador_visual import (
    CriterioVerificacionVisual,
    ResultadoVerificacionVisual,
    VerificadorVisual,
)


@dataclass
class ResultadoCicloGUI:
    ok: bool

    ejecutada: bool = False
    verificada: bool = False

    requiere_confirmacion: bool = False

    accion: AccionGUIPlanificada | None = None

    interpretacion_posterior: (
        InterpretacionVisual
        | None
    ) = None

    verificacion: (
        ResultadoVerificacionVisual
        | None
    ) = None

    mensaje: str = ""
    error: str | None = None

    datos: dict[str, Any] = field(
        default_factory=dict
    )


class CicloAccionGUI:
    """
    Cierra el bucle:

        ACTUAR
        -> CAPTURAR
        -> INTERPRETAR
        -> VERIFICAR

    La acción no se considera exitosa a nivel de objetivo hasta
    que la verificación visual posterior lo confirma.
    """

    def __init__(
        self,
        ejecutor_gui: EjecutorGUI,
        percepcion_visual: PercepcionVisual,
        interpretador_visual: InterpretadorVisual,
        verificador_visual: VerificadorVisual | None = None,
    ):
        self.ejecutor_gui = (
            ejecutor_gui
        )

        self.percepcion_visual = (
            percepcion_visual
        )

        self.interpretador_visual = (
            interpretador_visual
        )

        self.verificador_visual = (
            verificador_visual
            or VerificadorVisual()
        )

    def ejecutar_y_verificar(
        self,
        accion: AccionGUIPlanificada,
        criterio: CriterioVerificacionVisual,
        es_autonoma: bool,
        confirmada: bool = False,
        usar_modelo_vision: bool = True,
    ) -> ResultadoCicloGUI:

        ejecucion: ResultadoEjecucionGUI = (
            self.ejecutor_gui
            .ejecutar(
                accion=accion,
                es_autonoma=es_autonoma,
                confirmada=confirmada,
            )
        )

        if ejecucion.requiere_confirmacion:

            return ResultadoCicloGUI(
                ok=False,
                ejecutada=False,
                verificada=False,
                requiere_confirmacion=True,
                accion=accion,
                mensaje=ejecucion.mensaje,
                error=ejecucion.error,
                datos=ejecucion.datos,
            )

        if not ejecucion.ok:

            return ResultadoCicloGUI(
                ok=False,
                ejecutada=(
                    ejecucion.ejecutada
                ),
                verificada=False,
                accion=accion,
                mensaje=(
                    ejecucion.mensaje
                ),
                error=(
                    ejecucion.error
                ),
                datos=(
                    ejecucion.datos
                ),
            )

        estado = (
            self.percepcion_visual
            .construir_estado(
                capturar=True
            )
        )

        if (
            not estado.ok
            or estado.estado is None
        ):

            return ResultadoCicloGUI(
                ok=False,
                ejecutada=True,
                verificada=False,
                accion=accion,
                mensaje=(
                    "La acción se ejecutó, pero no se pudo "
                    "capturar el estado posterior."
                ),
                error=(
                    estado.error
                    or "percepcion_posterior_fallida"
                ),
            )

        interpretacion = (
            self.interpretador_visual
            .interpretar(
                estado=estado.estado,
                usar_modelo_vision=(
                    usar_modelo_vision
                ),
            )
        )

        if (
            not interpretacion.ok
            or interpretacion.interpretacion
            is None
        ):

            return ResultadoCicloGUI(
                ok=False,
                ejecutada=True,
                verificada=False,
                accion=accion,
                mensaje=(
                    "La acción se ejecutó, pero no se pudo "
                    "interpretar el estado posterior."
                ),
                error=(
                    interpretacion.error
                    or "interpretacion_posterior_fallida"
                ),
            )

        verificacion = (
            self.verificador_visual
            .verificar(
                criterio=criterio,
                interpretacion=(
                    interpretacion
                    .interpretacion
                ),
            )
        )

        return ResultadoCicloGUI(
            ok=(
                verificacion.ok
                and verificacion.cumplido
            ),
            ejecutada=True,
            verificada=(
                verificacion.cumplido
            ),
            accion=accion,
            interpretacion_posterior=(
                interpretacion
                .interpretacion
            ),
            verificacion=verificacion,
            mensaje=verificacion.mensaje,
            error=(
                None
                if (
                    verificacion.ok
                    and verificacion.cumplido
                )
                else (
                    verificacion.error
                    or "resultado_no_confirmado"
                )
            ),
            datos={
                "ejecucion":
                    ejecucion.datos,

                "evidencia":
                    verificacion.evidencia,
            },
        )