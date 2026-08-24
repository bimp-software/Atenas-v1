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


class TeclaEspecial(str, Enum):
    ENTER = "enter"
    ESC = "esc"
    TAB = "tab"
    BACKSPACE = "backspace"
    DELETE = "delete"
    SPACE = "space"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    HOME = "home"
    END = "end"
    PAGEUP = "pageup"
    PAGEDOWN = "pagedown"
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    WIN = "win"
    F1 = "f1"
    F2 = "f2"
    F3 = "f3"
    F4 = "f4"
    F5 = "f5"
    F6 = "f6"
    F7 = "f7"
    F8 = "f8"
    F9 = "f9"
    F10 = "f10"
    F11 = "f11"
    F12 = "f12"


@dataclass
class ResultadoTeclado:
    ok: bool
    accion: str

    mensaje: str = ""
    error: str | None = None

    datos: dict[str, Any] | None = None


class ControladorTeclado:
    """
    Control estructurado del teclado para Windows.

    Permite:
    - escribir texto Unicode;
    - pulsar teclas especiales;
    - combinaciones seguras como Ctrl+S, Ctrl+C, Ctrl+V;
    - escribir dentro de una ventana concreta, activándola primero.

    No ejecuta comandos de terminal ni interpreta instrucciones libres.
    """

    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_UNICODE = 0x0004

    VK = {
        "enter": 0x0D,
        "esc": 0x1B,
        "tab": 0x09,
        "backspace": 0x08,
        "delete": 0x2E,
        "space": 0x20,
        "up": 0x26,
        "down": 0x28,
        "left": 0x25,
        "right": 0x27,
        "home": 0x24,
        "end": 0x23,
        "pageup": 0x21,
        "pagedown": 0x22,
        "ctrl": 0x11,
        "alt": 0x12,
        "shift": 0x10,
        "win": 0x5B,
        "f1": 0x70,
        "f2": 0x71,
        "f3": 0x72,
        "f4": 0x73,
        "f5": 0x74,
        "f6": 0x75,
        "f7": 0x76,
        "f8": 0x77,
        "f9": 0x78,
        "f10": 0x79,
        "f11": 0x7A,
        "f12": 0x7B,
    }

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

    def _inicializar_windows(
        self,
    ) -> None:

        self._user32 = (
            ctypes.windll.user32
        )

        self._user32.keybd_event.argtypes = [
            wintypes.BYTE,
            wintypes.BYTE,
            wintypes.DWORD,
            ctypes.POINTER(
                ctypes.c_ulong
            ),
        ]

    def _no_disponible(
        self,
        accion: str,
    ) -> ResultadoTeclado:

        return ResultadoTeclado(
            ok=False,
            accion=accion,
            error="control_teclado_no_disponible",
            mensaje=(
                "La primera versión del controlador de teclado "
                "está implementada para Windows."
            ),
        )

    # =========================================================
    # TECLA SIMPLE
    # =========================================================

    def _vk(
        self,
        tecla: str,
    ) -> int | None:

        clave = (
            tecla
            or ""
        ).strip().lower()

        if clave in self.VK:
            return self.VK[
                clave
            ]

        if len(clave) == 1:
            codigo = (
                self._user32
                .VkKeyScanW(
                    ord(
                        clave
                    )
                )
            )

            if codigo == -1:
                return None

            return (
                codigo
                & 0xFF
            )

        return None

    def pulsar(
        self,
        tecla: str,
        repeticiones: int = 1,
        intervalo: float = 0.05,
    ) -> ResultadoTeclado:

        if not self.disponible:
            return self._no_disponible(
                "pulsar_tecla"
            )

        vk = self._vk(
            tecla
        )

        if vk is None:

            return ResultadoTeclado(
                ok=False,
                accion="pulsar_tecla",
                error="tecla_no_soportada",
                mensaje=(
                    f"Tecla no soportada: {tecla}"
                ),
            )

        repeticiones = max(
            1,
            min(
                20,
                int(
                    repeticiones
                ),
            ),
        )

        intervalo = max(
            0.01,
            min(
                0.5,
                float(
                    intervalo
                ),
            ),
        )

        for indice in range(
            repeticiones
        ):

            self._user32.keybd_event(
                vk,
                0,
                0,
                None,
            )

            self._user32.keybd_event(
                vk,
                0,
                self.KEYEVENTF_KEYUP,
                None,
            )

            if (
                indice
                < repeticiones - 1
            ):

                time.sleep(
                    intervalo
                )

        return ResultadoTeclado(
            ok=True,
            accion="pulsar_tecla",
            mensaje=(
                f"Tecla '{tecla}' pulsada "
                f"{repeticiones} vez/veces."
            ),
            datos={
                "tecla":
                    tecla,

                "repeticiones":
                    repeticiones,
            },
        )

    # =========================================================
    # TEXTO UNICODE
    # =========================================================

    def escribir_texto(
        self,
        texto: str,
        intervalo: float = 0.0,
    ) -> ResultadoTeclado:

        if not self.disponible:
            return self._no_disponible(
                "escribir_teclado"
            )

        texto = (
            texto
            or ""
        )

        if not texto:

            return ResultadoTeclado(
                ok=True,
                accion="escribir_teclado",
                mensaje="No había texto para escribir.",
                datos={
                    "caracteres":
                        0
                },
            )

        intervalo = max(
            0.0,
            min(
                0.25,
                float(
                    intervalo
                ),
            ),
        )

        # Limita escrituras masivas accidentales.
        texto = texto[:20000]

        for caracter in texto:

            unidad = ord(
                caracter
            )

            self._user32.keybd_event(
                0,
                unidad,
                self.KEYEVENTF_UNICODE,
                None,
            )

            self._user32.keybd_event(
                0,
                unidad,
                (
                    self.KEYEVENTF_UNICODE
                    | self.KEYEVENTF_KEYUP
                ),
                None,
            )

            if intervalo > 0:
                time.sleep(
                    intervalo
                )

        return ResultadoTeclado(
            ok=True,
            accion="escribir_teclado",
            mensaje=(
                f"Se escribieron {len(texto)} caracteres."
            ),
            datos={
                "caracteres":
                    len(
                        texto
                    )
            },
        )

    # =========================================================
    # COMBINACIONES
    # =========================================================

    def combinacion(
        self,
        teclas: list[str],
    ) -> ResultadoTeclado:

        if not self.disponible:
            return self._no_disponible(
                "combinacion_teclas"
            )

        if not teclas:

            return ResultadoTeclado(
                ok=False,
                accion="combinacion_teclas",
                error="sin_teclas",
            )

        if len(teclas) > 4:

            return ResultadoTeclado(
                ok=False,
                accion="combinacion_teclas",
                error="demasiadas_teclas",
            )

        vks = []

        for tecla in teclas:

            vk = self._vk(
                tecla
            )

            if vk is None:

                return ResultadoTeclado(
                    ok=False,
                    accion="combinacion_teclas",
                    error="tecla_no_soportada",
                    mensaje=(
                        f"Tecla no soportada: {tecla}"
                    ),
                )

            vks.append(
                vk
            )

        for vk in vks:

            self._user32.keybd_event(
                vk,
                0,
                0,
                None,
            )

        for vk in reversed(
            vks
        ):

            self._user32.keybd_event(
                vk,
                0,
                self.KEYEVENTF_KEYUP,
                None,
            )

        return ResultadoTeclado(
            ok=True,
            accion="combinacion_teclas",
            mensaje=(
                "Combinación ejecutada: "
                + "+".join(
                    teclas
                )
            ),
            datos={
                "teclas":
                    teclas
            },
        )

    # =========================================================
    # VENTANA
    # =========================================================

    def escribir_en_ventana(
        self,
        titulo: str,
        texto: str,
        intervalo: float = 0.0,
    ) -> ResultadoTeclado:

        resultado_ventana = (
            self.gestor_ventanas
            .activar(
                titulo=titulo
            )
        )

        if not resultado_ventana.ok:

            return ResultadoTeclado(
                ok=False,
                accion="escribir_en_ventana",
                error=(
                    resultado_ventana.error
                    or "no_se_pudo_activar_ventana"
                ),
            )

        time.sleep(
            0.08
        )

        resultado = (
            self.escribir_texto(
                texto=texto,
                intervalo=intervalo,
            )
        )

        resultado.accion = (
            "escribir_en_ventana"
        )

        if resultado.datos is None:
            resultado.datos = {}

        resultado.datos[
            "ventana"
        ] = titulo

        return resultado

    def combinacion_en_ventana(
        self,
        titulo: str,
        teclas: list[str],
    ) -> ResultadoTeclado:

        resultado_ventana = (
            self.gestor_ventanas
            .activar(
                titulo=titulo
            )
        )

        if not resultado_ventana.ok:

            return ResultadoTeclado(
                ok=False,
                accion="combinacion_teclas_ventana",
                error=(
                    resultado_ventana.error
                    or "no_se_pudo_activar_ventana"
                ),
            )

        time.sleep(
            0.08
        )

        resultado = (
            self.combinacion(
                teclas
            )
        )

        resultado.accion = (
            "combinacion_teclas_ventana"
        )

        if resultado.datos is None:
            resultado.datos = {}

        resultado.datos[
            "ventana"
        ] = titulo

        return resultado