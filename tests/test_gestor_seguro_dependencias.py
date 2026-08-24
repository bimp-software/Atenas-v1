from __future__ import annotations

import shutil

from pathlib import Path

from src.atenas.cerebro.desarrollo.gestor_entornos_proyecto import (
    DependenciaProyecto,
    GestorEntornosProyecto,
)

from src.atenas.cerebro.desarrollo.gestor_seguro_dependencias import (
    GestorSeguroDependencias,
    RiesgoDependencia,
)


def main():

    print()
    print("=" * 80)
    print(" GESTOR SEGURO DE DEPENDENCIAS - ATENAS")
    print("=" * 80)

    raiz = Path.cwd().resolve()

    base = (
        raiz
        / "data"
        / "pruebas_desarrollo"
        / "dependencias_seguras"
    )

    proyecto = (
        base
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
        "def hola():\n    return 'hola'\n",
        encoding="utf-8",
    )

    (
        proyecto
        / "requirements.txt"
    ).write_text(
        "pytest>=8.0\n",
        encoding="utf-8",
    )

    gestor_entorno = (
        GestorEntornosProyecto(
            timeout_segundos=60
        )
    )

    resultado_entorno = (
        gestor_entorno
        .preparar(
            carpeta_proyecto=(
                proyecto
            ),
            crear_venv_python=True,
        )
    )

    assert resultado_entorno.ok
    assert resultado_entorno.plan is not None

    plan = resultado_entorno.plan

    dependencia = (
        DependenciaProyecto(
            nombre="pytest",
            version=">=8.0",
            origen="requirements.txt",
        )
    )

    gestor = (
        GestorSeguroDependencias(
            timeout_segundos=120
        )
    )

    evaluacion = (
        gestor.evaluar(
            plan=plan,
            dependencia=dependencia,
        )
    )

    print()
    print(
        "Dependencia:",
        evaluacion.nombre
    )

    print(
        "Permitida:",
        evaluacion.permitida
    )

    print(
        "Riesgo:",
        evaluacion.riesgo
    )

    print(
        "Requiere confirmación:",
        evaluacion.requiere_confirmacion
    )

    print(
        "Motivo:",
        evaluacion.motivo
    )

    print()
    print(
        "Comando preparado:"
    )

    print(
        " ".join(
            evaluacion.comando
        )
    )

    assert evaluacion.permitida
    assert (
        evaluacion.riesgo
        == RiesgoDependencia.MEDIO
    )
    assert (
        evaluacion.requiere_confirmacion
    )

    # Sin confirmación NO instala.
    sin_confirmar = (
        gestor.instalar(
            carpeta_proyecto=(
                proyecto
            ),
            plan=plan,
            dependencia=dependencia,
            confirmado=False,
        )
    )

    print()
    print(
        "Instalación sin confirmar:",
        sin_confirmar.ok
    )

    print(
        "Motivo:",
        sin_confirmar.error
    )

    assert not sin_confirmar.ok
    assert (
        sin_confirmar.error
        == "requiere_confirmacion"
    )

    print()
    print("-" * 80)
    print(" TEST CORRECTO")
    print("-" * 80)

    print()
    print(
        "En esta prueba NO descargamos paquetes."
    )

    print(
        "El siguiente test podrá probar una instalación "
        "real solo cuando se autorice explícitamente."
    )

    print()
    print(
        "Proyecto persistente:",
        proyecto
    )

    print(
        f'explorer "{proyecto}"'
    )


if __name__ == "__main__":
    main()