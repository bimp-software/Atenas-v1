from __future__ import annotations

from src.atenas.cerebro.desarrollo import (
    SupervisorErrores,
)


def funcion_correcta(
    a: int,
    b: int,
) -> int:

    return a + b


def funcion_rota():

    datos = {}

    return datos[
        "campo_inexistente"
    ]


def main():

    print()
    print("=" * 80)
    print(" SUPERVISOR DE ERRORES - ATENAS")
    print("=" * 80)

    supervisor = (
        SupervisorErrores(
            desarrollo=None
        )
    )

    # =====================================================
    # FUNCIÓN CORRECTA
    # =====================================================

    resultado = (
        supervisor.ejecutar(
            funcion_correcta,
            2,
            3,

            modulo="tests.test_supervisor_errores",
        )
    )

    print()
    print(
        "Función correcta:",
        resultado
    )

    assert resultado["ok"]
    assert (
        resultado["resultado"]
        == 5
    )

    # =====================================================
    # FUNCIÓN ROTA
    # =====================================================

    resultado_error = (
        supervisor.ejecutar(
            funcion_rota,

            modulo="tests.test_supervisor_errores",
        )
    )

    print()
    print(
        "Función rota OK:",
        resultado_error["ok"]
    )

    assert (
        resultado_error["ok"]
        is False
    )

    evento = (
        resultado_error[
            "evento"
        ]
    )

    assert evento is not None

    print()
    print(
        "ID:",
        evento.id
    )

    print(
        "Tipo:",
        evento.tipo
    )

    print(
        "Mensaje:",
        evento.mensaje
    )

    print(
        "Módulo:",
        evento.modulo
    )

    print(
        "Función:",
        evento.funcion
    )

    print()
    print("TRACEBACK:")
    print(
        evento.traceback
    )

    assert (
        evento.tipo
        == "KeyError"
    )

    assert (
        "campo_inexistente"
        in evento.mensaje
    )

    assert (
        supervisor.contar()
        == 1
    )

    # =====================================================
    # CONTEXTO
    # =====================================================

    print()
    print("=" * 80)
    print(" CONTEXTO PARA QWEN")
    print("=" * 80)

    print()
    print(
        supervisor
        .contexto_para_llm()
    )

    assert (
        supervisor.ultimo()
        is evento
    )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()