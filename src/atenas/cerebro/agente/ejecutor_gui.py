from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .accion_gui import (
    AccionGUIPlanificada,
    TipoAccionGUI,
)

from .controlador_mouse import (
    BotonMouse,
    ControladorMouse,
)

from .controlador_teclado import (
    ControladorTeclado,
)

from .gestor_presupuesto_autonomia import (
    GestorPresupuestoAutonomia,
)


@dataclass
class ResultadoEjecucionGUI:
    ok: bool

    accion: AccionGUIPlanificada | None = None

    ejecutada: bool = False
    requiere_confirmacion: bool = False

    mensaje: str = ""
    error: str | None = None

    datos: dict[str, Any] = field(
        default_factory=dict
    )


class EjecutorGUI:
    """
    Ejecuta AccionGUIPlanificada usando mouse/teclado estructurados.

    Responsabilidades:
    - consultar política de autonomía;
    - impedir ejecuciones no autorizadas;
    - ejecutar movimientos/clicks/escritura;
    - devolver resultado estructurado.

    NO decide qué elemento visual usar.
    NO interpreta imágenes.
    """

    def __init__(
        self,
        mouse: ControladorMouse,
        teclado: ControladorTeclado,
        autonomia: GestorPresupuestoAutonomia | None = None,
    ):
        self.mouse = mouse
        self.teclado = teclado

        self.autonomia = (
            autonomia
            or GestorPresupuestoAutonomia()
        )

    # =========================================================
    # POLÍTICA
    # =========================================================

    @staticmethod
    def _accion_politica(
        accion: AccionGUIPlanificada,
    ) -> str:

        if accion.tipo == TipoAccionGUI.MOVER:
            return "mover_mouse_ventana"

        if accion.tipo == TipoAccionGUI.CLICK:
            return "click_mouse_ventana"

        if accion.tipo == TipoAccionGUI.DOBLE_CLICK:
            return "doble_click_mouse"

        if accion.tipo == TipoAccionGUI.ESCRIBIR:
            return "escribir_en_ventana"

        if accion.tipo == TipoAccionGUI.COMBINACION:
            return "combinacion_teclas_ventana"

        return "construir_estado_visual"

    # =========================================================
    # EJECUCIÓN
    # =========================================================

    def ejecutar(
        self,
        accion: AccionGUIPlanificada,
        es_autonoma: bool,
        confirmada: bool = False,
    ) -> ResultadoEjecucionGUI:

        nombre_politica = (
            self._accion_politica(
                accion
            )
        )

        evaluacion = (
            self.autonomia
            .evaluar(
                accion=nombre_politica,
                es_autonoma=es_autonoma,
                confirmada=confirmada,
            )
        )

        if not evaluacion.permitida:

            return ResultadoEjecucionGUI(
                ok=False,
                accion=accion,
                ejecutada=False,
                requiere_confirmacion=(
                    evaluacion
                    .requiere_confirmacion
                ),
                mensaje=evaluacion.motivo,
                error=(
                    "accion_bloqueada"
                    if evaluacion.bloqueada
                    else (
                        "requiere_confirmacion"
                        if evaluacion
                        .requiere_confirmacion
                        else "no_permitida"
                    )
                ),
                datos={
                    "politica":
                        nombre_politica,

                    "nivel":
                        evaluacion.nivel.value,

                    "costo":
                        evaluacion.costo,

                    "presupuesto_restante":
                        evaluacion
                        .presupuesto_restante,
                },
            )

        resultado = None

        # -----------------------------------------------------
        # MOVER
        # -----------------------------------------------------

        if accion.tipo == TipoAccionGUI.MOVER:

            if (
                not accion.ventana
                or accion.x_relativo is None
                or accion.y_relativo is None
            ):

                return ResultadoEjecucionGUI(
                    ok=False,
                    accion=accion,
                    error="accion_gui_incompleta",
                    mensaje=(
                        "Mover requiere ventana y coordenadas relativas."
                    ),
                )

            resultado = (
                self.mouse
                .mover_relativo_ventana(
                    titulo=accion.ventana,
                    x_relativo=accion.x_relativo,
                    y_relativo=accion.y_relativo,
                    duracion=0.15,
                    activar_ventana=True,
                )
            )

        # -----------------------------------------------------
        # CLICK
        # -----------------------------------------------------

        elif accion.tipo in {
            TipoAccionGUI.CLICK,
            TipoAccionGUI.DOBLE_CLICK,
        }:

            if (
                not accion.ventana
                or accion.x_relativo is None
                or accion.y_relativo is None
            ):

                return ResultadoEjecucionGUI(
                    ok=False,
                    accion=accion,
                    error="accion_gui_incompleta",
                    mensaje=(
                        "Click requiere ventana y coordenadas relativas."
                    ),
                )

            resultado = (
                self.mouse
                .click_relativo_ventana(
                    titulo=accion.ventana,
                    x_relativo=accion.x_relativo,
                    y_relativo=accion.y_relativo,
                    boton=BotonMouse.IZQUIERDO,
                    doble=(
                        accion.tipo
                        == TipoAccionGUI.DOBLE_CLICK
                    ),
                    duracion_movimiento=0.15,
                )
            )

        # -----------------------------------------------------
        # ESCRIBIR
        # -----------------------------------------------------

        elif accion.tipo == TipoAccionGUI.ESCRIBIR:

            if not accion.ventana:

                return ResultadoEjecucionGUI(
                    ok=False,
                    accion=accion,
                    error="ventana_requerida",
                )

            resultado = (
                self.teclado
                .escribir_en_ventana(
                    titulo=accion.ventana,
                    texto=(
                        accion.texto
                        or ""
                    ),
                    intervalo=0.0,
                )
            )

        # -----------------------------------------------------
        # COMBINACIÓN
        # -----------------------------------------------------

        elif accion.tipo == TipoAccionGUI.COMBINACION:

            if not accion.ventana:

                return ResultadoEjecucionGUI(
                    ok=False,
                    accion=accion,
                    error="ventana_requerida",
                )

            resultado = (
                self.teclado
                .combinacion_en_ventana(
                    titulo=accion.ventana,
                    teclas=(
                        accion.teclas
                        or []
                    ),
                )
            )

        # -----------------------------------------------------
        # OBSERVAR
        # -----------------------------------------------------

        elif accion.tipo == TipoAccionGUI.OBSERVAR:

            return ResultadoEjecucionGUI(
                ok=True,
                accion=accion,
                ejecutada=False,
                requiere_confirmacion=False,
                mensaje=(
                    "La acción OBSERVAR no requiere "
                    "ejecución física."
                ),
            )

        else:

            return ResultadoEjecucionGUI(
                ok=False,
                accion=accion,
                error="tipo_accion_gui_no_soportado",
            )

        if resultado is None:

            return ResultadoEjecucionGUI(
                ok=False,
                accion=accion,
                error="resultado_gui_ausente",
            )

        if (
            resultado.ok
            and es_autonoma
        ):

            self.autonomia.consumir(
                evaluacion,
                es_autonoma=True,
            )

        datos = (
            dict(
                resultado.datos
                or {}
            )
        )

        if getattr(
            resultado,
            "posicion",
            None,
        ) is not None:

            datos["posicion"] = {
                "x":
                    resultado.posicion.x,

                "y":
                    resultado.posicion.y,
            }

        datos[
            "politica"
        ] = nombre_politica

        datos[
            "presupuesto_restante"
        ] = (
            self.autonomia
            .presupuesto_restante
        )

        return ResultadoEjecucionGUI(
            ok=bool(
                resultado.ok
            ),
            accion=accion,
            ejecutada=bool(
                resultado.ok
            ),
            requiere_confirmacion=False,
            mensaje=(
                resultado.mensaje
                or "Acción GUI ejecutada."
            ),
            error=(
                resultado.error
            ),
            datos=datos,
        )