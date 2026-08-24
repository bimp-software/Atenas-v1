from __future__ import annotations

import json
import shutil

from pathlib import Path

from src.atenas.cerebro.desarrollo.gestor_entornos_proyecto import (
    GestorEntornosProyecto,
)

from src.atenas.cerebro.desarrollo.gestor_rollback_entorno import (
    GestorRollbackEntorno,
)


def main():

    print()
    print("=" * 80)
    print(" ROLLBACK DE ENTORNO - ATENAS")
    print("=" * 80)

    raiz = Path.cwd().resolve()

    proyecto = (
        raiz
        / "data"
        / "pruebas_desarrollo"
        / "rollback_entorno"
        / "proyecto"
    )

    if proyecto.exists():

        shutil.rmtree(
            proyecto
        )

    (
        proyecto
        / "src"
    ).mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        proyecto
        / "src"
        / "app.py"
    ).write_text(
        "def ejecutar():\n"
        "    return True\n",
        encoding="utf-8",
    )

    gestor_entornos = (
        GestorEntornosProyecto(
            timeout_segundos=60
        )
    )

    resultado_entorno = (
        gestor_entornos
        .preparar(
            carpeta_proyecto=(
                proyecto
            ),
            crear_venv_python=True,
        )
    )

    assert resultado_entorno.ok
    assert resultado_entorno.plan is not None

    plan = (
        resultado_entorno.plan
    )

    # Creamos un snapshot vacío de dependencias.
    snapshots = (
        proyecto
        / ".atenas"
        / "snapshots_dependencias"
    )

    snapshots.mkdir(
        parents=True,
        exist_ok=True,
    )

    snapshot = (
        snapshots
        / "snapshot_vacio.json"
    )

    snapshot.write_text(
        json.dumps(
            {
                "timestamp":
                    "test",

                "returncode":
                    0,

                "freeze":
                    [],

                "requirements_hash":
                    None,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    gestor = (
        GestorRollbackEntorno(
            timeout_segundos=120
        )
    )

    resultado = (
        gestor.restaurar(
            carpeta_proyecto=(
                proyecto
            ),
            plan=plan,
            snapshot=(
                snapshot
            ),
        )
    )

    print()
    print(
        "OK:",
        resultado.ok
    )

    print(
        "Restaurado:",
        resultado.restaurado
    )

    print(
        "Snapshot:",
        resultado.snapshot
    )

    print()
    print("-" * 80)
    print(" ACCIONES")
    print("-" * 80)

    for accion in (
        resultado.acciones
    ):

        print(
            "-",
            accion
        )

    assert resultado.ok
    assert resultado.restaurado

    print()
    print(
        "Proyecto persistente:",
        proyecto
    )

    print(
        f'explorer "{proyecto}"'
    )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()