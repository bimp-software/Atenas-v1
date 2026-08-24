from __future__ import annotations

import json
import shutil

from pathlib import Path

from src.atenas.cerebro.desarrollo.analista_requisitos import (
    AnalisisRequisitos,
    TipoSolucion,
)

from src.atenas.cerebro.desarrollo.arquitecto_software import (
    ArquitecturaSoftware,
)

from src.atenas.cerebro.desarrollo.disenador_base_datos import (
    ModeloBaseDatos,
)

from src.atenas.cerebro.desarrollo.planificador_sistema_software import (
    EpicaSoftware,
    FaseSoftware,
    PlanSistemaSoftware,
    TareaSoftware,
)

from src.atenas.cerebro.desarrollo.programador_tarea_software import (
    ProgramadorTareaSoftware,
)

from src.atenas.cerebro.desarrollo.validador_tarea_software import (
    ValidadorTareaSoftware,
)

from src.atenas.cerebro.desarrollo.ejecutor_plan_software import (
    EjecutorPlanSoftware,
)


class LLMFalso:

    def chat(
        self,
        mensajes,
    ):

        return json.dumps(
            {
                "resumen":
                    "Implementé suma con su prueba.",

                "completado":
                    True,

                "archivos": [
                    {
                        "ruta":
                            "src/calculadora.py",

                        "lenguaje":
                            "python",

                        "contenido":
                            (
                                "def sumar(a, b):\n"
                                "    return a + b\n"
                            ),
                    },
                    {
                        "ruta":
                            "tests/test_calculadora.py",

                        "lenguaje":
                            "python",

                        "contenido":
                            (
                                "from src.calculadora import sumar\n"
                                "\n"
                                "\n"
                                "def test_sumar():\n"
                                "    assert sumar(2, 3) == 5\n"
                            ),
                    },
                ],
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" PROGRAMAR + VALIDAR + TESTEAR - ATENAS")
    print("=" * 80)

    raiz = Path.cwd().resolve()

    base_prueba = (
        raiz
        / "data"
        / "pruebas_desarrollo"
        / "validacion_tarea"
    )

    proyecto = (
        base_prueba
        / "proyecto"
    )

    # Limpia SOLO la carpeta de esta prueba para evitar que un
    # archivo viejo de una ejecución anterior haga fallar pytest.
    if proyecto.exists():

        shutil.rmtree(
            proyecto
        )

    proyecto.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_plan = (
        base_prueba
        / "plan.json"
    )

    if ruta_plan.exists():

        ruta_plan.unlink()

    analisis = AnalisisRequisitos(
        nombre_proyecto="Calculadora",
        tipo_solucion=TipoSolucion.CLI,
        resumen="Prueba de validación.",
        complejidad="baja",
    )

    arquitectura = ArquitecturaSoftware(
        estilo="monolito_modular",
        tipo_solucion="cli",
    )

    modelo = ModeloBaseDatos(
        motor="sqlite",
        nombre="no_usada",
    )

    tarea = TareaSoftware(
        id="T1",
        titulo="Implementar suma",
        descripcion="Crear función sumar.",
        tipo="backend",
        prioridad=1.0,
        lenguaje="python",
        requiere_pruebas=True,
    )

    plan = PlanSistemaSoftware(
        id="PLAN-VALIDACION",
        nombre_proyecto="Calculadora",
        tipo_solucion="cli",
        arquitectura="monolito_modular",
        complejidad="baja",
        fases=[
            FaseSoftware(
                id="F1",
                nombre="Implementación",
                objetivo="Crear suma.",
                orden=1,
                epicas=[
                    EpicaSoftware(
                        id="E1",
                        nombre="Core",
                        descripcion="Core.",
                        prioridad=1.0,
                        tareas=[
                            tarea
                        ],
                    )
                ],
            )
        ],
        ruta_persistencia=str(
            ruta_plan
        ),
    )

    programador = (
        ProgramadorTareaSoftware(
            llm=LLMFalso()
        )
    )

    validador = (
        ValidadorTareaSoftware(
            timeout_segundos=30
        )
    )

    ejecutor = (
        EjecutorPlanSoftware(
            programador=programador,
            validador=validador,
        )
    )

    resultado = (
        ejecutor.ejecutar_siguiente(
            carpeta_proyecto=proyecto,
            analisis=analisis,
            arquitectura=arquitectura,
            modelo_bd=modelo,
            plan=plan,
        )
    )

    print()
    print(
        "Estado:",
        resultado.estado
    )

    print(
        "OK:",
        resultado.ok
    )

    assert (
        resultado.validacion
        is not None
    )

    print(
        "Sintaxis:",
        resultado.validacion.sintaxis_ok
    )

    print(
        "Pruebas:",
        resultado.validacion.pruebas_ok
    )

    print(
        "Python:",
        resultado.validacion.archivos_python
    )

    # IMPORTANTE:
    # Imprimimos el resultado de pytest ANTES de los assert.
    # Así, si falla, veremos la causa exacta.
    print()
    print("-" * 80)
    print(" RESULTADO DE PYTEST")
    print("-" * 80)

    for comando in (
        resultado.validacion.comandos
    ):

        print(
            "Comando:",
            " ".join(
                comando.comando
            )
        )

        print(
            "Return code:",
            comando.returncode
        )

        if comando.stdout:

            print()
            print("STDOUT:")
            print(
                comando.stdout
            )

        if comando.stderr:

            print()
            print("STDERR:")
            print(
                comando.stderr
            )

    if resultado.validacion.errores:

        print()
        print("-" * 80)
        print(" ERRORES DE VALIDACIÓN")
        print("-" * 80)

        for error in (
            resultado.validacion.errores
        ):

            print(
                error
            )

    assert resultado.ok
    assert resultado.validacion.ok
    assert resultado.plan_completado

    assert (
        proyecto
        / "src"
        / "__init__.py"
    ).exists()

    assert (
        proyecto
        / "src"
        / "calculadora.py"
    ).exists()

    assert (
        proyecto
        / "tests"
        / "__init__.py"
    ).exists()

    assert (
        proyecto
        / "tests"
        / "test_calculadora.py"
    ).exists()

    assert ruta_plan.exists()

    print()
    print(
        "Proyecto persistente:",
        proyecto
    )

    print(
        "Plan persistente:",
        ruta_plan
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