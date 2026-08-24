from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class TipoAccionSistema(str, Enum):
    LEER_TEXTO = "leer_texto"
    LISTAR_DIRECTORIO = "listar_directorio"
    CREAR_CARPETA = "crear_carpeta"
    ESCRIBIR_TEXTO = "escribir_texto"

    ABRIR_RUTA = "abrir_ruta"
    ABRIR_APLICACION = "abrir_aplicacion"

    LISTAR_PROCESOS = "listar_procesos"


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
    Capa estructurada para interactuar con el computador.

    Principios:
    - NO recibe comandos shell arbitrarios.
    - NO usa shell=True.
    - Las escrituras se restringen a raíces autorizadas.
    - Las aplicaciones se abren mediante alias registrados.
    - No implementa borrado ni sobrescrituras peligrosas por defecto.
    - Toda acción devuelve un resultado estructurado.

    Esta capa será utilizada posteriormente por el Agente y por el
    controlador de escritorio/mouse/teclado.
    """

    def __init__(
        self,
        raices_escritura: list[str | Path] | None = None,
        aplicaciones: dict[str, list[str]] | None = None,
    ):

        if raices_escritura is None:

            home = Path.home()

            candidatos = [
                home / "Desktop",
                home / "Documents",
            ]

            self.raices_escritura = [
                ruta.resolve()
                for ruta in candidatos
                if ruta.exists()
            ]

        else:

            self.raices_escritura = [
                Path(
                    ruta
                ).expanduser().resolve()
                for ruta in raices_escritura
            ]

        self.aplicaciones = (
            aplicaciones
            or self._aplicaciones_por_defecto()
        )

    # =========================================================
    # APLICACIONES CONOCIDAS
    # =========================================================

    @staticmethod
    def _aplicaciones_por_defecto(
        self=None,
    ) -> dict[str, list[str]]:

        sistema = platform.system().lower()

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
            }

        return {
            "archivos": [
                "xdg-open",
                ".",
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
            for item in comando
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

        for raiz in self.raices_escritura:

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

            permitidas = [
                str(item)
                for item in self.raices_escritura
            ]

            raise PermissionError(
                (
                    "Ruta fuera de las raíces de escritura "
                    f"autorizadas: {ruta}. "
                    f"Permitidas: {permitidas}"
                )
            )

    # =========================================================
    # LECTURA
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
                mensaje=(
                    f"No existe: {archivo}"
                ),
            )

        if not archivo.is_file():

            return ResultadoAccionSistema(
                ok=False,
                accion="leer_texto",
                error="ruta_no_es_archivo",
            )

        tamaño = archivo.stat().st_size

        if tamaño > max_bytes:

            return ResultadoAccionSistema(
                ok=False,
                accion="leer_texto",
                error="archivo_demasiado_grande",
                mensaje=(
                    f"El archivo tiene {tamaño} bytes."
                ),
            )

        try:

            contenido = archivo.read_text(
                encoding="utf-8"
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
            int(limite),
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

    # =========================================================
    # ESCRITURA
    # =========================================================

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
                mensaje=(
                    "Carpeta disponible."
                ),
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
                    mensaje=(
                        "No se sobrescribió el archivo."
                    ),
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
    # ABRIR RUTAS / APLICACIONES
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

            sistema = platform.system().lower()

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

        comando = self.aplicaciones.get(
            clave
        )

        if comando is None:

            return ResultadoAccionSistema(
                ok=False,
                accion="abrir_aplicacion",
                error="aplicacion_no_registrada",
                mensaje=(
                    f"Alias no registrado: {clave}"
                ),
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
                for item in argumentos
            )

        ejecutable = comando_final[0]

        if (
            platform.system().lower()
            != "windows"
            and shutil.which(
                ejecutable
            )
            is None
        ):

            return ResultadoAccionSistema(
                ok=False,
                accion="abrir_aplicacion",
                error="ejecutable_no_disponible",
                mensaje=ejecutable,
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

                    "comando":
                        comando_final,
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

        sistema = platform.system().lower()

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
                        mensaje=(
                            proceso.stderr
                            or ""
                        ),
                    )

                import csv
                import io

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

                    if len(procesos) >= limite:
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

                if proceso.returncode != 0:

                    return ResultadoAccionSistema(
                        ok=False,
                        accion="listar_procesos",
                        error="ps_fallo",
                    )

                procesos = []

                for linea in (
                    proceso.stdout
                    or ""
                ).splitlines():

                    partes = linea.strip().split(
                        None,
                        1,
                    )

                    if len(partes) != 2:
                        continue

                    procesos.append({
                        "pid":
                            partes[0],

                        "nombre":
                            partes[1],
                    })

                    if len(procesos) >= limite:
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
    # DESPACHO ESTRUCTURADO
    # =========================================================

    def ejecutar(
        self,
        accion: AccionSistema,
    ) -> ResultadoAccionSistema:

        tipo = accion.tipo
        args = accion.argumentos or {}

        if tipo == TipoAccionSistema.LEER_TEXTO:

            return self.leer_texto(
                ruta=args["ruta"],
                max_bytes=int(
                    args.get(
                        "max_bytes",
                        2_000_000,
                    )
                ),
            )

        if tipo == TipoAccionSistema.LISTAR_DIRECTORIO:

            return self.listar_directorio(
                ruta=args["ruta"],
                limite=int(
                    args.get(
                        "limite",
                        200,
                    )
                ),
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
                    args[
                        "alias"
                    ]
                ),
                argumentos=[
                    str(item)
                    for item in (
                        args.get(
                            "argumentos",
                            [],
                        )
                        or []
                    )
                ],
            )

        if tipo == TipoAccionSistema.LISTAR_PROCESOS:

            return self.listar_procesos(
                limite=int(
                    args.get(
                        "limite",
                        300,
                    )
                )
            )

        return ResultadoAccionSistema(
            ok=False,
            accion=str(
                tipo
            ),
            error="accion_no_soportada",
        )

    # =========================================================
    # CATÁLOGO PARA AGENTE/UI
    # =========================================================

    def catalogo(
        self,
    ) -> dict[str, Any]:

        return {
            "acciones": [
                item.value
                for item in TipoAccionSistema
            ],

            "raices_escritura": [
                str(item)
                for item in (
                    self.raices_escritura
                )
            ],

            "aplicaciones": sorted(
                self.aplicaciones.keys()
            ),
        }