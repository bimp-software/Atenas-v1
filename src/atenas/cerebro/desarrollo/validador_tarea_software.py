from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import time

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ResultadoComandoValidacion:
    comando: list[str]
    ok: bool
    returncode: int
    stdout: str = ""
    stderr: str = ""
    duracion: float = 0.0


@dataclass
class ResultadoValidacionTarea:
    ok: bool

    sintaxis_ok: bool
    pruebas_ok: bool

    archivos_python: int = 0
    archivos_json: int = 0

    errores: list[str] = field(
        default_factory=list
    )

    comandos: list[
        ResultadoComandoValidacion
    ] = field(
        default_factory=list
    )

    resumen: str = ""


class ValidadorTareaSoftware:
    """
    Valida una tarea ya programada dentro de un proyecto.

    Esta versión corrige dos problemas frecuentes en proyectos
    generados dentro de otro repositorio:

    1. pytest puede resolver el paquete "src" del repositorio
       padre en vez del "src" del proyecto generado.
    2. plugins globales de pytest pueden alterar una prueba que
       debería ser aislada.

    Por eso:
    - añade explícitamente la raíz del proyecto a PYTHONPATH;
    - ejecuta pytest dentro de la carpeta del proyecto;
    - deshabilita autoload de plugins externos;
    - limita pytest a la carpeta tests/;
    - conserva stdout/stderr completos para diagnóstico.
    """

    def __init__(
        self,
        timeout_segundos: int = 60,
    ):
        self.timeout_segundos = max(
            5,
            int(
                timeout_segundos
            ),
        )

    # =========================================================
    # RUTAS
    # =========================================================

    @staticmethod
    def _ruta_segura(
        raiz: Path,
        ruta: Path,
    ) -> bool:

        try:

            ruta.resolve().relative_to(
                raiz.resolve()
            )

            return True

        except ValueError:

            return False

    # =========================================================
    # VALIDACIÓN ESTÁTICA
    # =========================================================

    def _validar_python(
        self,
        raiz: Path,
    ) -> tuple[
        int,
        list[str],
    ]:

        errores = []
        cantidad = 0

        for archivo in raiz.rglob(
            "*.py"
        ):

            if not self._ruta_segura(
                raiz,
                archivo,
            ):
                continue

            cantidad += 1

            try:

                contenido = (
                    archivo.read_text(
                        encoding="utf-8"
                    )
                )

                ast.parse(
                    contenido,
                    filename=str(
                        archivo
                    ),
                )

            except Exception as error:

                errores.append(
                    (
                        f"{archivo}: "
                        f"{type(error).__name__}: "
                        f"{error}"
                    )
                )

        return (
            cantidad,
            errores,
        )

    def _validar_json(
        self,
        raiz: Path,
    ) -> tuple[
        int,
        list[str],
    ]:

        errores = []
        cantidad = 0

        for archivo in raiz.rglob(
            "*.json"
        ):

            if not self._ruta_segura(
                raiz,
                archivo,
            ):
                continue

            cantidad += 1

            try:

                json.loads(
                    archivo.read_text(
                        encoding="utf-8"
                    )
                )

            except Exception as error:

                errores.append(
                    (
                        f"{archivo}: "
                        f"{type(error).__name__}: "
                        f"{error}"
                    )
                )

        return (
            cantidad,
            errores,
        )

    # =========================================================
    # PREPARAR PROYECTO PYTHON
    # =========================================================

    @staticmethod
    def _preparar_paquetes_python(
        raiz: Path,
    ) -> None:
        """
        Hace importable un proyecto generado con layout:

            proyecto/
                src/
                    modulo.py
                tests/
                    test_modulo.py

        No reemplaza archivos existentes.
        """

        src = (
            raiz
            / "src"
        )

        tests = (
            raiz
            / "tests"
        )

        if src.exists():

            init_src = (
                src
                / "__init__.py"
            )

            if not init_src.exists():

                init_src.write_text(
                    "",
                    encoding="utf-8",
                )

        if tests.exists():

            init_tests = (
                tests
                / "__init__.py"
            )

            if not init_tests.exists():

                init_tests.write_text(
                    "",
                    encoding="utf-8",
                )

    # =========================================================
    # PRUEBAS PYTHON
    # =========================================================

    @staticmethod
    def _hay_tests_python(
        raiz: Path,
    ) -> bool:

        tests = (
            raiz
            / "tests"
        )

        if not tests.exists():

            return False

        return any(
            tests.rglob(
                "test_*.py"
            )
        )

    @staticmethod
    def _entorno_pytest(
        raiz: Path,
    ) -> dict[str, str]:

        entorno = (
            os.environ.copy()
        )

        raiz_str = str(
            raiz.resolve()
        )

        pythonpath_actual = (
            entorno.get(
                "PYTHONPATH",
                "",
            )
        )

        if pythonpath_actual:

            entorno[
                "PYTHONPATH"
            ] = (
                raiz_str
                + os.pathsep
                + pythonpath_actual
            )

        else:

            entorno[
                "PYTHONPATH"
            ] = raiz_str

        # Evita que plugins instalados globalmente alteren
        # las pruebas de un proyecto generado.
        entorno[
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD"
        ] = "1"

        # Mejor salida UTF-8 en Windows.
        entorno[
            "PYTHONUTF8"
        ] = "1"

        return entorno

    def _ejecutar_pytest(
        self,
        raiz: Path,
    ) -> ResultadoComandoValidacion:

        tests = (
            raiz
            / "tests"
        )

        comando = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(
                tests
            ),
        ]

        inicio = (
            time.perf_counter()
        )

        try:

            proceso = subprocess.run(
                comando,
                cwd=str(
                    raiz
                ),
                env=(
                    self._entorno_pytest(
                        raiz
                    )
                ),
                capture_output=True,
                text=True,
                timeout=(
                    self.timeout_segundos
                ),
                shell=False,
            )

            duracion = (
                time.perf_counter()
                - inicio
            )

            return ResultadoComandoValidacion(
                comando=comando,
                ok=(
                    proceso.returncode
                    == 0
                ),
                returncode=(
                    proceso.returncode
                ),
                stdout=(
                    proceso.stdout
                    or ""
                ),
                stderr=(
                    proceso.stderr
                    or ""
                ),
                duracion=duracion,
            )

        except subprocess.TimeoutExpired as error:

            duracion = (
                time.perf_counter()
                - inicio
            )

            stdout = (
                error.stdout
                if isinstance(
                    error.stdout,
                    str,
                )
                else ""
            )

            stderr = (
                error.stderr
                if isinstance(
                    error.stderr,
                    str,
                )
                else ""
            )

            return ResultadoComandoValidacion(
                comando=comando,
                ok=False,
                returncode=-1,
                stdout=stdout,
                stderr=(
                    stderr
                    + "\nTimeout ejecutando pruebas."
                ).strip(),
                duracion=duracion,
            )

        except Exception as error:

            duracion = (
                time.perf_counter()
                - inicio
            )

            return ResultadoComandoValidacion(
                comando=comando,
                ok=False,
                returncode=-1,
                stderr=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
                duracion=duracion,
            )

    # =========================================================
    # VALIDACIÓN GENERAL
    # =========================================================

    def validar(
        self,
        carpeta_proyecto: str | Path,
        ejecutar_pruebas: bool = True,
    ) -> ResultadoValidacionTarea:

        raiz = Path(
            carpeta_proyecto
        ).resolve()

        if not raiz.exists():

            return ResultadoValidacionTarea(
                ok=False,
                sintaxis_ok=False,
                pruebas_ok=False,
                errores=[
                    "La carpeta del proyecto no existe."
                ],
                resumen=(
                    "No fue posible validar "
                    "el proyecto."
                ),
            )

        self._preparar_paquetes_python(
            raiz
        )

        py_count, py_errors = (
            self._validar_python(
                raiz
            )
        )

        json_count, json_errors = (
            self._validar_json(
                raiz
            )
        )

        errores = (
            py_errors
            + json_errors
        )

        sintaxis_ok = (
            not errores
        )

        comandos = []

        pruebas_ok = True

        if (
            ejecutar_pruebas
            and sintaxis_ok
            and self._hay_tests_python(
                raiz
            )
        ):

            resultado_pytest = (
                self._ejecutar_pytest(
                    raiz
                )
            )

            comandos.append(
                resultado_pytest
            )

            pruebas_ok = (
                resultado_pytest.ok
            )

            if not pruebas_ok:

                if resultado_pytest.stdout:

                    errores.append(
                        resultado_pytest.stdout
                    )

                if resultado_pytest.stderr:

                    errores.append(
                        resultado_pytest.stderr
                    )

        ok = bool(
            sintaxis_ok
            and pruebas_ok
        )

        if ok:

            resumen = (
                "Validación correcta: "
                "sintaxis y pruebas superadas."
            )

        elif not sintaxis_ok:

            resumen = (
                "La validación falló por "
                "errores de sintaxis o estructura."
            )

        else:

            resumen = (
                "La sintaxis es correcta, "
                "pero las pruebas fallaron."
            )

        return ResultadoValidacionTarea(
            ok=ok,
            sintaxis_ok=sintaxis_ok,
            pruebas_ok=pruebas_ok,
            archivos_python=py_count,
            archivos_json=json_count,
            errores=errores,
            comandos=comandos,
            resumen=resumen,
        )