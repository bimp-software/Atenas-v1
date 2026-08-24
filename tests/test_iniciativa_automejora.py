from __future__ import annotations

import tempfile

from dataclasses import dataclass
from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    IniciativaAutoMejora,
    ResultadoCicloAutoMejora,
)


class CicloFalso:

    def __init__(
        self,
    ):
        self.llamadas = 0
        self.ultima_aplicacion = None

    def ejecutar(
        self,
        tests=None,
        permitir_aplicacion=False,
        limite_archivos=None,
    ):

        self.llamadas += 1
        self.ultima_aplicacion = (
            permitir_aplicacion
        )

        return ResultadoCicloAutoMejora(
            ok=True,
            estado="propuesta_validada",
            aplicada=False,
            mensaje="Ciclo simulado correcto.",
        )


def main():

    print()
    print("=" * 80)
    print(" INICIATIVA DE AUTOMEJORA - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        ciclo = (
            CicloFalso()
        )

        iniciativa = (
            IniciativaAutoMejora(
                ciclo=ciclo,
                estado_path=(
                    raiz
                    / "estado_automejora.json"
                ),
                cooldown_minutos=360,
                max_ciclos_diarios=3,
                autoaplicar=False,
            )
        )

        # =====================================================
        # PRIMER CICLO: DEBE EJECUTARSE
        # =====================================================

        decision = (
            iniciativa.decidir()
        )

        print()
        print(
            "Primera decisión:",
            decision.ejecutar
        )

        print(
            "Motivo:",
            decision.motivo
        )

        assert decision.ejecutar

        resultado = (
            iniciativa
            .ejecutar_si_corresponde()
        )

        assert resultado.ok
        assert resultado.ciclo is not None
        assert ciclo.llamadas == 1
        assert (
            ciclo.ultima_aplicacion
            is False
        )

        print(
            "Primer ciclo:",
            resultado.ciclo.estado
        )

        # =====================================================
        # SEGUNDO CICLO INMEDIATO: BLOQUEADO POR COOLDOWN
        # =====================================================

        segunda = (
            iniciativa.decidir()
        )

        print()
        print(
            "Segunda decisión:",
            segunda.ejecutar
        )

        print(
            "Motivo:",
            segunda.motivo
        )

        assert (
            segunda.ejecutar
            is False
        )

        resultado_segundo = (
            iniciativa
            .ejecutar_si_corresponde()
        )

        assert resultado_segundo.ok
        assert (
            resultado_segundo.ciclo
            is None
        )

        assert ciclo.llamadas == 1

        # =====================================================
        # FORZAR CICLO
        # =====================================================

        forzado = (
            iniciativa
            .ejecutar_si_corresponde(
                forzar=True,
                permitir_aplicacion=True,
            )
        )

        assert forzado.ok
        assert forzado.ciclo is not None
        assert ciclo.llamadas == 2
        assert (
            ciclo.ultima_aplicacion
            is True
        )

        print()
        print(
            "Ciclo forzado:",
            forzado.ciclo.estado
        )

        # =====================================================
        # PERSISTENCIA
        # =====================================================

        iniciativa_2 = (
            IniciativaAutoMejora(
                ciclo=ciclo,
                estado_path=(
                    raiz
                    / "estado_automejora.json"
                ),
                cooldown_minutos=360,
                max_ciclos_diarios=3,
                autoaplicar=False,
            )
        )

        estado = (
            iniciativa_2.estado()
        )

        print()
        print(
            "Intentos persistidos:",
            estado[
                "intentos_hoy"
            ]
        )

        print(
            "Último estado:",
            estado[
                "ultimo_estado"
            ]
        )

        assert (
            estado[
                "intentos_hoy"
            ]
            == 2
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()