from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class TipoEntorno(str, Enum):
    PYTHON = "python"
    NODE = "node"
    JAVA = "java"
    DOTNET = "dotnet"
    RUST = "rust"
    GO = "go"
    CPP = "cpp"
    ARDUINO = "arduino"
    DESCONOCIDO = "desconocido"


@dataclass
class RuntimeDetectado:
    tipo: TipoEntorno
    disponible: bool
    ejecutable: str | None = None
    version: str | None = None
    gestor_paquetes: str | None = None
    gestor_disponible: bool = False


@dataclass
class DependenciaProyecto:
    nombre: str
    version: str | None = None
    origen: str = "inferida"
    instalada: bool | None = None


@dataclass
class PlanEntornoProyecto:
    tipo: TipoEntorno
    carpeta_proyecto: str
    runtime: RuntimeDetectado

    archivo_dependencias: str | None = None
    dependencias: list[DependenciaProyecto] = field(default_factory=list)

    entorno_virtual: str | None = None
    entorno_preparado: bool = False

    comandos_sugeridos: list[list[str]] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)

    manifiesto: str | None = None


@dataclass
class ResultadoPreparacionEntorno:
    ok: bool
    plan: PlanEntornoProyecto | None = None
    acciones: list[str] = field(default_factory=list)
    error: str | None = None


