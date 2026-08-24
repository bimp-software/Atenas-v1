from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

from .gestor_entornos_proyecto import (
    DependenciaProyecto,
    PlanEntornoProyecto,
    TipoEntorno,
)


class RiesgoDependencia(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"
    BLOQUEADO = "bloqueado"


@dataclass
class EvaluacionDependencia:
    nombre: str
    version: str | None

    permitida: bool
    riesgo: RiesgoDependencia

    requiere_confirmacion: bool

    motivo: str

    comando: list[str] = field(
        default_factory=list
    )


@dataclass
class ResultadoInstalacionDependencia:
    ok: bool

    nombre: str

    instalada: bool = False

    returncode: int | None = None

    stdout: str = ""
    stderr: str = ""

    snapshot: str | None = None
    manifiesto: str | None = None

    error: str | None = None


class GestorSeguroDependencias:
    """
    Instala dependencias SOLO dentro del entorno aislado del proyecto.

    Reglas:
    - no usa shell=True;
    - no instala en el Python global;
    - no ejecuta comandos arbitrarios del LLM;
    - construye el comando a partir de datos estructurados;
    - mantiene snapshot del estado anterior;
    - registra historial;
    - puede bloquear paquetes expresamente prohibidos;
    - las dependencias de riesgo medio/alto requieren confirmación.

    Esta primera versión implementa instalación real para Python.
    Node queda preparado para la siguiente etapa.
    """

    PAQUETES_BLOQUEADOS = {
        # Mantén aquí nombres que quieras prohibir explícitamente.
        # Ejemplo:
        # "paquete-peligroso",
    }

    def __init__(
        self,
        timeout_segundos: int = 180,
    ):
        self.timeout_segundos = max(
            30,
            int(timeout_segundos),
        )

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _normalizar_nombre(
        nombre: str,
    ) -> str:

        return (
            nombre
            .strip()
            .lower()
            .replace("_", "-")
        )

    @staticmethod
    def _python_venv(
        venv: str | Path,
    ) -> Path:

        venv = Path(
            venv
        )

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

    @staticmethod
    def _hash_archivo(
        ruta: Path,
    ) -> str | None:

        if not ruta.exists():
            return None

        return hashlib.sha256(
            ruta.read_bytes()
        ).hexdigest()

    # =========================================================
    # SNAPSHOT
    # =========================================================

    def _snapshot_python(
        self,
        carpeta_proyecto: Path,
        python_exe: Path,
    ) -> Path:

        carpeta = (
            carpeta_proyecto
            / ".atenas"
            / "snapshots_dependencias"
        )

        carpeta.mkdir(
            parents=True,
            exist_ok=True,
        )

        marca = str(
            int(
                time.time()
            )
        )

        destino = (
            carpeta
            / f"python_{marca}.json"
        )

        proceso = subprocess.run(
            [
                str(
                    python_exe
                ),
                "-m",
                "pip",
                "freeze",
            ],
            cwd=str(
                carpeta_proyecto
            ),
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )

        datos = {
            "timestamp":
                marca,

            "returncode":
                proceso.returncode,

            "freeze":
                (
                    proceso.stdout
                    or ""
                ).splitlines(),

            "requirements_hash":
                self._hash_archivo(
                    carpeta_proyecto
                    / "requirements.txt"
                ),
        }

        destino.write_text(
            json.dumps(
                datos,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return destino

    # =========================================================
    # EVALUAR
    # =========================================================

    def evaluar(
        self,
        plan: PlanEntornoProyecto,
        dependencia: DependenciaProyecto,
    ) -> EvaluacionDependencia:

        nombre = self._normalizar_nombre(
            dependencia.nombre
        )

        if nombre in self.PAQUETES_BLOQUEADOS:

            return EvaluacionDependencia(
                nombre=dependencia.nombre,
                version=dependencia.version,
                permitida=False,
                riesgo=RiesgoDependencia.BLOQUEADO,
                requiere_confirmacion=True,
                motivo=(
                    "La dependencia está expresamente "
                    "bloqueada por la política local."
                ),
            )

        if plan.tipo != TipoEntorno.PYTHON:

            return EvaluacionDependencia(
                nombre=dependencia.nombre,
                version=dependencia.version,
                permitida=False,
                riesgo=RiesgoDependencia.MEDIO,
                requiere_confirmacion=True,
                motivo=(
                    "Esta versión del gestor solo instala "
                    "dependencias Python automáticamente."
                ),
            )

        if not plan.entorno_virtual:

            return EvaluacionDependencia(
                nombre=dependencia.nombre,
                version=dependencia.version,
                permitida=False,
                riesgo=RiesgoDependencia.ALTO,
                requiere_confirmacion=True,
                motivo=(
                    "No existe un entorno virtual aislado."
                ),
            )

        python_exe = self._python_venv(
            plan.entorno_virtual
        )

        if not python_exe.exists():

            return EvaluacionDependencia(
                nombre=dependencia.nombre,
                version=dependencia.version,
                permitida=False,
                riesgo=RiesgoDependencia.ALTO,
                requiere_confirmacion=True,
                motivo=(
                    "El ejecutable Python del .venv no existe."
                ),
            )

        especificacion = (
            dependencia.nombre
            + (
                dependencia.version
                or ""
            )
        )

        # En esta etapa, cualquier instalación desde Internet
        # requiere confirmación explícita.
        return EvaluacionDependencia(
            nombre=dependencia.nombre,
            version=dependencia.version,
            permitida=True,
            riesgo=RiesgoDependencia.MEDIO,
            requiere_confirmacion=True,
            motivo=(
                "La instalación está aislada en .venv, "
                "pero puede descargar y ejecutar código "
                "de terceros."
            ),
            comando=[
                str(
                    python_exe
                ),
                "-m",
                "pip",
                "install",
                especificacion,
            ],
        )

    # =========================================================
    # INSTALAR
    # =========================================================

    def instalar(
        self,
        carpeta_proyecto: str | Path,
        plan: PlanEntornoProyecto,
        dependencia: DependenciaProyecto,
        confirmado: bool = False,
    ) -> ResultadoInstalacionDependencia:

        carpeta = Path(
            carpeta_proyecto
        ).resolve()

        evaluacion = self.evaluar(
            plan=plan,
            dependencia=dependencia,
        )

        if not evaluacion.permitida:

            return ResultadoInstalacionDependencia(
                ok=False,
                nombre=dependencia.nombre,
                error=evaluacion.motivo,
            )

        if (
            evaluacion.requiere_confirmacion
            and not confirmado
        ):

            return ResultadoInstalacionDependencia(
                ok=False,
                nombre=dependencia.nombre,
                error="requiere_confirmacion",
            )

        python_exe = Path(
            evaluacion.comando[0]
        )

        try:

            snapshot = (
                self._snapshot_python(
                    carpeta_proyecto=carpeta,
                    python_exe=python_exe,
                )
            )

            proceso = subprocess.run(
                evaluacion.comando,
                cwd=str(
                    carpeta
                ),
                capture_output=True,
                text=True,
                timeout=(
                    self.timeout_segundos
                ),
                shell=False,
            )

            instalada = bool(
                proceso.returncode
                == 0
            )

            manifiesto_dir = (
                carpeta
                / ".atenas"
                / "dependencias"
            )

            manifiesto_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            manifiesto = (
                manifiesto_dir
                / (
                    self._normalizar_nombre(
                        dependencia.nombre
                    )
                    + ".json"
                )
            )

            manifiesto.write_text(
                json.dumps(
                    {
                        "dependencia":
                            asdict(
                                dependencia
                            ),

                        "evaluacion":
                            asdict(
                                evaluacion
                            ),

                        "instalada":
                            instalada,

                        "returncode":
                            proceso.returncode,

                        "stdout":
                            proceso.stdout
                            or "",

                        "stderr":
                            proceso.stderr
                            or "",

                        "snapshot":
                            str(
                                snapshot
                            ),
                    },
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
                encoding="utf-8",
            )

            return ResultadoInstalacionDependencia(
                ok=instalada,
                nombre=dependencia.nombre,
                instalada=instalada,
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
                snapshot=str(
                    snapshot
                ),
                manifiesto=str(
                    manifiesto
                ),
                error=(
                    None
                    if instalada
                    else "pip_install_fallo"
                ),
            )

        except subprocess.TimeoutExpired:

            return ResultadoInstalacionDependencia(
                ok=False,
                nombre=dependencia.nombre,
                error="timeout",
            )

        except Exception as error:

            return ResultadoInstalacionDependencia(
                ok=False,
                nombre=dependencia.nombre,
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )