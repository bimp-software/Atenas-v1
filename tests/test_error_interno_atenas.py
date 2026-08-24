from __future__ import annotations

from src.atenas.cerebro.desarrollo import (
    SupervisorErrores,
)


class ComponenteRoto:

    def procesar(
        self,
    ):

        objeto = {}

        return objeto[
            "propiedad_que_no_existe"
        ]


def main():

    print()
    print("=" * 80)
    print(" ERROR INTERNO SUPERVISADO - ATENAS")
    print("=" * 80)

    supervisor = (
        SupervisorErrores(
            desarrollo=None
        )
    )

    componente = (
        ComponenteRoto()
    )

    resultado = (
        supervisor.ejecutar(
            componente.procesar,

            modulo=(
                "tests."
                "test_error_interno_atenas"
            ),

            nombre_funcion=(
                "ComponenteRoto.procesar"
            ),

            componente=(
                "memoria"
            ),

            diagnosticar=False,
        )
    )

    assert (
        resultado["ok"]
        is False
    )

    evento = (
        resultado["evento"]
    )

    assert evento is not None

    print()
    print(
        "Evento:",
        evento.id
    )

    print(
        "Tipo:",
        evento.tipo
    )

    print(
        "Componente:",
        evento.componente
    )

    print(
        "Función:",
        evento.funcion
    )

    assert (
        evento.tipo
        == "KeyError"
    )

    assert (
        evento.componente
        == "memoria"
    )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()