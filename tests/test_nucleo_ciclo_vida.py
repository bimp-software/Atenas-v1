from __future__ import annotations

from src.atenas.cerebro.nucleo_conversacional import (
    NucleoConversacional,
)


class ResultadoRevisionFalso:
    decision = type(
        "Decision",
        (),
        {
            "ejecutar": True,
            "motivo": "Revisión simulada.",
        },
    )()

    ciclo = type(
        "Ciclo",
        (),
        {
            "estado": "propuesta_validada",
            "aplicada": False,
        },
    )()


def main():

    print()
    print("=" * 80)
    print(" CICLO DE VIDA INTEGRADO EN NÚCLEO - ATENAS")
    print("=" * 80)

    atenas = NucleoConversacional()

    try:

        # Para no esperar 20 turnos durante el test.
        atenas.ciclo_vida.revisar_cada_turnos = 3

        llamadas = {
            "total": 0,
        }

        def revision_falsa(
            tests=None,
        ):
            llamadas["total"] += 1

            atenas.ciclo_vida.estado.turnos_desde_revision = 0
            atenas.ciclo_vida.estado.total_revisiones += 1

            return ResultadoRevisionFalso()

        atenas.ciclo_vida.revisar_si_corresponde = (
            revision_falsa
        )

        # =====================================================
        # TURNO 1
        # =====================================================

        assert (
            atenas._procesar_ciclo_vida()
            is None
        )

        assert llamadas["total"] == 0

        # =====================================================
        # TURNO 2
        # =====================================================

        assert (
            atenas._procesar_ciclo_vida()
            is None
        )

        assert llamadas["total"] == 0

        # =====================================================
        # TURNO 3
        # =====================================================

        resultado = (
            atenas._procesar_ciclo_vida()
        )

        assert resultado is not None
        assert llamadas["total"] == 1

        estado = (
            atenas.estado_ciclo_vida()
        )

        print()
        print(
            "Revisar cada turnos:",
            estado[
                "revisar_cada_turnos"
            ]
        )

        print(
            "Turnos desde revisión:",
            estado[
                "turnos_desde_revision"
            ]
        )

        print(
            "Total revisiones:",
            estado[
                "total_revisiones"
            ]
        )

        assert (
            estado[
                "total_revisiones"
            ]
            == 1
        )

        assert (
            atenas
            .ultima_revision_automejora
            is resultado
        )

    finally:

        atenas.cerrar()

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()