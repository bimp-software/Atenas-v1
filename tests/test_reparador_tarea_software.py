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

from src.atenas.cerebro.desarrollo.reparador_tarea_software import (
    ReparadorTareaSoftware,
)

from src.atenas.cerebro.desarrollo.ejecutor_plan_software import (
    EjecutorPlanSoftware,
)


class LLMFalso:

    def __init__(
        self,
    ):
        self.llamadas = 0

    def chat(
        self,
        mensajes,
    ):

        self.llamadas += 1

        # 1. Programación inicial deliberadamente incorrecta.
        if self.llamadas == 1:

            return json.dumps(
                {
                    "resumen":
                        "Implementé sumar con su prueba.",

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
                                    "    return a - b\n"
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

        # 2. Reparación basada en el fallo real.
        return json.dumps(
            {
                "resumen":
                    "Corregí sumar: debía sumar "
                    "en lugar de restar.",

                "archivos": [
                    {
                        "ruta":
                            "src/calculadora.py",

                        "contenido":
                            (
                                "def sumar(a, b):\n"
                                "    return a + b\n"
                            ),
                    }
                ],
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" PROGRAMAR + FALLAR + REPARAR + VALIDAR - ATENAS")
    print("=" * 80)

    raiz = Path.cwd().resolve()

    base = (
        raiz
        / "data"
        / "pruebas_desarrollo"
        / "reparacion_tarea"
    )

    proyecto = (
        base
        / "proyecto"
    )

    if proyecto.exists():
        shutil.rmtree(
            proyecto
        )

    proyecto.mkdir(
        parents=True,
        exist_ok=True,
    )

    ruta_plan = (
        base
        / "plan.json"
    )

    if ruta_plan.exists():
        ruta_plan.unlink()

    analisis = AnalisisRequisitos(
        nombre_proyecto="Calculadora",
        tipo_solucion=TipoSolucion.CLI,
        resumen="Prueba de reparación.",
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
        descripcion="Crear una función que sume dos números.",
        tipo="backend",
        prioridad=1.0,
        criterios_aceptacion=[
            "sumar(2, 3) debe retornar 5."
        ],
        lenguaje="python",
        requiere_pruebas=True,
    )

    plan = PlanSistemaSoftware(
        id="PLAN-REPARACION",
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

    llm = LLMFalso()

    programador = (
        ProgramadorTareaSoftware(
            llm=llm
        )
    )

    validador = (
        ValidadorTareaSoftware(
            timeout_segundos=30
        )
    )

    reparador = (
        ReparadorTareaSoftware(
            llm=llm,
            validador=validador,
            max_intentos=2,
        )
    )

    ejecutor = (
        EjecutorPlanSoftware(
            programador=programador,
            validador=validador,
            reparador=reparador,
        )
    )

    resultado = (
        ejecutor
        .ejecutar_siguiente(
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

    assert resultado.reparacion is not None

    print(
        "Reparada:",
        resultado.reparacion.reparada
    )

    print(
        "Intentos:",
        len(
            resultado.reparacion.intentos
        )
    )

    for intento in (
        resultado.reparacion.intentos
    ):

        print()
        print(
            f"Intento {intento.numero}:",
            intento.resumen
        )

        print(
            "Archivos:",
            intento.archivos_modificados
        )

        print(
            "Validación:",
            intento.validacion_ok
        )

    assert resultado.ok
    assert (
        resultado.estado
        == "tarea_reparada_completada"
    )
    assert resultado.reparacion.reparada
    assert resultado.validacion is not None
    assert resultado.validacion.ok
    assert resultado.plan_completado

    codigo = (
        proyecto
        / "src"
        / "calculadora.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "return a + b"
        in codigo
    )

    print()
    print(
        "Código corregido:",
        proyecto
        / "src"
        / "calculadora.py"
    )

    print(
        "Plan persistido:",
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