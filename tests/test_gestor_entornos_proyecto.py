from __future__ import annotations

import shutil

from pathlib import Path

from src.atenas.cerebro.desarrollo.gestor_entornos_proyecto import (
    GestorEntornosProyecto,
    TipoEntorno,
)


def main():

    print()
    print("=" * 80)
    print(" GESTOR DE ENTORNOS POR PROYECTO - ATENAS")
    print("=" * 80)

    raiz_atenas = (
        Path.cwd()
        .resolve()
    )

    base = (
        raiz_atenas
        / "data"
        / "pruebas_desarrollo"
        / "gestor_entornos"
    )

    proyecto = (
        base
        / "proyecto_python"
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
        (
            "def saludo():\n"
            "    return 'hola'\n"
        ),
        encoding="utf-8",
    )

    # Ponemos solo una dependencia que sabemos que puede estar o no
    # instalada dentro del nuevo .venv. No se instalará.
    (
        proyecto
        / "requirements.txt"
    ).write_text(
        (
            "pytest>=8.0\n"
        ),
        encoding="utf-8",
    )

    gestor = (
        GestorEntornosProyecto(
            timeout_segundos=60
        )
    )

    resultado = (
        gestor.preparar(
            carpeta_proyecto=(
                proyecto
            ),
            crear_venv_python=True,
        )
    )

    assert resultado.ok
    assert resultado.plan is not None

    plan = resultado.plan

    print()
    print(
        "Tipo:",
        plan.tipo
    )

    print(
        "Runtime disponible:",
        plan.runtime.disponible
    )

    print(
        "Versión:",
        plan.runtime.version
    )

    print(
        "Entorno virtual:",
        plan.entorno_virtual
    )

    print(
        "Entorno preparado:",
        plan.entorno_preparado
    )

    print(
        "Archivo dependencias:",
        plan.archivo_dependencias
    )

    print()
    print("-" * 80)
    print(" DEPENDENCIAS")
    print("-" * 80)

    for dep in (
        plan.dependencias
    ):

        print(
            dep.nombre,
            dep.version,
            "instalada=",
            dep.instalada,
        )

    print()
    print("-" * 80)
    print(" ACCIONES")
    print("-" * 80)

    for accion in resultado.acciones:

        print(
            "-",
            accion
        )

    print()
    print("-" * 80)
    print(" COMANDOS SUGERIDOS NO EJECUTADOS")
    print("-" * 80)

    for comando in (
        plan.comandos_sugeridos
    ):

        print(
            " ".join(
                comando
            )
        )

    print()
    print("-" * 80)
    print(" ADVERTENCIAS")
    print("-" * 80)

    for advertencia in (
        plan.advertencias
    ):

        print(
            "-",
            advertencia
        )

    assert (
        plan.tipo
        == TipoEntorno.PYTHON
    )

    assert (
        plan.runtime.disponible
    )

    assert plan.entorno_virtual

    assert Path(
        plan.entorno_virtual
    ).exists()

    assert plan.manifiesto

    assert Path(
        plan.manifiesto
    ).exists()

    print()
    print(
        "Manifiesto:",
        plan.manifiesto
    )

    print(
        "Proyecto persistente:",
        proyecto
    )

    print()
    print(
        f'explorer "{proyecto}"'
    )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()