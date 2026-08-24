from __future__ import annotations

from src.atenas.cerebro.identidad import (
    identidad_atenas,
    autoconcepto_atenas,
)


def main():

    print()
    print("=" * 70)
    print(" IDENTIDAD DE ATENAS")
    print("=" * 70)

    print()
    print(
        identidad_atenas
        .contexto_para_llm()
    )

    print()
    print("=" * 70)
    print(" AUTOCONCEPTO")
    print("=" * 70)

    autoconcepto_atenas.registrar_componente(
        "llm",
        True,
    )

    autoconcepto_atenas.registrar_componente(
        "memoria",
        True,
    )

    autoconcepto_atenas.registrar_componente(
        "internet",
        True,
    )

    autoconcepto_atenas.registrar_componente(
        "robot",
        False,
    )

    autoconcepto_atenas.registrar_limitacion(
        "El cuerpo robótico todavía está en desarrollo."
    )

    print()
    print(
        autoconcepto_atenas
        .contexto_para_llm()
    )

    print()
    print("=" * 70)
    print(" CAPACIDADES")
    print("=" * 70)

    for capacidad in (
        autoconcepto_atenas
        .obtener_capacidades()
    ):

        print(
            "-",
            capacidad
        )

    print()
    print("=" * 70)
    print(" LIMITACIONES")
    print("=" * 70)

    for limitacion in (
        autoconcepto_atenas
        .obtener_limitaciones()
    ):

        print(
            "-",
            limitacion
        )


if __name__ == "__main__":
    main()