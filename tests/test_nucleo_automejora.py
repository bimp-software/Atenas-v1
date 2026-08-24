from __future__ import annotations

from src.atenas.cerebro.nucleo_conversacional import (
    NucleoConversacional,
)


def main():

    print()
    print("=" * 80)
    print(" AUTOMEJORA REAL EN NÚCLEO - ATENAS")
    print("=" * 80)

    atenas = NucleoConversacional()

    try:

        informe = (
            atenas.analizar_mejoras()
        )

        assert informe is not None

        print()
        print(
            "Archivos analizados:",
            informe.total_archivos
        )

        print(
            "Hallazgos:",
            len(
                informe.hallazgos
            )
        )

        print()
        print("=" * 80)
        print(" PRIORIDADES")
        print("=" * 80)

        prioritarias = (
            atenas
            .mejoras_prioritarias(
                limite=10,
                severidad_minima=0.50,
            )
        )

        for numero, hallazgo in enumerate(
            prioritarias,
            start=1,
        ):

            print()
            print(
                f"{numero}.",
                hallazgo.tipo.value,
                "->",
                hallazgo.archivo
            )

            if hallazgo.simbolo:

                print(
                    "Símbolo:",
                    hallazgo.simbolo
                )

            print(
                hallazgo.descripcion
            )

            print(
                "Severidad:",
                round(
                    hallazgo.severidad,
                    3,
                )
            )

            print(
                "Riesgo:",
                hallazgo.riesgo_estimado
            )

        print()
        print("=" * 80)
        print(" CONTEXTO PARA QWEN")
        print("=" * 80)

        print()
        print(
            atenas.contexto_mejoras(
                limite=10
            )
        )

        estado = (
            atenas.estado_desarrollo()
        )

        assert (
            estado.get(
                "automejora"
            )
            is True
        )

        print()
        print(
            "Automejora activa:",
            estado["automejora"]
        )

        print(
            "Hallazgos registrados:",
            estado[
                "hallazgos_automejora"
            ]
        )

    finally:

        atenas.cerrar()

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()