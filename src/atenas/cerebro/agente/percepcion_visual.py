from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .capturador_pantalla import (
    CapturadorPantalla,
)
from .gestor_ventanas import (
    GestorVentanas,
)
from .controlador_mouse import (
    ControladorMouse,
)


@dataclass
class EstadoVisual:
    creada_en: str

    captura_ok: bool
    captura_ruta: str | None = None

    pantalla_ancho: int | None = None
    pantalla_alto: int | None = None

    ventana_activa: dict[str, Any] | None = None
    ventanas_visibles: list[dict[str, Any]] = field(
        default_factory=list
    )

    mouse: dict[str, int] | None = None

    contexto_aplicacion: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ResultadoPercepcionVisual:
    ok: bool

    estado: EstadoVisual | None = None

    mensaje: str = ""
    error: str | None = None


class PercepcionVisual:
    """
    Construye una escena visual estructurada a partir de:
    - captura de pantalla;
    - ventana activa;
    - ventanas visibles;
    - posición del mouse.

    Esta clase todavía NO interpreta píxeles con un modelo visual.
    Su responsabilidad es generar el contexto perceptivo coherente
    que más adelante podrá consumir un modelo de visión.
    """

    def __init__(
        self,
        capturador: CapturadorPantalla | None = None,
        gestor_ventanas: GestorVentanas | None = None,
        controlador_mouse: ControladorMouse | None = None,
    ):
        self.gestor_ventanas = (
            gestor_ventanas
            or GestorVentanas()
        )

        self.controlador_mouse = (
            controlador_mouse
            or ControladorMouse(
                gestor_ventanas=(
                    self.gestor_ventanas
                )
            )
        )

        self.capturador = (
            capturador
            or CapturadorPantalla(
                gestor_ventanas=(
                    self.gestor_ventanas
                )
            )
        )

    @staticmethod
    def _ahora() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _contexto_aplicacion(
        titulo: str | None,
    ) -> str | None:

        if not titulo:
            return None

        t = titulo.lower()

        if (
            "visual studio code" in t
            or "vscode" in t
        ):
            return "editor_codigo"

        if (
            "powershell" in t
            or "command prompt" in t
            or "cmd" in t
        ):
            return "terminal"

        if (
            "chrome" in t
            or "edge" in t
            or "firefox" in t
            or "brave" in t
        ):
            return "navegador"

        if (
            "notepad" in t
            or "bloc de notas" in t
        ):
            return "editor_texto"

        if (
            "explorer" in t
            or "explorador de archivos" in t
        ):
            return "explorador_archivos"

        return "aplicacion_generica"

    def construir_estado(
        self,
        capturar: bool = True,
        todos_monitores: bool = True,
    ) -> ResultadoPercepcionVisual:

        captura_ruta = None
        ancho = None
        alto = None
        captura_ok = False

        if capturar:

            captura = (
                self.capturador
                .capturar_pantalla(
                    todos_monitores=(
                        todos_monitores
                    )
                )
            )

            captura_ok = (
                captura.ok
            )

            if (
                captura.ok
                and captura.captura
                is not None
            ):

                captura_ruta = (
                    captura.captura.ruta
                )

                ancho = (
                    captura.captura.ancho
                )

                alto = (
                    captura.captura.alto
                )

        ventana_activa = None

        resultado_activa = (
            self.gestor_ventanas
            .activa()
        )

        if (
            resultado_activa.ok
            and resultado_activa.ventana
            is not None
        ):

            v = resultado_activa.ventana

            ventana_activa = {
                "hwnd":
                    v.hwnd,

                "titulo":
                    v.titulo,

                "pid":
                    v.proceso_id,

                "x":
                    v.x,

                "y":
                    v.y,

                "ancho":
                    v.ancho,

                "alto":
                    v.alto,
            }

        ventanas_visibles = []

        listado = (
            self.gestor_ventanas
            .listar()
        )

        if listado.ok:

            for v in listado.ventanas:

                ventanas_visibles.append({
                    "hwnd":
                        v.hwnd,

                    "titulo":
                        v.titulo,

                    "pid":
                        v.proceso_id,

                    "x":
                        v.x,

                    "y":
                        v.y,

                    "ancho":
                        v.ancho,

                    "alto":
                        v.alto,

                    "activa":
                        v.activa,
                })

        mouse = None

        resultado_mouse = (
            self.controlador_mouse
            .posicion()
        )

        if (
            resultado_mouse.ok
            and resultado_mouse.posicion
            is not None
        ):

            mouse = {
                "x":
                    resultado_mouse.posicion.x,

                "y":
                    resultado_mouse.posicion.y,
            }

        titulo_activo = (
            ventana_activa.get(
                "titulo"
            )
            if ventana_activa
            else None
        )

        estado = EstadoVisual(
            creada_en=self._ahora(),
            captura_ok=captura_ok,
            captura_ruta=captura_ruta,
            pantalla_ancho=ancho,
            pantalla_alto=alto,
            ventana_activa=ventana_activa,
            ventanas_visibles=(
                ventanas_visibles
            ),
            mouse=mouse,
            contexto_aplicacion=(
                self._contexto_aplicacion(
                    titulo_activo
                )
            ),
            metadata={
                "cantidad_ventanas":
                    len(
                        ventanas_visibles
                    ),

                "todos_monitores":
                    bool(
                        todos_monitores
                    ),
            },
        )

        return ResultadoPercepcionVisual(
            ok=True,
            estado=estado,
            mensaje=(
                "Estado visual construido."
            ),
        )

    @staticmethod
    def resumen_para_agente(
        estado: EstadoVisual,
    ) -> str:

        lineas = [
            "ESCENA VISUAL ACTUAL:",
            "",
        ]

        if estado.ventana_activa:

            lineas.extend([
                "Ventana activa:",
                str(
                    estado.ventana_activa.get(
                        "titulo"
                    )
                    or "Sin título"
                ),
                "",
            ])

        if (
            estado.pantalla_ancho
            is not None
            and estado.pantalla_alto
            is not None
        ):

            lineas.extend([
                (
                    "Resolución capturada: "
                    f"{estado.pantalla_ancho} x "
                    f"{estado.pantalla_alto}"
                ),
                "",
            ])

        if estado.mouse:

            lineas.extend([
                (
                    "Mouse: "
                    f"x={estado.mouse['x']}, "
                    f"y={estado.mouse['y']}"
                ),
                "",
            ])

        lineas.append(
            "Ventanas visibles:"
        )

        for ventana in (
            estado.ventanas_visibles[:20]
        ):

            lineas.append(
                "- "
                + (
                    ventana.get(
                        "titulo"
                    )
                    or "Sin título"
                )
            )

        lineas.extend([
            "",
            (
                "Contexto de aplicación: "
                f"{estado.contexto_aplicacion}"
            ),
            (
                "Captura: "
                f"{estado.captura_ruta}"
            ),
        ])

        return "\n".join(
            lineas
        )