from __future__ import annotations

import csv
import io
import os
import platform
import shutil
import subprocess

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .gestor_ventanas import (
    GestorVentanas,
)

from .controlador_mouse import (
    BotonMouse,
    ControladorMouse,
)

from .controlador_teclado import (
    ControladorTeclado,
)

from .capturador_pantalla import (
    CapturadorPantalla,
)

from .percepcion_visual import (
    PercepcionVisual,
)

from .interpretador_visual import (
    InterpretadorVisual,
)

from .adaptador_vision_ollama import (
    AdaptadorVisionOllama,
)

from .ejecutor_gui import (
    EjecutorGUI,
)

from .verificador_visual import (
    VerificadorVisual,
)

from .ciclo_accion_gui import (
    CicloAccionGUI,
)


class TipoAccionSistema(str, Enum):
    LEER_TEXTO = "leer_texto"
    LISTAR_DIRECTORIO = "listar_directorio"
    CREAR_CARPETA = "crear_carpeta"
    ESCRIBIR_TEXTO = "escribir_texto"

    ABRIR_RUTA = "abrir_ruta"
    ABRIR_APLICACION = "abrir_aplicacion"

    LISTAR_PROCESOS = "listar_procesos"

    LISTAR_VENTANAS = "listar_ventanas"
    VENTANA_ACTIVA = "ventana_activa"
    ACTIVAR_VENTANA = "activar_ventana"
    MINIMIZAR_VENTANA = "minimizar_ventana"
    MAXIMIZAR_VENTANA = "maximizar_ventana"
    RESTAURAR_VENTANA = "restaurar_ventana"

    POSICION_MOUSE = "posicion_mouse"
    MOVER_MOUSE = "mover_mouse"
    MOVER_MOUSE_VENTANA = "mover_mouse_ventana"
    CLICK_MOUSE = "click_mouse"
    DOBLE_CLICK_MOUSE = "doble_click_mouse"
    CLICK_MOUSE_VENTANA = "click_mouse_ventana"
    SCROLL_MOUSE = "scroll_mouse"

    ESCRIBIR_TECLADO = "escribir_teclado"
    PULSAR_TECLA = "pulsar_tecla"
    COMBINACION_TECLAS = "combinacion_teclas"
    ESCRIBIR_EN_VENTANA = "escribir_en_ventana"
    COMBINACION_TECLAS_VENTANA = "combinacion_teclas_ventana"

    CAPTURAR_PANTALLA = "capturar_pantalla"
    CAPTURAR_VENTANA = "capturar_ventana"
    LISTAR_CAPTURAS = "listar_capturas"
    CONSTRUIR_ESTADO_VISUAL = "construir_estado_visual"
    INTERPRETAR_ESCENA = "interpretar_escena"
    ESTADO_VISION = "estado_vision"


@dataclass
class AccionSistema:
    tipo: TipoAccionSistema

    argumentos: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ResultadoAccionSistema:
    ok: bool
    accion: str

    mensaje: str = ""

    datos: dict[str, Any] = field(
        default_factory=dict
    )

    error: str | None = None


