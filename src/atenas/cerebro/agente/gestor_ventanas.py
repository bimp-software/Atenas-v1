from __future__ import annotations

import ctypes
import platform

from ctypes import wintypes
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VentanaSistema:
    hwnd: int
    titulo: str
    visible: bool

    proceso_id: int | None = None

    x: int | None = None
    y: int | None = None
    ancho: int | None = None
    alto: int | None = None

    activa: bool = False


@dataclass
class ResultadoVentanas:
    ok: bool
    accion: str

    ventanas: list[VentanaSistema] = field(
        default_factory=list
    )

    ventana: VentanaSistema | None = None

    mensaje: str = ""
    error: str | None = None


class GestorVentanas:
    """
    Gestor estructurado de ventanas.

    En Windows utiliza Win32 mediante ctypes, por lo que no requiere
    pywin32 ni otra dependencia externa.

    Capacidades:
    - listar ventanas visibles;
    - conocer la ventana activa;
    - buscar por título;
    - activar/traer al frente;
    - minimizar;
    - maximizar;
    - restaurar;
    - conocer posición y tamaño.

    No mueve el mouse ni escribe texto.
    """

    SW_HIDE = 0
    SW_SHOWNORMAL = 1
    SW_SHOWMINIMIZED = 2
    SW_SHOWMAXIMIZED = 3
    SW_RESTORE = 9

    def __init__(self):
        self.sistema = (
            platform.system()
            .strip()
            .lower()
        )

        self.disponible = (
            self.sistema == "windows"
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

        self._user32.GetWindowTextLengthW.argtypes = [
            wintypes.HWND
        ]

        self._user32.GetWindowTextLengthW.restype = (
            ctypes.c_int
        )

        self._user32.GetWindowTextW.argtypes = [
            wintypes.HWND,
            wintypes.LPWSTR,
            ctypes.c_int,
        ]

        self._user32.GetWindowTextW.restype = (
            ctypes.c_int
        )

        self._user32.IsWindowVisible.argtypes = [
            wintypes.HWND
        ]

        self._user32.IsWindowVisible.restype = (
            wintypes.BOOL
        )

        self._user32.GetForegroundWindow.restype = (
            wintypes.HWND
        )

        self._user32.GetWindowRect.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(
                wintypes.RECT
            ),
        ]

        self._user32.GetWindowRect.restype = (
            wintypes.BOOL
        )

        self._user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(
                wintypes.DWORD
            ),
        ]

        self._user32.GetWindowThreadProcessId.restype = (
            wintypes.DWORD
        )

        self._user32.ShowWindow.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
        ]

        self._user32.ShowWindow.restype = (
            wintypes.BOOL
        )

        self._user32.SetForegroundWindow.argtypes = [
            wintypes.HWND
        ]

        self._user32.SetForegroundWindow.restype = (
            wintypes.BOOL
        )

        self._user32.BringWindowToTop.argtypes = [
            wintypes.HWND
        ]

        self._user32.BringWindowToTop.restype = (
            wintypes.BOOL
        )

        self._user32.IsWindow.argtypes = [
            wintypes.HWND
        ]

        self._user32.IsWindow.restype = (
            wintypes.BOOL
        )

    # =========================================================
    # UTILIDADES
    # =========================================================

    def _no_disponible(
        self,
        accion: str,
    ) -> ResultadoVentanas:

        return ResultadoVentanas(
            ok=False,
            accion=accion,
            error="gestor_ventanas_no_disponible",
            mensaje=(
                "La primera versión de GestorVentanas "
                "está implementada para Windows."
            ),
        )

    def _titulo_windows(
        self,
        hwnd: int,
    ) -> str:

        longitud = (
            self._user32
            .GetWindowTextLengthW(
                hwnd
            )
        )

        if longitud <= 0:
            return ""

        buffer = ctypes.create_unicode_buffer(
            longitud + 1
        )

        self._user32.GetWindowTextW(
            hwnd,
            buffer,
            longitud + 1,
        )

        return (
            buffer.value
            or ""
        ).strip()

    def _ventana_windows(
        self,
        hwnd: int,
    ) -> VentanaSistema | None:

        if not self._user32.IsWindow(
            hwnd
        ):
            return None

        titulo = (
            self._titulo_windows(
                hwnd
            )
        )

        visible = bool(
            self._user32
            .IsWindowVisible(
                hwnd
            )
        )

        rect = wintypes.RECT()

        tiene_rect = bool(
            self._user32
            .GetWindowRect(
                hwnd,
                ctypes.byref(
                    rect
                ),
            )
        )

        pid = wintypes.DWORD()

        self._user32.GetWindowThreadProcessId(
            hwnd,
            ctypes.byref(
                pid
            ),
        )

        activa_hwnd = (
            self._user32
            .GetForegroundWindow()
        )

        return VentanaSistema(
            hwnd=int(
                hwnd
            ),
            titulo=titulo,
            visible=visible,
            proceso_id=int(
                pid.value
            ),
            x=(
                int(
                    rect.left
                )
                if tiene_rect
                else None
            ),
            y=(
                int(
                    rect.top
                )
                if tiene_rect
                else None
            ),
            ancho=(
                int(
                    rect.right
                    - rect.left
                )
                if tiene_rect
                else None
            ),
            alto=(
                int(
                    rect.bottom
                    - rect.top
                )
                if tiene_rect
                else None
            ),
            activa=(
                int(
                    activa_hwnd
                    or 0
                )
                == int(
                    hwnd
                )
            ),
        )

    # =========================================================
    # LISTAR
    # =========================================================

    def listar(
        self,
        incluir_sin_titulo: bool = False,
        limite: int = 200,
    ) -> ResultadoVentanas:

        if not self.disponible:
            return self._no_disponible(
                "listar_ventanas"
            )

        ventanas: list[
            VentanaSistema
        ] = []

        WNDENUMPROC = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HWND,
            wintypes.LPARAM,
        )

        @WNDENUMPROC
        def callback(
            hwnd,
            lparam,
        ):

            if len(
                ventanas
            ) >= max(
                1,
                int(
                    limite
                ),
            ):
                return False

            ventana = (
                self._ventana_windows(
                    hwnd
                )
            )

            if ventana is None:
                return True

            if not ventana.visible:
                return True

            if (
                not incluir_sin_titulo
                and not ventana.titulo
            ):
                return True

            ventanas.append(
                ventana
            )

            return True

        self._user32.EnumWindows(
            callback,
            0,
        )

        ventanas.sort(
            key=lambda item: (
                not item.activa,
                item.titulo.lower(),
            )
        )

        return ResultadoVentanas(
            ok=True,
            accion="listar_ventanas",
            ventanas=ventanas,
            mensaje=(
                f"{len(ventanas)} "
                "ventana(s) visible(s)."
            ),
        )

    # =========================================================
    # ACTIVA
    # =========================================================

    def activa(
        self,
    ) -> ResultadoVentanas:

        if not self.disponible:
            return self._no_disponible(
                "ventana_activa"
            )

        hwnd = (
            self._user32
            .GetForegroundWindow()
        )

        if not hwnd:

            return ResultadoVentanas(
                ok=False,
                accion="ventana_activa",
                error="sin_ventana_activa",
            )

        ventana = (
            self._ventana_windows(
                hwnd
            )
        )

        if ventana is None:

            return ResultadoVentanas(
                ok=False,
                accion="ventana_activa",
                error="ventana_invalida",
            )

        return ResultadoVentanas(
            ok=True,
            accion="ventana_activa",
            ventana=ventana,
            mensaje=(
                f"Ventana activa: "
                f"{ventana.titulo}"
            ),
        )

    # =========================================================
    # BUSCAR
    # =========================================================

    def buscar(
        self,
        titulo: str,
        exacto: bool = False,
    ) -> ResultadoVentanas:

        consulta = (
            titulo
            or ""
        ).strip().lower()

        if not consulta:

            return ResultadoVentanas(
                ok=False,
                accion="buscar_ventana",
                error="titulo_vacio",
            )

        listado = self.listar()

        if not listado.ok:
            return listado

        coincidencias = []

        for ventana in listado.ventanas:

            actual = (
                ventana.titulo
                or ""
            ).strip().lower()

            if exacto:

                coincide = (
                    actual
                    == consulta
                )

            else:

                coincide = (
                    consulta
                    in actual
                )

            if coincide:

                coincidencias.append(
                    ventana
                )

        if not coincidencias:

            return ResultadoVentanas(
                ok=False,
                accion="buscar_ventana",
                error="ventana_no_encontrada",
                mensaje=(
                    f"No se encontró una ventana "
                    f"con título: {titulo}"
                ),
            )

        return ResultadoVentanas(
            ok=True,
            accion="buscar_ventana",
            ventanas=coincidencias,
            ventana=(
                coincidencias[0]
            ),
            mensaje=(
                f"{len(coincidencias)} "
                "coincidencia(s)."
            ),
        )

    # =========================================================
    # RESOLVER HWND
    # =========================================================

    def _resolver_hwnd(
        self,
        hwnd: int | None = None,
        titulo: str | None = None,
    ) -> tuple[
        int | None,
        str | None,
    ]:

        if hwnd is not None:

            if (
                self.disponible
                and self._user32.IsWindow(
                    int(
                        hwnd
                    )
                )
            ):

                return (
                    int(
                        hwnd
                    ),
                    None,
                )

            return (
                None,
                "hwnd_invalido",
            )

        if titulo:

            resultado = self.buscar(
                titulo
            )

            if (
                resultado.ok
                and resultado.ventana
            ):

                return (
                    resultado.ventana.hwnd,
                    None,
                )

            return (
                None,
                resultado.error
                or "ventana_no_encontrada",
            )

        return (
            None,
            "sin_identificador_ventana",
        )

    # =========================================================
    # ACTIVAR
    # =========================================================

    def activar(
        self,
        hwnd: int | None = None,
        titulo: str | None = None,
    ) -> ResultadoVentanas:

        if not self.disponible:
            return self._no_disponible(
                "activar_ventana"
            )

        objetivo, error = (
            self._resolver_hwnd(
                hwnd=hwnd,
                titulo=titulo,
            )
        )

        if objetivo is None:

            return ResultadoVentanas(
                ok=False,
                accion="activar_ventana",
                error=error,
            )

        self._user32.ShowWindow(
            objetivo,
            self.SW_RESTORE,
        )

        self._user32.BringWindowToTop(
            objetivo
        )

        ok = bool(
            self._user32.SetForegroundWindow(
                objetivo
            )
        )

        ventana = (
            self._ventana_windows(
                objetivo
            )
        )

        return ResultadoVentanas(
            ok=(
                ok
                or (
                    ventana is not None
                    and ventana.activa
                )
            ),
            accion="activar_ventana",
            ventana=ventana,
            mensaje=(
                "Ventana activada."
                if ok
                else (
                    "Windows recibió la solicitud "
                    "de activar la ventana."
                )
            ),
        )

    # =========================================================
    # ESTADO VISUAL
    # =========================================================

    def _mostrar(
        self,
        codigo: int,
        accion: str,
        hwnd: int | None = None,
        titulo: str | None = None,
    ) -> ResultadoVentanas:

        if not self.disponible:
            return self._no_disponible(
                accion
            )

        objetivo, error = (
            self._resolver_hwnd(
                hwnd=hwnd,
                titulo=titulo,
            )
        )

        if objetivo is None:

            return ResultadoVentanas(
                ok=False,
                accion=accion,
                error=error,
            )

        self._user32.ShowWindow(
            objetivo,
            codigo,
        )

        ventana = (
            self._ventana_windows(
                objetivo
            )
        )

        return ResultadoVentanas(
            ok=True,
            accion=accion,
            ventana=ventana,
            mensaje=(
                f"Acción '{accion}' "
                "enviada a la ventana."
            ),
        )

    def minimizar(
        self,
        hwnd: int | None = None,
        titulo: str | None = None,
    ) -> ResultadoVentanas:

        return self._mostrar(
            codigo=self.SW_SHOWMINIMIZED,
            accion="minimizar_ventana",
            hwnd=hwnd,
            titulo=titulo,
        )

    def maximizar(
        self,
        hwnd: int | None = None,
        titulo: str | None = None,
    ) -> ResultadoVentanas:

        return self._mostrar(
            codigo=self.SW_SHOWMAXIMIZED,
            accion="maximizar_ventana",
            hwnd=hwnd,
            titulo=titulo,
        )

    def restaurar(
        self,
        hwnd: int | None = None,
        titulo: str | None = None,
    ) -> ResultadoVentanas:

        return self._mostrar(
            codigo=self.SW_RESTORE,
            accion="restaurar_ventana",
            hwnd=hwnd,
            titulo=titulo,
        )