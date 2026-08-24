from __future__ import annotations

import ctypes
import platform
import time

from ctypes import wintypes
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .gestor_ventanas import (
    GestorVentanas,
)


class BotonMouse(str, Enum):
    IZQUIERDO = "izquierdo"
    DERECHO = "derecho"
    MEDIO = "medio"


@dataclass
class PosicionMouse:
    x: int
    y: int


@dataclass
class ResultadoMouse:
    ok: bool
    accion: str

    posicion: PosicionMouse | None = None

    mensaje: str = ""
    error: str | None = None

    datos: dict[str, Any] | None = None


class ControladorMouse:
    """
    Control estructurado del mouse.

    Windows:
    - obtiene posición actual;
    - mueve el cursor;
    - mueve relativo a una ventana;
    - click izquierdo/derecho/medio;
    - doble click;
    - scroll vertical.

    No recibe comandos libres ni interpreta texto natural.
    """

    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_WHEEL = 0x0800

    WHEEL_DELTA = 120

    def __init__(
        self,
        gestor_ventanas: GestorVentanas | None = None,
    ):
        self.sistema = (
            platform.system()
            .strip()
            .lower()
        )

        self.disponible = (
            self.sistema == "windows"
        )

        self.gestor_ventanas = (
            gestor_ventanas
            or GestorVentanas()
        )

        self._user32 = None

        if self.disponible:
            self._inicializar_windows()

    # =========================================================
    # WINDOWS
    # =========================================================

    def _inicializar_windows(
        self,
    ) -> None:

        self._user32 = (
            ctypes.windll.user32
        )

        self._user32.GetCursorPos.argtypes = [
            ctypes.POINTER(
                wintypes.POINT
            )
        ]

        self._user32.GetCursorPos.restype = (
            wintypes.BOOL
        )

        self._user32.SetCursorPos.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
        ]

        self._user32.SetCursorPos.restype = (
            wintypes.BOOL
        )

        self._user32.mouse_event.argtypes = [
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.c_void_p,
        ]

    # =========================================================
    # UTILIDADES
    # =========================================================

    def _no_disponible(
        self,
        accion: str,
    ) -> ResultadoMouse:

        return ResultadoMouse(
            ok=False,
            accion=accion,
            error="control_mouse_no_disponible",
            mensaje=(
                "La primera versión del controlador "
                "de mouse está implementada para Windows."
            ),
        )

    @staticmethod
    def _validar_coordenada(
        valor: int,
    ) -> int:

        return int(
            max(
                -32768,
                min(
                    32767,
                    int(valor),
                ),
            )
        )

    # =========================================================
    # POSICIÓN
    # =========================================================

    def posicion(
        self,
    ) -> ResultadoMouse:

        if not self.disponible:
            return self._no_disponible(
                "posicion_mouse"
            )

        punto = wintypes.POINT()

        ok = bool(
            self._user32.GetCursorPos(
                ctypes.byref(
                    punto
                )
            )
        )

        if not ok:

            return ResultadoMouse(
                ok=False,
                accion="posicion_mouse",
                error="no_se_pudo_obtener_posicion",
            )

        return ResultadoMouse(
            ok=True,
            accion="posicion_mouse",
            posicion=PosicionMouse(
                x=int(
                    punto.x
                ),
                y=int(
                    punto.y
                ),
            ),
            mensaje="Posición obtenida.",
        )

    # =========================================================
    # MOVER
    # =========================================================

    def mover(
        self,
        x: int,
        y: int,
        duracion: float = 0.0,
    ) -> ResultadoMouse:

        if not self.disponible:
            return self._no_disponible(
                "mover_mouse"
            )

        destino_x = (
            self._validar_coordenada(
                x
            )
        )

        destino_y = (
            self._validar_coordenada(
                y
            )
        )

        duracion = max(
            0.0,
            min(
                5.0,
                float(
                    duracion
                ),
            ),
        )

        if duracion <= 0:

            ok = bool(
                self._user32.SetCursorPos(
                    destino_x,
                    destino_y,
                )
            )

        else:

            actual = self.posicion()

            if (
                not actual.ok
                or actual.posicion
                is None
            ):

                return ResultadoMouse(
                    ok=False,
                    accion="mover_mouse",
                    error=(
                        actual.error
                        or "posicion_actual_no_disponible"
                    ),
                )

            pasos = max(
                2,
                min(
                    120,
                    int(
                        duracion
                        * 60
                    ),
                ),
            )

            inicio_x = (
                actual.posicion.x
            )

            inicio_y = (
                actual.posicion.y
            )

            intervalo = (
                duracion
                / pasos
            )

            ok = True

            for paso in range(
                1,
                pasos + 1,
            ):

                progreso = (
                    paso
                    / pasos
                )

                actual_x = int(
                    inicio_x
                    + (
                        destino_x
                        - inicio_x
                    )
                    * progreso
                )

                actual_y = int(
                    inicio_y
                    + (
                        destino_y
                        - inicio_y
                    )
                    * progreso
                )

                if not self._user32.SetCursorPos(
                    actual_x,
                    actual_y,
                ):
                    ok = False
                    break

                time.sleep(
                    intervalo
                )

        return ResultadoMouse(
            ok=ok,
            accion="mover_mouse",
            posicion=PosicionMouse(
                x=destino_x,
                y=destino_y,
            ),
            mensaje=(
                "Cursor movido."
                if ok
                else "No se pudo mover el cursor."
            ),
        )

    # =========================================================
    # RELATIVO A VENTANA
    # =========================================================

    def mover_relativo_ventana(
        self,
        titulo: str,
        x_relativo: float,
        y_relativo: float,
        duracion: float = 0.0,
        activar_ventana: bool = True,
    ) -> ResultadoMouse:

        if not self.disponible:
            return self._no_disponible(
                "mover_mouse_ventana"
            )

        x_relativo = max(
            0.0,
            min(
                1.0,
                float(
                    x_relativo
                ),
            ),
        )

        y_relativo = max(
            0.0,
            min(
                1.0,
                float(
                    y_relativo
                ),
            ),
        )

        resultado = (
            self.gestor_ventanas
            .buscar(
                titulo
            )
        )

        if (
            not resultado.ok
            or resultado.ventana
            is None
        ):

            return ResultadoMouse(
                ok=False,
                accion="mover_mouse_ventana",
                error=(
                    resultado.error
                    or "ventana_no_encontrada"
                ),
            )

        ventana = (
            resultado.ventana
        )

        if (
            ventana.x is None
            or ventana.y is None
            or ventana.ancho is None
            or ventana.alto is None
        ):

            return ResultadoMouse(
                ok=False,
                accion="mover_mouse_ventana",
                error="geometria_ventana_no_disponible",
            )

        if activar_ventana:

            self.gestor_ventanas.activar(
                hwnd=ventana.hwnd
            )

        destino_x = int(
            ventana.x
            + ventana.ancho
            * x_relativo
        )

        destino_y = int(
            ventana.y
            + ventana.alto
            * y_relativo
        )

        resultado_mouse = self.mover(
            x=destino_x,
            y=destino_y,
            duracion=duracion,
        )

        if resultado_mouse.datos is None:
            resultado_mouse.datos = {}

        resultado_mouse.accion = (
            "mover_mouse_ventana"
        )

        resultado_mouse.datos.update({
            "ventana":
                ventana.titulo,

            "hwnd":
                ventana.hwnd,

            "x_relativo":
                x_relativo,

            "y_relativo":
                y_relativo,
        })

        return resultado_mouse

    # =========================================================
    # CLICK
    # =========================================================

    def _flags_boton(
        self,
        boton: BotonMouse,
    ) -> tuple[int, int]:

        if boton == BotonMouse.DERECHO:

            return (
                self.MOUSEEVENTF_RIGHTDOWN,
                self.MOUSEEVENTF_RIGHTUP,
            )

        if boton == BotonMouse.MEDIO:

            return (
                self.MOUSEEVENTF_MIDDLEDOWN,
                self.MOUSEEVENTF_MIDDLEUP,
            )

        return (
            self.MOUSEEVENTF_LEFTDOWN,
            self.MOUSEEVENTF_LEFTUP,
        )

    def click(
        self,
        boton: BotonMouse = BotonMouse.IZQUIERDO,
        cantidad: int = 1,
        intervalo: float = 0.12,
    ) -> ResultadoMouse:

        if not self.disponible:
            return self._no_disponible(
                "click_mouse"
            )

        cantidad = max(
            1,
            min(
                3,
                int(
                    cantidad
                ),
            ),
        )

        intervalo = max(
            0.05,
            min(
                1.0,
                float(
                    intervalo
                ),
            ),
        )

        abajo, arriba = (
            self._flags_boton(
                boton
            )
        )

        for indice in range(
            cantidad
        ):

            self._user32.mouse_event(
                abajo,
                0,
                0,
                0,
                None,
            )

            self._user32.mouse_event(
                arriba,
                0,
                0,
                0,
                None,
            )

            if (
                indice
                < cantidad - 1
            ):

                time.sleep(
                    intervalo
                )

        posicion = self.posicion()

        return ResultadoMouse(
            ok=True,
            accion="click_mouse",
            posicion=(
                posicion.posicion
                if posicion.ok
                else None
            ),
            mensaje=(
                f"{cantidad} click(s) "
                f"con botón {boton.value}."
            ),
            datos={
                "boton":
                    boton.value,

                "cantidad":
                    cantidad,
            },
        )

    def doble_click(
        self,
        boton: BotonMouse = BotonMouse.IZQUIERDO,
    ) -> ResultadoMouse:

        resultado = self.click(
            boton=boton,
            cantidad=2,
            intervalo=0.10,
        )

        resultado.accion = (
            "doble_click_mouse"
        )

        return resultado

    # =========================================================
    # CLICK EN VENTANA
    # =========================================================

    def click_relativo_ventana(
        self,
        titulo: str,
        x_relativo: float,
        y_relativo: float,
        boton: BotonMouse = BotonMouse.IZQUIERDO,
        doble: bool = False,
        duracion_movimiento: float = 0.15,
    ) -> ResultadoMouse:

        movimiento = (
            self.mover_relativo_ventana(
                titulo=titulo,
                x_relativo=x_relativo,
                y_relativo=y_relativo,
                duracion=duracion_movimiento,
                activar_ventana=True,
            )
        )

        if not movimiento.ok:
            return movimiento

        if doble:

            resultado = self.doble_click(
                boton=boton
            )

            resultado.accion = (
                "doble_click_mouse_ventana"
            )

        else:

            resultado = self.click(
                boton=boton
            )

            resultado.accion = (
                "click_mouse_ventana"
            )

        if resultado.datos is None:
            resultado.datos = {}

        resultado.datos.update({
            "ventana":
                titulo,

            "x_relativo":
                max(
                    0.0,
                    min(
                        1.0,
                        float(
                            x_relativo
                        ),
                    ),
                ),

            "y_relativo":
                max(
                    0.0,
                    min(
                        1.0,
                        float(
                            y_relativo
                        ),
                    ),
                ),
        })

        return resultado

    # =========================================================
    # SCROLL
    # =========================================================

    def scroll(
        self,
        pasos: int,
    ) -> ResultadoMouse:

        if not self.disponible:
            return self._no_disponible(
                "scroll_mouse"
            )

        pasos = max(
            -20,
            min(
                20,
                int(
                    pasos
                ),
            ),
        )

        if pasos == 0:

            return ResultadoMouse(
                ok=True,
                accion="scroll_mouse",
                mensaje="Sin desplazamiento.",
                datos={
                    "pasos":
                        0
                },
            )

        delta = (
            pasos
            * self.WHEEL_DELTA
        )

        self._user32.mouse_event(
            self.MOUSEEVENTF_WHEEL,
            0,
            0,
            delta,
            None,
        )

        return ResultadoMouse(
            ok=True,
            accion="scroll_mouse",
            mensaje=(
                f"Scroll aplicado: {pasos}."
            ),
            datos={
                "pasos":
                    pasos,

                "delta":
                    delta,
            },
        )