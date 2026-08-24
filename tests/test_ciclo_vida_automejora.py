from __future__ import annotations

from dataclasses import dataclass

from src.atenas.cerebro.desarrollo.ciclo_vida import (
    GestorCicloVidaAtenas,
)


@dataclass
class ResultadoFalso:
    ok: bool = True


class DesarrolloFalso:

    def __init__(self):
        self.llamadas = 0

    def ejecutar_iniciativa_automejora(
        self,
        tests=None,
        forzar=False,
        permitir_aplicacion=None,
        limite_archivos=None,
    ):
        self.llamadas += 1

        assert forzar is False
        assert permitir_aplicacion is False

        return ResultadoFalso()


def main():

    print()
    print("=" * 80)
    print(" CICLO DE VIDA DE AUTOMEJORA - ATENAS")
    print("=" * 80)

    desarrollo = DesarrolloFalso()

    ciclo = GestorCicloVidaAtenas(
        desarrollo=desarrollo,
        revisar_cada_turnos=3,
    )

    for _ in range(2):
        ciclo.registrar_turno()

    assert ciclo.debe_revisar() is False

    ciclo.registrar_turno()

    assert ciclo.debe_revisar() is True

    resultado = ciclo.revisar_si_corresponde()

    assert resultado is not None
    assert desarrollo.llamadas == 1
    assert ciclo.estado.turnos_desde_revision == 0
    assert ciclo.estado.total_revisiones == 1

    print()
    print("Llamadas desarrollo:", desarrollo.llamadas)
    print("Total revisiones:", ciclo.estado.total_revisiones)
    print("Última revisión:", ciclo.estado.ultima_revision)

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()