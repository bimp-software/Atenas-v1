from __future__ import annotations

import json
import os
import subprocess

from dataclasses import dataclass, field
from pathlib import Path

from .gestor_entornos_proyecto import (
    PlanEntornoProyecto,
    TipoEntorno,
)


@dataclass
class ResultadoRollbackEntorno:
    ok: bool
    tipo: str

    restaurado: bool = False

    snapshot: str | None = None

    acciones: list[str] = field(
        default_factory=list
    )

    stdout: str = ""
    stderr: str = ""

    error: str | None = None


class GestorRollbackEntorno:
    """
    Restaura el estado de dependencias de un proyecto usando los
    snapshots creados antes de instalaciones.

    Primera versión:
    - Python: restaura exactamente el pip freeze del snapshot.
    - No toca el Python global.
    - Trabaja solo con el .venv del proyecto.
    - No usa shell=True.
    - No inventa rollback si el snapshot no existe.

    Node y otros runtimes se incorporarán después.
    """

    def __init__(
        self,
        timeout_segundos: int = 180,
    ):
        self.timeout_segundos = max(
            30,
            int(timeout_segundos),
        )

    # =========================================================
    # PYTHON
    # =========================================================

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
    def _leer_snapshot_python(
        snapshot: Path,
    ) -> list[str]:

        datos = json.loads(
            snapshot.read_text(
                encoding="utf-8"
            )
        )

        freeze = (
            datos.get(
                "freeze",
                [],
            )
            or []
        )

        return [
            str(item).strip()
            for item
            in freeze
            if str(item).strip()
        ]

    def _rollback_python(
        self,
        carpeta_proyecto: Path,
        plan: PlanEntornoProyecto,
        snapshot: Path,
    ) -> ResultadoRollbackEntorno:

        if not plan.entorno_virtual:

            return ResultadoRollbackEntorno(
                ok=False,
                tipo="python",
                snapshot=str(
                    snapshot
                ),
                error=(
                    "El plan no contiene "
                    "un entorno virtual."
                ),
            )

        python_exe = (
            self._python_venv(
                plan.entorno_virtual
            )
        )

        if not python_exe.exists():

            return ResultadoRollbackEntorno(
                ok=False,
                tipo="python",
                snapshot=str(
                    snapshot
                ),
                error=(
                    "El ejecutable Python "
                    "del .venv no existe."
                ),
            )

        try:

            freeze_objetivo = (
                self._leer_snapshot_python(
                    snapshot
                )
            )

        except Exception as error:

            return ResultadoRollbackEntorno(
                ok=False,
                tipo="python",
                snapshot=str(
                    snapshot
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        acciones = []

        # =====================================================
        # ESTADO ACTUAL
        # =====================================================

        actual = subprocess.run(
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

        if actual.returncode != 0:

            return ResultadoRollbackEntorno(
                ok=False,
                tipo="python",
                snapshot=str(
                    snapshot
                ),
                stdout=(
                    actual.stdout
                    or ""
                ),
                stderr=(
                    actual.stderr
                    or ""
                ),
                error="pip_freeze_fallo",
            )

        freeze_actual = {
            linea.strip()
            for linea
            in (
                actual.stdout
                or ""
            ).splitlines()
            if linea.strip()
        }

        freeze_objetivo_set = set(
            freeze_objetivo
        )

        # =====================================================
        # DESINSTALAR LO QUE NO ESTABA EN EL SNAPSHOT
        # =====================================================

        extras = sorted(
            freeze_actual
            - freeze_objetivo_set
        )

        if extras:

            nombres = []

            for especificacion in extras:

                nombre = (
                    especificacion
                    .split(
                        "==",
                        1,
                    )[0]
                    .strip()
                )

                if nombre:
                    nombres.append(
                        nombre
                    )

            if nombres:

                proceso_uninstall = (
                    subprocess.run(
                        [
                            str(
                                python_exe
                            ),
                            "-m",
                            "pip",
                            "uninstall",
                            "-y",
                            *nombres,
                        ],
                        cwd=str(
                            carpeta_proyecto
                        ),
                        capture_output=True,
                        text=True,
                        timeout=(
                            self.timeout_segundos
                        ),
                        shell=False,
                    )
                )

                acciones.append(
                    (
                        "Se intentó retirar "
                        f"{len(nombres)} paquete(s) "
                        "que no estaban en el snapshot."
                    )
                )

                if (
                    proceso_uninstall.returncode
                    != 0
                ):

                    return ResultadoRollbackEntorno(
                        ok=False,
                        tipo="python",
                        snapshot=str(
                            snapshot
                        ),
                        acciones=acciones,
                        stdout=(
                            proceso_uninstall.stdout
                            or ""
                        ),
                        stderr=(
                            proceso_uninstall.stderr
                            or ""
                        ),
                        error=(
                            "pip_uninstall_fallo"
                        ),
                    )

        # =====================================================
        # REINSTALAR VERSIONES DEL SNAPSHOT
        # =====================================================

        if freeze_objetivo:

            requirements_temp = (
                carpeta_proyecto
                / ".atenas"
                / "rollback_requirements.txt"
            )

            requirements_temp.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            requirements_temp.write_text(
                "\n".join(
                    freeze_objetivo
                )
                + "\n",
                encoding="utf-8",
            )

            proceso_install = (
                subprocess.run(
                    [
                        str(
                            python_exe
                        ),
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        str(
                            requirements_temp
                        ),
                    ],
                    cwd=str(
                        carpeta_proyecto
                    ),
                    capture_output=True,
                    text=True,
                    timeout=(
                        self.timeout_segundos
                    ),
                    shell=False,
                )
            )

            acciones.append(
                (
                    "Se reinstalaron las versiones "
                    "registradas en el snapshot."
                )
            )

            if (
                proceso_install.returncode
                != 0
            ):

                return ResultadoRollbackEntorno(
                    ok=False,
                    tipo="python",
                    snapshot=str(
                        snapshot
                    ),
                    acciones=acciones,
                    stdout=(
                        proceso_install.stdout
                        or ""
                    ),
                    stderr=(
                        proceso_install.stderr
                        or ""
                    ),
                    error="pip_install_rollback_fallo",
                )

        # =====================================================
        # VALIDACIÓN FINAL
        # =====================================================

        final = subprocess.run(
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

        if final.returncode != 0:

            return ResultadoRollbackEntorno(
                ok=False,
                tipo="python",
                snapshot=str(
                    snapshot
                ),
                acciones=acciones,
                stdout=(
                    final.stdout
                    or ""
                ),
                stderr=(
                    final.stderr
                    or ""
                ),
                error=(
                    "validacion_final_fallo"
                ),
            )

        estado_final = {
            linea.strip()
            for linea
            in (
                final.stdout
                or ""
            ).splitlines()
            if linea.strip()
        }

        restaurado = (
            estado_final
            == freeze_objetivo_set
        )

        return ResultadoRollbackEntorno(
            ok=restaurado,
            tipo="python",
            restaurado=(
                restaurado
            ),
            snapshot=str(
                snapshot
            ),
            acciones=acciones,
            stdout=(
                final.stdout
                or ""
            ),
            stderr=(
                final.stderr
                or ""
            ),
            error=(
                None
                if restaurado
                else (
                    "estado_final_no_coincide "
                    "con snapshot"
                )
            ),
        )

    # =========================================================
    # PÚBLICO
    # =========================================================

    def restaurar(
        self,
        carpeta_proyecto: str | Path,
        plan: PlanEntornoProyecto,
        snapshot: str | Path,
    ) -> ResultadoRollbackEntorno:

        carpeta = Path(
            carpeta_proyecto
        ).resolve()

        snapshot_path = Path(
            snapshot
        ).resolve()

        if not carpeta.exists():

            return ResultadoRollbackEntorno(
                ok=False,
                tipo=(
                    plan.tipo.value
                ),
                error=(
                    "La carpeta del proyecto "
                    "no existe."
                ),
            )

        if not snapshot_path.exists():

            return ResultadoRollbackEntorno(
                ok=False,
                tipo=(
                    plan.tipo.value
                ),
                snapshot=str(
                    snapshot_path
                ),
                error=(
                    "El snapshot no existe."
                ),
            )

        if (
            plan.tipo
            == TipoEntorno.PYTHON
        ):

            return self._rollback_python(
                carpeta_proyecto=(
                    carpeta
                ),
                plan=plan,
                snapshot=(
                    snapshot_path
                ),
            )

        return ResultadoRollbackEntorno(
            ok=False,
            tipo=(
                plan.tipo.value
            ),
            snapshot=str(
                snapshot_path
            ),
            error=(
                "Rollback todavía no implementado "
                "para este tipo de entorno."
            ),
        )