class GestorEntornosProyecto:
    """
    Detecta y prepara entornos de desarrollo por proyecto.

    Esta versión puede:
    - detectar el tipo de proyecto;
    - detectar runtimes instalados;
    - leer requirements.txt, pyproject.toml y package.json;
    - crear .venv de Python sin acceder a Internet;
    - generar un manifiesto reproducible;
    - detectar dependencias faltantes;
    - preparar comandos sugeridos de instalación.

    IMPORTANTE:
    No instala dependencias externas automáticamente.
    La instalación se hará después mediante una capa separada de
    ejecución autorizada y controlada.

    Así ATENAS puede planificar y preparar el entorno sin ejecutar
    paquetes arbitrarios provenientes del LLM.
    """

    def __init__(
        self,
        timeout_segundos: int = 30,
    ):
        self.timeout_segundos = max(
            5,
            int(timeout_segundos),
        )

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _which(
        nombre: str,
    ) -> str | None:

        return shutil.which(nombre)

    @staticmethod
    def _version_comando(
        comando: list[str],
        timeout: int = 10,
    ) -> str | None:

        try:

            proceso = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )

            salida = (
                (proceso.stdout or "")
                + "\n"
                + (proceso.stderr or "")
            ).strip()

            if not salida:
                return None

            return salida.splitlines()[0].strip()

        except Exception:
            return None

    # =========================================================
    # DETECTAR TIPO
    # =========================================================

    @staticmethod
    def detectar_tipo(
        carpeta_proyecto: str | Path,
    ) -> TipoEntorno:

        raiz = Path(
            carpeta_proyecto
        ).resolve()

        if (
            (raiz / "pyproject.toml").exists()
            or (raiz / "requirements.txt").exists()
            or any(raiz.rglob("*.py"))
        ):
            return TipoEntorno.PYTHON

        if (
            (raiz / "package.json").exists()
            or any(raiz.rglob("*.ts"))
            or any(raiz.rglob("*.js"))
        ):
            return TipoEntorno.NODE

        if (
            (raiz / "Cargo.toml").exists()
            or any(raiz.rglob("*.rs"))
        ):
            return TipoEntorno.RUST

        if (
            (raiz / "go.mod").exists()
            or any(raiz.rglob("*.go"))
        ):
            return TipoEntorno.GO

        if (
            any(raiz.rglob("*.csproj"))
            or any(raiz.rglob("*.cs"))
        ):
            return TipoEntorno.DOTNET

        if (
            (raiz / "pom.xml").exists()
            or (raiz / "build.gradle").exists()
            or any(raiz.rglob("*.java"))
        ):
            return TipoEntorno.JAVA

        if any(
            raiz.rglob("*.ino")
        ):
            return TipoEntorno.ARDUINO

        if (
            (raiz / "CMakeLists.txt").exists()
            or any(raiz.rglob("*.cpp"))
            or any(raiz.rglob("*.c"))
        ):
            return TipoEntorno.CPP

        return TipoEntorno.DESCONOCIDO

    # =========================================================
    # DETECTAR RUNTIMES
    # =========================================================

    def detectar_runtime(
        self,
        tipo: TipoEntorno,
    ) -> RuntimeDetectado:

        if tipo == TipoEntorno.PYTHON:

            ejecutable = sys.executable

            return RuntimeDetectado(
                tipo=tipo,
                disponible=True,
                ejecutable=ejecutable,
                version=self._version_comando(
                    [
                        ejecutable,
                        "--version",
                    ]
                ),
                gestor_paquetes="pip",
                gestor_disponible=(
                    subprocess.run(
                        [
                            ejecutable,
                            "-m",
                            "pip",
                            "--version",
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        shell=False,
                    ).returncode
                    == 0
                ),
            )

        mapa = {
            TipoEntorno.NODE: (
                "node",
                ["node", "--version"],
                "npm",
            ),
            TipoEntorno.JAVA: (
                "java",
                ["java", "-version"],
                "maven/gradle",
            ),
            TipoEntorno.DOTNET: (
                "dotnet",
                ["dotnet", "--version"],
                "dotnet",
            ),
            TipoEntorno.RUST: (
                "rustc",
                ["rustc", "--version"],
                "cargo",
            ),
            TipoEntorno.GO: (
                "go",
                ["go", "version"],
                "go",
            ),
            TipoEntorno.CPP: (
                "cmake",
                ["cmake", "--version"],
                "cmake",
            ),
            TipoEntorno.ARDUINO: (
                "arduino-cli",
                ["arduino-cli", "version"],
                "arduino-cli",
            ),
        }

        if tipo not in mapa:

            return RuntimeDetectado(
                tipo=tipo,
                disponible=False,
            )

        nombre, comando_version, gestor = mapa[
            tipo
        ]

        ejecutable = self._which(
            nombre
        )

        gestor_ejecutable = self._which(
            gestor.split("/")[0]
        )

        return RuntimeDetectado(
            tipo=tipo,
            disponible=bool(
                ejecutable
            ),
            ejecutable=ejecutable,
            version=(
                self._version_comando(
                    comando_version
                )
                if ejecutable
                else None
            ),
            gestor_paquetes=gestor,
            gestor_disponible=bool(
                gestor_ejecutable
            ),
        )

    # =========================================================
    # DEPENDENCIAS PYTHON
    # =========================================================

    @staticmethod
    def _parse_requirement(
        linea: str,
    ) -> DependenciaProyecto | None:

        linea = (
            linea
            .strip()
        )

        if (
            not linea
            or linea.startswith("#")
            or linea.startswith("-")
        ):
            return None

        separadores = [
            "==",
            ">=",
            "<=",
            "~=",
            "!=",
            ">",
            "<",
        ]

        for separador in separadores:

            if separador in linea:

                nombre, version = (
                    linea.split(
                        separador,
                        1,
                    )
                )

                return DependenciaProyecto(
                    nombre=nombre.strip(),
                    version=(
                        separador
                        + version.strip()
                    ),
                    origen="requirements.txt",
                )

        return DependenciaProyecto(
            nombre=linea,
            origen="requirements.txt",
        )

    def _leer_requirements(
        self,
        raiz: Path,
    ) -> tuple[
        str | None,
        list[DependenciaProyecto],
    ]:

        archivo = (
            raiz
            / "requirements.txt"
        )

        if not archivo.exists():

            return (
                None,
                [],
            )

        dependencias = []

        for linea in archivo.read_text(
            encoding="utf-8"
        ).splitlines():

            dep = self._parse_requirement(
                linea
            )

            if dep is not None:
                dependencias.append(
                    dep
                )

        return (
            str(archivo),
            dependencias,
        )

    @staticmethod
    def _modulo_importable(
        python_exe: str,
        nombre: str,
    ) -> bool:

        modulo = (
            nombre
            .replace("-", "_")
            .strip()
        )

        # Algunos nombres de paquete no coinciden exactamente
        # con el nombre importable. Este mapa puede crecer.
        alias = {
            "beautifulsoup4": "bs4",
            "pillow": "PIL",
            "pyyaml": "yaml",
            "scikit-learn": "sklearn",
            "python-dotenv": "dotenv",
        }

        modulo = alias.get(
            modulo.lower(),
            modulo,
        )

        codigo = (
            "import importlib.util,sys;"
            f"sys.exit(0 if importlib.util.find_spec({modulo!r}) else 1)"
        )

        try:

            return (
                subprocess.run(
                    [
                        python_exe,
                        "-c",
                        codigo,
                    ],
                    capture_output=True,
                    timeout=10,
                    shell=False,
                ).returncode
                == 0
            )

        except Exception:
            return False

    # =========================================================
    # NODE
    # =========================================================

    @staticmethod
    def _leer_package_json(
        raiz: Path,
    ) -> tuple[
        str | None,
        list[DependenciaProyecto],
    ]:

        archivo = (
            raiz
            / "package.json"
        )

        if not archivo.exists():

            return (
                None,
                [],
            )

        try:

            datos = json.loads(
                archivo.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:

            return (
                str(archivo),
                [],
            )

        resultado = []

        for seccion in (
            "dependencies",
            "devDependencies",
        ):

            valores = (
                datos.get(
                    seccion,
                    {},
                )
                or {}
            )

            if not isinstance(
                valores,
                dict,
            ):
                continue

            for nombre, version in (
                valores.items()
            ):

                resultado.append(
                    DependenciaProyecto(
                        nombre=str(
                            nombre
                        ),
                        version=str(
                            version
                        ),
                        origen=(
                            f"package.json:{seccion}"
                        ),
                        instalada=(
                            (
                                raiz
                                / "node_modules"
                                / str(nombre)
                            ).exists()
                        ),
                    )
                )

        return (
            str(archivo),
            resultado,
        )

    # =========================================================
    # PREPARAR PYTHON
    # =========================================================

    def _crear_venv(
        self,
        raiz: Path,
    ) -> tuple[
        bool,
        str | None,
        list[str],
    ]:

        venv = (
            raiz
            / ".venv"
        )

        acciones = []

        if venv.exists():

            acciones.append(
                "El entorno virtual .venv ya existe."
            )

            return (
                True,
                str(venv),
                acciones,
            )

        try:

            proceso = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "venv",
                    str(venv),
                ],
                cwd=str(raiz),
                capture_output=True,
                text=True,
                timeout=max(
                    self.timeout_segundos,
                    60,
                ),
                shell=False,
            )

            if proceso.returncode != 0:

                return (
                    False,
                    None,
                    [
                        (
                            "No se pudo crear .venv: "
                            + (
                                proceso.stderr
                                or proceso.stdout
                                or "error desconocido"
                            )
                        )
                    ],
                )

            acciones.append(
                "ATENAS creó .venv para aislar el proyecto."
            )

            return (
                True,
                str(venv),
                acciones,
            )

        except Exception as error:

            return (
                False,
                None,
                [
                    (
                        f"{type(error).__name__}: "
                        f"{error}"
                    )
                ],
            )

    @staticmethod
    def _python_venv(
        venv: Path,
    ) -> Path:

        if os.name == "nt":

            return (
                venv
                / "Scripts"
                / "python.exe"
            )

        return (
            venv
            / "bin"
            / "python"
        )

    # =========================================================
    # MANIFIESTO
    # =========================================================

    @staticmethod
    def _guardar_manifiesto(
        raiz: Path,
        plan: PlanEntornoProyecto,
    ) -> str:

        carpeta_atenas = (
            raiz
            / ".atenas"
        )

        carpeta_atenas.mkdir(
            parents=True,
            exist_ok=True,
        )

        archivo = (
            carpeta_atenas
            / "entorno.json"
        )

        archivo.write_text(
            json.dumps(
                asdict(
                    plan
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        return str(
            archivo
        )

    # =========================================================
    # PLANIFICAR / PREPARAR
    # =========================================================

    def preparar(
        self,
        carpeta_proyecto: str | Path,
        crear_venv_python: bool = True,
    ) -> ResultadoPreparacionEntorno:

        raiz = Path(
            carpeta_proyecto
        ).resolve()

        if not raiz.exists():

            return ResultadoPreparacionEntorno(
                ok=False,
                error=(
                    "La carpeta del proyecto "
                    "no existe."
                ),
            )

        tipo = self.detectar_tipo(
            raiz
        )

        runtime = self.detectar_runtime(
            tipo
        )

        dependencias = []
        archivo_dependencias = None
        entorno_virtual = None
        entorno_preparado = False
        acciones = []
        advertencias = []
        comandos = []

        # =====================================================
        # PYTHON
        # =====================================================

        if tipo == TipoEntorno.PYTHON:

            (
                archivo_dependencias,
                dependencias,
            ) = self._leer_requirements(
                raiz
            )

            if crear_venv_python:

                (
                    venv_ok,
                    venv_ruta,
                    acciones_venv,
                ) = self._crear_venv(
                    raiz
                )

                acciones.extend(
                    acciones_venv
                )

                entorno_virtual = (
                    venv_ruta
                )

                entorno_preparado = (
                    venv_ok
                )

                if (
                    venv_ok
                    and venv_ruta
                ):

                    python_venv = (
                        self._python_venv(
                            Path(
                                venv_ruta
                            )
                        )
                    )

                    for dep in dependencias:

                        dep.instalada = (
                            self._modulo_importable(
                                str(
                                    python_venv
                                ),
                                dep.nombre,
                            )
                        )

                    faltantes = [
                        dep
                        for dep
                        in dependencias
                        if dep.instalada is False
                    ]

                    if (
                        faltantes
                        and archivo_dependencias
                    ):

                        comandos.append(
                            [
                                str(
                                    python_venv
                                ),
                                "-m",
                                "pip",
                                "install",
                                "-r",
                                archivo_dependencias,
                            ]
                        )

                        advertencias.append(
                            (
                                f"Hay {len(faltantes)} "
                                "dependencia(s) no instaladas. "
                                "ATENAS solo preparó el comando; "
                                "no accedió a Internet ni instaló "
                                "paquetes automáticamente."
                            )
                        )

            else:

                entorno_preparado = bool(
                    runtime.disponible
                )

        # =====================================================
        # NODE
        # =====================================================

        elif tipo == TipoEntorno.NODE:

            (
                archivo_dependencias,
                dependencias,
            ) = self._leer_package_json(
                raiz
            )

            entorno_preparado = bool(
                runtime.disponible
            )

            if (
                archivo_dependencias
                and any(
                    dep.instalada is False
                    for dep in dependencias
                )
            ):

                if runtime.gestor_disponible:

                    comandos.append(
                        [
                            "npm",
                            "install",
                        ]
                    )

                    advertencias.append(
                        (
                            "Hay dependencias Node faltantes. "
                            "El comando npm install fue "
                            "preparado pero no ejecutado."
                        )
                    )

        else:

            entorno_preparado = bool(
                runtime.disponible
            )

            if not runtime.disponible:

                advertencias.append(
                    (
                        f"No se encontró el runtime "
                        f"para {tipo.value}."
                    )
                )

        plan = PlanEntornoProyecto(
            tipo=tipo,
            carpeta_proyecto=str(
                raiz
            ),
            runtime=runtime,
            archivo_dependencias=(
                archivo_dependencias
            ),
            dependencias=dependencias,
            entorno_virtual=(
                entorno_virtual
            ),
            entorno_preparado=(
                entorno_preparado
            ),
            comandos_sugeridos=(
                comandos
            ),
            advertencias=(
                advertencias
            ),
        )

        manifiesto = (
            self._guardar_manifiesto(
                raiz,
                plan,
            )
        )

        plan.manifiesto = (
            manifiesto
        )

        # Reescribir para incluir su propia ruta.
        Path(
            manifiesto
        ).write_text(
            json.dumps(
                asdict(
                    plan
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        return ResultadoPreparacionEntorno(
            ok=True,
            plan=plan,
            acciones=acciones,
        )