class EjecutorSistema:
    """
    Interacción estructurada con el computador.

    Nunca ejecuta texto libre como shell.
    """

    def __init__(
        self,
        raices_escritura: list[
            str | Path
        ] | None = None,
        aplicaciones: dict[
            str,
            list[str],
        ] | None = None,
        gestor_ventanas: (
            GestorVentanas
            | None
        ) = None,
        controlador_mouse: (
            ControladorMouse
            | None
        ) = None,
        controlador_teclado: (
            ControladorTeclado
            | None
        ) = None,
        capturador_pantalla: (
            CapturadorPantalla
            | None
        ) = None,
        percepcion_visual: (
            PercepcionVisual
            | None
        ) = None,
        interpretador_visual: (
            InterpretadorVisual
            | None
        ) = None,
        vision_ollama: (
            AdaptadorVisionOllama
            | None
        ) = None,
    ):

        if raices_escritura is None:

            home = Path.home()

            candidatos = [
                home / "Desktop",
                home / "Documents",
            ]

            self.raices_escritura = [
                ruta.resolve()
                for ruta
                in candidatos
                if ruta.exists()
            ]

        else:

            self.raices_escritura = [
                Path(
                    ruta
                ).expanduser().resolve()
                for ruta
                in raices_escritura
            ]

        self.aplicaciones = (
            aplicaciones
            or self._aplicaciones_por_defecto()
        )

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

        self.controlador_teclado = (
            controlador_teclado
            or ControladorTeclado(
                gestor_ventanas=(
                    self.gestor_ventanas
                )
            )
        )

        self.capturador_pantalla = (
            capturador_pantalla
            or CapturadorPantalla(
                gestor_ventanas=(
                    self.gestor_ventanas
                )
            )
        )

        self.percepcion_visual = (
            percepcion_visual
            or PercepcionVisual(
                capturador=(
                    self.capturador_pantalla
                ),
                gestor_ventanas=(
                    self.gestor_ventanas
                ),
                controlador_mouse=(
                    self.controlador_mouse
                ),
            )
        )

        self.vision_ollama = (
            vision_ollama
            or AdaptadorVisionOllama()
        )

        self.interpretador_visual = (
            interpretador_visual
            or InterpretadorVisual(
                vision=(
                    self.vision_ollama
                )
            )
        )

        self.ejecutor_gui = (
            EjecutorGUI(
                mouse=(
                    self.controlador_mouse
                ),
                teclado=(
                    self.controlador_teclado
                ),
            )
        )

        self.verificador_visual = (
            VerificadorVisual()
        )

        self.ciclo_accion_gui = (
            CicloAccionGUI(
                ejecutor_gui=(
                    self.ejecutor_gui
                ),
                percepcion_visual=(
                    self.percepcion_visual
                ),
                interpretador_visual=(
                    self.interpretador_visual
                ),
                verificador_visual=(
                    self.verificador_visual
                ),
            )
        )

    # =========================================================
    # APPS
    # =========================================================

    @staticmethod
    def _aplicaciones_por_defecto(
    ) -> dict[str, list[str]]:

        sistema = (
            platform.system()
            .lower()
        )

        if sistema == "windows":

            return {
                "explorador": [
                    "explorer.exe",
                ],
                "notepad": [
                    "notepad.exe",
                ],
                "bloc_notas": [
                    "notepad.exe",
                ],
                "powershell": [
                    "powershell.exe",
                ],
                "cmd": [
                    "cmd.exe",
                ],
                "vscode": [
                    "code",
                ],
                "visual_studio_code": [
                    "code",
                ],
            }

        if sistema == "darwin":

            return {
                "finder": [
                    "open",
                    ".",
                ],
                "terminal": [
                    "open",
                    "-a",
                    "Terminal",
                ],
                "textedit": [
                    "open",
                    "-a",
                    "TextEdit",
                ],
                "vscode": [
                    "code",
                ],
            }

        return {
            "archivos": [
                "xdg-open",
                ".",
            ],
            "vscode": [
                "code",
            ],
        }

    def registrar_aplicacion(
        self,
        alias: str,
        comando: list[str],
    ) -> None:

        alias = (
            alias
            or ""
        ).strip().lower()

        if not alias:
            raise ValueError(
                "El alias no puede estar vacío."
            )

        if not comando:
            raise ValueError(
                "El comando estructurado no puede estar vacío."
            )

        self.aplicaciones[
            alias
        ] = [
            str(item)
            for item
            in comando
        ]

    # =========================================================
    # RUTAS
    # =========================================================

    @staticmethod
    def _resolver(
        ruta: str | Path,
    ) -> Path:

        return Path(
            ruta
        ).expanduser().resolve()

    def _es_ruta_escribible(
        self,
        ruta: Path,
    ) -> bool:

        for raiz in (
            self.raices_escritura
        ):

            try:

                ruta.relative_to(
                    raiz
                )

                return True

            except ValueError:

                continue

        return False

    def _validar_escritura(
        self,
        ruta: Path,
    ) -> None:

        if not self._es_ruta_escribible(
            ruta
        ):

            raise PermissionError(
                (
                    "Ruta fuera de las raíces "
                    f"autorizadas: {ruta}"
                )
            )

    # =========================================================
    # ARCHIVOS
    # =========================================================

    def leer_texto(
        self,
        ruta: str | Path,
        max_bytes: int = 2_000_000,
    ) -> ResultadoAccionSistema:

        archivo = self._resolver(
            ruta
        )

        if not archivo.exists():

            return ResultadoAccionSistema(
                ok=False,
                accion="leer_texto",
                error="archivo_no_existe",
            )

        if not archivo.is_file():

            return ResultadoAccionSistema(
                ok=False,
                accion="leer_texto",
                error="ruta_no_es_archivo",
            )

        tamaño = (
            archivo.stat().st_size
        )

        if tamaño > max_bytes:

            return ResultadoAccionSistema(
                ok=False,
                accion="leer_texto",
                error="archivo_demasiado_grande",
            )

        try:

            contenido = (
                archivo.read_text(
                    encoding="utf-8"
                )
            )

        except UnicodeDecodeError:

            return ResultadoAccionSistema(
                ok=False,
                accion="leer_texto",
                error="archivo_no_utf8",
            )

        return ResultadoAccionSistema(
            ok=True,
            accion="leer_texto",
            mensaje="Archivo leído.",
            datos={
                "ruta":
                    str(
                        archivo
                    ),

                "contenido":
                    contenido,

                "bytes":
                    tamaño,
            },
        )

    def listar_directorio(
        self,
        ruta: str | Path,
        limite: int = 200,
    ) -> ResultadoAccionSistema:

        carpeta = self._resolver(
            ruta
        )

        if not carpeta.exists():

            return ResultadoAccionSistema(
                ok=False,
                accion="listar_directorio",
                error="carpeta_no_existe",
            )

        if not carpeta.is_dir():

            return ResultadoAccionSistema(
                ok=False,
                accion="listar_directorio",
                error="ruta_no_es_directorio",
            )

        elementos = []

        for item in sorted(
            carpeta.iterdir(),
            key=lambda x: (
                not x.is_dir(),
                x.name.lower(),
            ),
        )[:max(
            1,
            int(
                limite
            ),
        )]:

            elementos.append({
                "nombre":
                    item.name,

                "ruta":
                    str(
                        item
                    ),

                "tipo":
                    (
                        "carpeta"
                        if item.is_dir()
                        else "archivo"
                    ),

                "bytes":
                    (
                        item.stat().st_size
                        if item.is_file()
                        else None
                    ),
            })

        return ResultadoAccionSistema(
            ok=True,
            accion="listar_directorio",
            mensaje=(
                f"{len(elementos)} elemento(s)."
            ),
            datos={
                "ruta":
                    str(
                        carpeta
                    ),

                "elementos":
                    elementos,
            },
        )

    def crear_carpeta(
        self,
        ruta: str | Path,
    ) -> ResultadoAccionSistema:

        carpeta = self._resolver(
            ruta
        )

        try:

            self._validar_escritura(
                carpeta
            )

            carpeta.mkdir(
                parents=True,
                exist_ok=True,
            )

            return ResultadoAccionSistema(
                ok=True,
                accion="crear_carpeta",
                mensaje="Carpeta disponible.",
                datos={
                    "ruta":
                        str(
                            carpeta
                        )
                },
            )

        except Exception as error:

            return ResultadoAccionSistema(
                ok=False,
                accion="crear_carpeta",
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    def escribir_texto(
        self,
        ruta: str | Path,
        contenido: str,
        sobrescribir: bool = False,
    ) -> ResultadoAccionSistema:

        archivo = self._resolver(
            ruta
        )

        try:

            self._validar_escritura(
                archivo
            )

            if (
                archivo.exists()
                and not sobrescribir
            ):

                return ResultadoAccionSistema(
                    ok=False,
                    accion="escribir_texto",
                    error="archivo_ya_existe",
                )

            archivo.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            archivo.write_text(
                contenido,
                encoding="utf-8",
            )

            return ResultadoAccionSistema(
                ok=True,
                accion="escribir_texto",
                mensaje="Archivo escrito.",
                datos={
                    "ruta":
                        str(
                            archivo
                        ),

                    "bytes":
                        archivo.stat().st_size,
                },
            )

        except Exception as error:

            return ResultadoAccionSistema(
                ok=False,
                accion="escribir_texto",
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    # =========================================================
    # ABRIR
    # =========================================================

    def abrir_ruta(
        self,
        ruta: str | Path,
    ) -> ResultadoAccionSistema:

        destino = self._resolver(
            ruta
        )

        if not destino.exists():

            return ResultadoAccionSistema(
                ok=False,
                accion="abrir_ruta",
                error="ruta_no_existe",
            )

        try:

            sistema = (
                platform.system()
                .lower()
            )

            if sistema == "windows":

                os.startfile(
                    str(
                        destino
                    )
                )

            elif sistema == "darwin":

                subprocess.Popen(
                    [
                        "open",
                        str(
                            destino
                        ),
                    ],
                    shell=False,
                )

            else:

                subprocess.Popen(
                    [
                        "xdg-open",
                        str(
                            destino
                        ),
                    ],
                    shell=False,
                )

            return ResultadoAccionSistema(
                ok=True,
                accion="abrir_ruta",
                mensaje="Ruta abierta.",
                datos={
                    "ruta":
                        str(
                            destino
                        )
                },
            )

        except Exception as error:

            return ResultadoAccionSistema(
                ok=False,
                accion="abrir_ruta",
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    def abrir_aplicacion(
        self,
        alias: str,
        argumentos: list[str] | None = None,
    ) -> ResultadoAccionSistema:

        clave = (
            alias
            or ""
        ).strip().lower()

        comando = (
            self.aplicaciones.get(
                clave
            )
        )

        if comando is None:

            return ResultadoAccionSistema(
                ok=False,
                accion="abrir_aplicacion",
                error="aplicacion_no_registrada",
                datos={
                    "disponibles":
                        sorted(
                            self.aplicaciones.keys()
                        )
                },
            )

        comando_final = list(
            comando
        )

        if argumentos:

            comando_final.extend(
                str(item)
                for item
                in argumentos
            )

        try:

            proceso = subprocess.Popen(
                comando_final,
                shell=False,
            )

            return ResultadoAccionSistema(
                ok=True,
                accion="abrir_aplicacion",
                mensaje=(
                    f"Aplicación '{clave}' iniciada."
                ),
                datos={
                    "alias":
                        clave,

                    "pid":
                        proceso.pid,
                },
            )

        except Exception as error:

            return ResultadoAccionSistema(
                ok=False,
                accion="abrir_aplicacion",
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    # =========================================================
    # PROCESOS
    # =========================================================

    def listar_procesos(
        self,
        limite: int = 300,
    ) -> ResultadoAccionSistema:

        sistema = (
            platform.system()
            .lower()
        )

        try:

            if sistema == "windows":

                proceso = subprocess.run(
                    [
                        "tasklist",
                        "/FO",
                        "CSV",
                        "/NH",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    shell=False,
                )

                if proceso.returncode != 0:

                    return ResultadoAccionSistema(
                        ok=False,
                        accion="listar_procesos",
                        error="tasklist_fallo",
                    )

                filas = csv.reader(
                    io.StringIO(
                        proceso.stdout
                    )
                )

                procesos = []

                for fila in filas:

                    if len(fila) < 2:
                        continue

                    procesos.append({
                        "nombre":
                            fila[0],

                        "pid":
                            fila[1],
                    })

                    if len(
                        procesos
                    ) >= limite:
                        break

            else:

                proceso = subprocess.run(
                    [
                        "ps",
                        "-eo",
                        "pid=,comm=",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    shell=False,
                )

                procesos = []

                for linea in (
                    proceso.stdout
                    or ""
                ).splitlines():

                    partes = (
                        linea.strip()
                        .split(
                            None,
                            1,
                        )
                    )

                    if len(partes) != 2:
                        continue

                    procesos.append({
                        "pid":
                            partes[0],

                        "nombre":
                            partes[1],
                    })

                    if len(
                        procesos
                    ) >= limite:
                        break

            return ResultadoAccionSistema(
                ok=True,
                accion="listar_procesos",
                mensaje=(
                    f"{len(procesos)} proceso(s)."
                ),
                datos={
                    "procesos":
                        procesos
                },
            )

        except Exception as error:

            return ResultadoAccionSistema(
                ok=False,
                accion="listar_procesos",
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    # =========================================================
    # VENTANAS
    # =========================================================

    def listar_ventanas(
        self,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.gestor_ventanas
            .listar()
        )

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion="listar_ventanas",
            mensaje=resultado.mensaje,
            error=resultado.error,
            datos={
                "ventanas": [
                    {
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
                    }
                    for v
                    in resultado.ventanas
                ]
            },
        )

    def ventana_activa(
        self,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.gestor_ventanas
            .activa()
        )

        datos = {}

        if resultado.ventana:

            v = resultado.ventana

            datos["ventana"] = {
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
            }

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion="ventana_activa",
            mensaje=resultado.mensaje,
            error=resultado.error,
            datos=datos,
        )

    def _accion_ventana(
        self,
        metodo: str,
        accion: str,
        hwnd: int | None = None,
        titulo: str | None = None,
    ) -> ResultadoAccionSistema:

        funcion = getattr(
            self.gestor_ventanas,
            metodo,
        )

        resultado = funcion(
            hwnd=hwnd,
            titulo=titulo,
        )

        datos = {}

        if resultado.ventana:

            v = resultado.ventana

            datos["ventana"] = {
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
            }

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=accion,
            mensaje=resultado.mensaje,
            error=resultado.error,
            datos=datos,
        )


    # =========================================================
    # MOUSE
    # =========================================================

    def posicion_mouse(
        self,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.controlador_mouse
            .posicion()
        )

        datos = {}

        if resultado.posicion:

            datos["posicion"] = {
                "x":
                    resultado.posicion.x,

                "y":
                    resultado.posicion.y,
            }

        if resultado.datos:

            datos.update(
                resultado.datos
            )

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=datos,
            error=resultado.error,
        )

    def mover_mouse(
        self,
        x: int,
        y: int,
        duracion: float = 0.0,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.controlador_mouse
            .mover(
                x=x,
                y=y,
                duracion=duracion,
            )
        )

        datos = {}

        if resultado.posicion:

            datos["posicion"] = {
                "x":
                    resultado.posicion.x,

                "y":
                    resultado.posicion.y,
            }

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=datos,
            error=resultado.error,
        )

    def mover_mouse_ventana(
        self,
        titulo: str,
        x_relativo: float,
        y_relativo: float,
        duracion: float = 0.15,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.controlador_mouse
            .mover_relativo_ventana(
                titulo=titulo,
                x_relativo=x_relativo,
                y_relativo=y_relativo,
                duracion=duracion,
            )
        )

        datos = (
            dict(
                resultado.datos
                or {}
            )
        )

        if resultado.posicion:

            datos["posicion"] = {
                "x":
                    resultado.posicion.x,

                "y":
                    resultado.posicion.y,
            }

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=datos,
            error=resultado.error,
        )

    def click_mouse(
        self,
        boton: str = "izquierdo",
        doble: bool = False,
    ) -> ResultadoAccionSistema:

        try:

            boton_enum = BotonMouse(
                boton
            )

        except ValueError:

            return ResultadoAccionSistema(
                ok=False,
                accion="click_mouse",
                error="boton_mouse_invalido",
            )

        if doble:

            resultado = (
                self.controlador_mouse
                .doble_click(
                    boton=boton_enum
                )
            )

        else:

            resultado = (
                self.controlador_mouse
                .click(
                    boton=boton_enum
                )
            )

        datos = (
            dict(
                resultado.datos
                or {}
            )
        )

        if resultado.posicion:

            datos["posicion"] = {
                "x":
                    resultado.posicion.x,

                "y":
                    resultado.posicion.y,
            }

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=datos,
            error=resultado.error,
        )

    def click_mouse_ventana(
        self,
        titulo: str,
        x_relativo: float,
        y_relativo: float,
        boton: str = "izquierdo",
        doble: bool = False,
    ) -> ResultadoAccionSistema:

        try:

            boton_enum = BotonMouse(
                boton
            )

        except ValueError:

            return ResultadoAccionSistema(
                ok=False,
                accion="click_mouse_ventana",
                error="boton_mouse_invalido",
            )

        resultado = (
            self.controlador_mouse
            .click_relativo_ventana(
                titulo=titulo,
                x_relativo=x_relativo,
                y_relativo=y_relativo,
                boton=boton_enum,
                doble=doble,
            )
        )

        datos = (
            dict(
                resultado.datos
                or {}
            )
        )

        if resultado.posicion:

            datos["posicion"] = {
                "x":
                    resultado.posicion.x,

                "y":
                    resultado.posicion.y,
            }

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=datos,
            error=resultado.error,
        )

    def scroll_mouse(
        self,
        pasos: int,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.controlador_mouse
            .scroll(
                pasos=pasos
            )
        )

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=(
                resultado.datos
                or {}
            ),
            error=resultado.error,
        )


    # =========================================================
    # TECLADO
    # =========================================================

    def escribir_teclado(
        self,
        texto: str,
        intervalo: float = 0.0,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.controlador_teclado
            .escribir_texto(
                texto=texto,
                intervalo=intervalo,
            )
        )

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=(
                resultado.datos
                or {}
            ),
            error=resultado.error,
        )

    def pulsar_tecla(
        self,
        tecla: str,
        repeticiones: int = 1,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.controlador_teclado
            .pulsar(
                tecla=tecla,
                repeticiones=repeticiones,
            )
        )

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=(
                resultado.datos
                or {}
            ),
            error=resultado.error,
        )

    def combinacion_teclas(
        self,
        teclas: list[str],
    ) -> ResultadoAccionSistema:

        resultado = (
            self.controlador_teclado
            .combinacion(
                teclas=teclas
            )
        )

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=(
                resultado.datos
                or {}
            ),
            error=resultado.error,
        )

    def escribir_en_ventana(
        self,
        titulo: str,
        texto: str,
        intervalo: float = 0.0,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.controlador_teclado
            .escribir_en_ventana(
                titulo=titulo,
                texto=texto,
                intervalo=intervalo,
            )
        )

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=(
                resultado.datos
                or {}
            ),
            error=resultado.error,
        )

    def combinacion_teclas_ventana(
        self,
        titulo: str,
        teclas: list[str],
    ) -> ResultadoAccionSistema:

        resultado = (
            self.controlador_teclado
            .combinacion_en_ventana(
                titulo=titulo,
                teclas=teclas,
            )
        )

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=(
                resultado.datos
                or {}
            ),
            error=resultado.error,
        )


    # =========================================================
    # CAPTURA / PERCEPCIÓN VISUAL BASE
    # =========================================================

    def capturar_pantalla(
        self,
        todos_monitores: bool = True,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.capturador_pantalla
            .capturar_pantalla(
                todos_monitores=(
                    todos_monitores
                )
            )
        )

        datos = {}

        if resultado.captura is not None:

            captura = (
                resultado.captura
            )

            datos["captura"] = {
                "id":
                    captura.id,

                "ruta":
                    captura.ruta,

                "ancho":
                    captura.ancho,

                "alto":
                    captura.alto,

                "creada_en":
                    captura.creada_en,

                "tipo":
                    captura.tipo,

                "ventana_titulo":
                    captura.ventana_titulo,

                "ventana_hwnd":
                    captura.ventana_hwnd,

                "metadata":
                    captura.metadata,
            }

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=datos,
            error=resultado.error,
        )

    def capturar_ventana(
        self,
        titulo: str,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.capturador_pantalla
            .capturar_ventana(
                titulo=titulo
            )
        )

        datos = {}

        if resultado.captura is not None:

            captura = (
                resultado.captura
            )

            datos["captura"] = {
                "id":
                    captura.id,

                "ruta":
                    captura.ruta,

                "ancho":
                    captura.ancho,

                "alto":
                    captura.alto,

                "creada_en":
                    captura.creada_en,

                "tipo":
                    captura.tipo,

                "ventana_titulo":
                    captura.ventana_titulo,

                "ventana_hwnd":
                    captura.ventana_hwnd,

                "metadata":
                    captura.metadata,
            }

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion=resultado.accion,
            mensaje=resultado.mensaje,
            datos=datos,
            error=resultado.error,
        )

    def listar_capturas(
        self,
        limite: int = 30,
    ) -> ResultadoAccionSistema:

        capturas = (
            self.capturador_pantalla
            .listar_capturas(
                limite=limite
            )
        )

        return ResultadoAccionSistema(
            ok=True,
            accion="listar_capturas",
            mensaje=(
                f"{len(capturas)} captura(s)."
            ),
            datos={
                "capturas":
                    capturas
            },
        )


    def construir_estado_visual(
        self,
        capturar: bool = True,
    ) -> ResultadoAccionSistema:

        resultado = (
            self.percepcion_visual
            .construir_estado(
                capturar=capturar
            )
        )

        if (
            not resultado.ok
            or resultado.estado
            is None
        ):

            return ResultadoAccionSistema(
                ok=False,
                accion="construir_estado_visual",
                error=(
                    resultado.error
                    or "estado_visual_no_disponible"
                ),
                mensaje=resultado.mensaje,
            )

        estado = resultado.estado

        return ResultadoAccionSistema(
            ok=True,
            accion="construir_estado_visual",
            mensaje=(
                self.percepcion_visual
                .resumen_para_agente(
                    estado
                )
            ),
            datos={
                "estado_visual": {
                    "creada_en":
                        estado.creada_en,

                    "captura_ok":
                        estado.captura_ok,

                    "captura_ruta":
                        estado.captura_ruta,

                    "pantalla_ancho":
                        estado.pantalla_ancho,

                    "pantalla_alto":
                        estado.pantalla_alto,

                    "ventana_activa":
                        estado.ventana_activa,

                    "ventanas_visibles":
                        estado.ventanas_visibles,

                    "mouse":
                        estado.mouse,

                    "contexto_aplicacion":
                        estado.contexto_aplicacion,

                    "metadata":
                        estado.metadata,
                }
            },
        )


    def interpretar_escena(
        self,
        usar_modelo_vision: bool = True,
    ) -> ResultadoAccionSistema:

        resultado_estado = self.percepcion_visual.construir_estado(
            capturar=True
        )

        if (
            not resultado_estado.ok
            or resultado_estado.estado is None
        ):
            return ResultadoAccionSistema(
                ok=False,
                accion="interpretar_escena",
                error=(
                    resultado_estado.error
                    or "estado_visual_no_disponible"
                ),
            )

        resultado = self.interpretador_visual.interpretar(
            estado=resultado_estado.estado,
            usar_modelo_vision=usar_modelo_vision,
        )

        if resultado.interpretacion is None:
            return ResultadoAccionSistema(
                ok=False,
                accion="interpretar_escena",
                error=(
                    resultado.error
                    or "interpretacion_no_disponible"
                ),
                mensaje=resultado.mensaje,
            )

        i = resultado.interpretacion

        return ResultadoAccionSistema(
            ok=resultado.ok,
            accion="interpretar_escena",
            mensaje=i.resumen,
            datos={
                "contexto_aplicacion": i.contexto_aplicacion,
                "confianza_global": i.confianza_global,
                "observaciones": i.observaciones,
                "riesgos": i.riesgos,
                "elementos": [
                    {
                        "tipo": e.tipo,
                        "descripcion": e.descripcion,
                        "confianza": e.confianza,
                        "x_relativo": e.x_relativo,
                        "y_relativo": e.y_relativo,
                        "ancho_relativo": e.ancho_relativo,
                        "alto_relativo": e.alto_relativo,
                        "texto": e.texto,
                        "accion_sugerida": e.accion_sugerida,
                        "metadata": e.metadata,
                    }
                    for e in i.elementos
                ],
            },
            error=resultado.error,
        )


    def estado_vision(
        self,
    ) -> ResultadoAccionSistema:

        estado = (
            self.vision_ollama
            .estado()
        )

        return ResultadoAccionSistema(
            ok=estado.disponible,
            accion="estado_vision",
            mensaje=estado.mensaje,
            datos={
                "disponible":
                    estado.disponible,

                "servidor":
                    estado.servidor,

                "modelo":
                    estado.modelo,
            },
            error=estado.error,
        )

    # =========================================================
    # DESPACHO
    # =========================================================

    def ejecutar(
        self,
        accion: AccionSistema,
    ) -> ResultadoAccionSistema:

        tipo = accion.tipo
        args = (
            accion.argumentos
            or {}
        )

        if tipo == TipoAccionSistema.LEER_TEXTO:

            return self.leer_texto(
                ruta=args["ruta"]
            )

        if tipo == TipoAccionSistema.LISTAR_DIRECTORIO:

            return self.listar_directorio(
                ruta=args["ruta"]
            )

        if tipo == TipoAccionSistema.CREAR_CARPETA:

            return self.crear_carpeta(
                ruta=args["ruta"]
            )

        if tipo == TipoAccionSistema.ESCRIBIR_TEXTO:

            return self.escribir_texto(
                ruta=args["ruta"],
                contenido=str(
                    args.get(
                        "contenido",
                        "",
                    )
                ),
                sobrescribir=bool(
                    args.get(
                        "sobrescribir",
                        False,
                    )
                ),
            )

        if tipo == TipoAccionSistema.ABRIR_RUTA:

            return self.abrir_ruta(
                ruta=args["ruta"]
            )

        if tipo == TipoAccionSistema.ABRIR_APLICACION:

            return self.abrir_aplicacion(
                alias=str(
                    args["alias"]
                ),
                argumentos=[
                    str(item)
                    for item
                    in (
                        args.get(
                            "argumentos",
                            [],
                        )
                        or []
                    )
                ],
            )

        if tipo == TipoAccionSistema.LISTAR_PROCESOS:

            return self.listar_procesos()

        if tipo == TipoAccionSistema.LISTAR_VENTANAS:

            return self.listar_ventanas()

        if tipo == TipoAccionSistema.VENTANA_ACTIVA:

            return self.ventana_activa()

        if tipo == TipoAccionSistema.ACTIVAR_VENTANA:

            return self._accion_ventana(
                metodo="activar",
                accion="activar_ventana",
                hwnd=args.get(
                    "hwnd"
                ),
                titulo=args.get(
                    "titulo"
                ),
            )

        if tipo == TipoAccionSistema.MINIMIZAR_VENTANA:

            return self._accion_ventana(
                metodo="minimizar",
                accion="minimizar_ventana",
                hwnd=args.get(
                    "hwnd"
                ),
                titulo=args.get(
                    "titulo"
                ),
            )

        if tipo == TipoAccionSistema.MAXIMIZAR_VENTANA:

            return self._accion_ventana(
                metodo="maximizar",
                accion="maximizar_ventana",
                hwnd=args.get(
                    "hwnd"
                ),
                titulo=args.get(
                    "titulo"
                ),
            )

        if tipo == TipoAccionSistema.RESTAURAR_VENTANA:

            return self._accion_ventana(
                metodo="restaurar",
                accion="restaurar_ventana",
                hwnd=args.get(
                    "hwnd"
                ),
                titulo=args.get(
                    "titulo"
                ),
            )


        if tipo == TipoAccionSistema.POSICION_MOUSE:

            return self.posicion_mouse()

        if tipo == TipoAccionSistema.MOVER_MOUSE:

            return self.mover_mouse(
                x=int(
                    args["x"]
                ),
                y=int(
                    args["y"]
                ),
                duracion=float(
                    args.get(
                        "duracion",
                        0.0,
                    )
                ),
            )

        if tipo == TipoAccionSistema.MOVER_MOUSE_VENTANA:

            return self.mover_mouse_ventana(
                titulo=str(
                    args["titulo"]
                ),
                x_relativo=float(
                    args["x_relativo"]
                ),
                y_relativo=float(
                    args["y_relativo"]
                ),
                duracion=float(
                    args.get(
                        "duracion",
                        0.15,
                    )
                ),
            )

        if tipo == TipoAccionSistema.CLICK_MOUSE:

            return self.click_mouse(
                boton=str(
                    args.get(
                        "boton",
                        "izquierdo",
                    )
                ),
                doble=bool(
                    args.get(
                        "doble",
                        False,
                    )
                ),
            )

        if tipo == TipoAccionSistema.DOBLE_CLICK_MOUSE:

            return self.click_mouse(
                boton=str(
                    args.get(
                        "boton",
                        "izquierdo",
                    )
                ),
                doble=True,
            )

        if tipo == TipoAccionSistema.CLICK_MOUSE_VENTANA:

            return self.click_mouse_ventana(
                titulo=str(
                    args["titulo"]
                ),
                x_relativo=float(
                    args["x_relativo"]
                ),
                y_relativo=float(
                    args["y_relativo"]
                ),
                boton=str(
                    args.get(
                        "boton",
                        "izquierdo",
                    )
                ),
                doble=bool(
                    args.get(
                        "doble",
                        False,
                    )
                ),
            )

        if tipo == TipoAccionSistema.SCROLL_MOUSE:

            return self.scroll_mouse(
                pasos=int(
                    args.get(
                        "pasos",
                        0,
                    )
                )
            )


        if tipo == TipoAccionSistema.ESCRIBIR_TECLADO:

            return self.escribir_teclado(
                texto=str(
                    args.get(
                        "texto",
                        "",
                    )
                ),
                intervalo=float(
                    args.get(
                        "intervalo",
                        0.0,
                    )
                ),
            )

        if tipo == TipoAccionSistema.PULSAR_TECLA:

            return self.pulsar_tecla(
                tecla=str(
                    args["tecla"]
                ),
                repeticiones=int(
                    args.get(
                        "repeticiones",
                        1,
                    )
                ),
            )

        if tipo == TipoAccionSistema.COMBINACION_TECLAS:

            return self.combinacion_teclas(
                teclas=[
                    str(item)
                    for item
                    in (
                        args.get(
                            "teclas",
                            [],
                        )
                        or []
                    )
                ]
            )

        if tipo == TipoAccionSistema.ESCRIBIR_EN_VENTANA:

            return self.escribir_en_ventana(
                titulo=str(
                    args["titulo"]
                ),
                texto=str(
                    args.get(
                        "texto",
                        "",
                    )
                ),
                intervalo=float(
                    args.get(
                        "intervalo",
                        0.0,
                    )
                ),
            )

        if tipo == TipoAccionSistema.COMBINACION_TECLAS_VENTANA:

            return self.combinacion_teclas_ventana(
                titulo=str(
                    args["titulo"]
                ),
                teclas=[
                    str(item)
                    for item
                    in (
                        args.get(
                            "teclas",
                            [],
                        )
                        or []
                    )
                ],
            )


        if tipo == TipoAccionSistema.CAPTURAR_PANTALLA:

            return self.capturar_pantalla(
                todos_monitores=bool(
                    args.get(
                        "todos_monitores",
                        True,
                    )
                )
            )

        if tipo == TipoAccionSistema.CAPTURAR_VENTANA:

            return self.capturar_ventana(
                titulo=str(
                    args["titulo"]
                )
            )

        if tipo == TipoAccionSistema.LISTAR_CAPTURAS:

            return self.listar_capturas(
                limite=int(
                    args.get(
                        "limite",
                        30,
                    )
                )
            )


        if tipo == TipoAccionSistema.CONSTRUIR_ESTADO_VISUAL:

            return self.construir_estado_visual(
                capturar=bool(
                    args.get(
                        "capturar",
                        True,
                    )
                )
            )

        if tipo == TipoAccionSistema.INTERPRETAR_ESCENA:

            return self.interpretar_escena(
                usar_modelo_vision=bool(
                    args.get("usar_modelo_vision", True)
                )
            )

        if tipo == TipoAccionSistema.ESTADO_VISION:

            return self.estado_vision()

        return ResultadoAccionSistema(
            ok=False,
            accion=str(
                tipo
            ),
            error="accion_no_soportada",
        )

    def catalogo(
        self,
    ) -> dict[str, Any]:

        return {
            "acciones": [
                item.value
                for item
                in TipoAccionSistema
            ],

            "raices_escritura": [
                str(item)
                for item
                in self.raices_escritura
            ],

            "aplicaciones":
                sorted(
                    self.aplicaciones.keys()
                ),

            "gestor_ventanas":
                self.gestor_ventanas.disponible,

            "controlador_mouse":
                self.controlador_mouse.disponible,

            "controlador_teclado":
                self.controlador_teclado.disponible,

            "capturador_pantalla":
                self.capturador_pantalla.disponible,

            "ejecutor_gui":
                True,

            "verificador_visual":
                True,
        }