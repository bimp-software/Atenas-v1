from __future__ import annotations

import os
import subprocess
import sys
import time

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ResultadoPrueba:
    ok: bool

    comando: list[str]

    returncode: int | None

    stdout: str
    stderr: str

    duracion: float

    timeout: bool = False

    error: str | None = None


class EjecutorPruebas:
    """
    Ejecuta pruebas Python de manera estructurada.

    No acepta comandos shell arbitrarios.
    """

    MAX_TIMEOUT = 300

    def __init__(
        self,
        raiz_proyecto: str | Path = ".",
    ):
        self.raiz = Path(
            raiz_proyecto
        ).resolve()

    # =========================================================
    # EJECUTAR
    # =========================================================

    def _ejecutar(
        self,
        comando: list[str],
        timeout: int = 60,
        cwd: str | Path | None = None,
    ) -> ResultadoPrueba:

        timeout = max(
            1,
            min(
                int(timeout),
                self.MAX_TIMEOUT,
            ),
        )

        directorio = (
            Path(cwd).resolve()
            if cwd is not None
            else self.raiz
        )

        inicio = time.perf_counter()

        try:

            proceso = subprocess.run(
                comando,

                cwd=str(
                    directorio
                ),

                capture_output=True,
                text=True,

                timeout=timeout,

                shell=False,

                env=os.environ.copy(),
            )

            duracion = (
                time.perf_counter()
                - inicio
            )

            return ResultadoPrueba(
                ok=(
                    proceso.returncode
                    == 0
                ),

                comando=comando,

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

            stdout = error.stdout or ""
            stderr = error.stderr or ""

            if isinstance(
                stdout,
                bytes,
            ):
                stdout = stdout.decode(
                    errors="replace"
                )

            if isinstance(
                stderr,
                bytes,
            ):
                stderr = stderr.decode(
                    errors="replace"
                )

            return ResultadoPrueba(
                ok=False,

                comando=comando,

                returncode=None,

                stdout=stdout,
                stderr=stderr,

                duracion=duracion,

                timeout=True,

                error="timeout",
            )

        except Exception as error:

            duracion = (
                time.perf_counter()
                - inicio
            )

            return ResultadoPrueba(
                ok=False,

                comando=comando,

                returncode=None,

                stdout="",
                stderr="",

                duracion=duracion,

                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    # =========================================================
    # EJECUTAR MÓDULO
    # =========================================================

    def ejecutar_modulo(
        self,
        modulo: str,
        timeout: int = 60,
        cwd: str | Path | None = None,
    ) -> ResultadoPrueba:

        modulo = (
            modulo
            or ""
        ).strip()

        if not modulo:

            raise ValueError(
                "El módulo no puede estar vacío."
            )

        # Permitimos únicamente nombres de módulo Python.
        caracteres_validos = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789_"
            "."
        )

        if any(
            caracter not in caracteres_validos
            for caracter in modulo
        ):

            raise ValueError(
                "Nombre de módulo inválido."
            )

        comando = [
            sys.executable,
            "-m",
            modulo,
        ]

        return self._ejecutar(
            comando=comando,
            timeout=timeout,
            cwd=cwd,
        )

    # =========================================================
    # EJECUTAR TEST DEL PROYECTO
    # =========================================================

    def ejecutar_test(
        self,
        modulo_test: str,
        timeout: int = 60,
        cwd: str | Path | None = None,
    ) -> ResultadoPrueba:

        if not modulo_test.startswith(
            "tests."
        ):

            raise ValueError(
                "Solo se permiten módulos "
                "dentro de tests."
            )

        return self.ejecutar_modulo(
            modulo=modulo_test,
            timeout=timeout,
            cwd=cwd,
        )

    # =========================================================
    # COMPROBAR SINTAXIS
    # =========================================================

    def comprobar_sintaxis(
        self,
        ruta: str,
        timeout: int = 30,
        cwd: str | Path | None = None,
    ) -> ResultadoPrueba:

        ruta = (
            ruta
            or ""
        ).strip()

        if not ruta:

            raise ValueError(
                "La ruta no puede estar vacía."
            )

        ruta_path = Path(
            ruta
        )

        if ruta_path.suffix.lower() != ".py":

            raise ValueError(
                "Solo se puede comprobar "
                "sintaxis de archivos Python."
            )

        comando = [
            sys.executable,
            "-m",
            "py_compile",
            ruta,
        ]

        return self._ejecutar(
            comando=comando,
            timeout=timeout,
            cwd=cwd,
        )

    # =========================================================
    # PYTEST
    # =========================================================

    def ejecutar_pytest(
        self,
        objetivo: str | None = None,
        timeout: int = 120,
        cwd: str | Path | None = None,
    ) -> ResultadoPrueba:

        comando = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ]

        if objetivo:

            # No permitimos argumentos arbitrarios.
            # Solo ruta/nodo pytest sencillo.
            if any(
                peligroso in objetivo
                for peligroso in (
                    ";",
                    "&",
                    "|",
                    ">",
                    "<",
                    "`",
                    "$(",
                )
            ):

                raise ValueError(
                    "Objetivo pytest inválido."
                )

            comando.append(
                objetivo
            )

        return self._ejecutar(
            comando=comando,
            timeout=timeout,
            cwd=cwd,
        )