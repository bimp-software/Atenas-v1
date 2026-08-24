from __future__ import annotations

from dataclasses import dataclass

from src.atenas.cerebro.desarrollo import (
    MotorAutorreparacion,
)


@dataclass
class DiagnosticoFalso:
    categoria: str
    archivo_principal: str
    linea_principal: int = 10
    confianza: float = 0.95


@dataclass
class EventoFalso:
    tipo: str
    mensaje: str
    traceback: str

    componente: str

    diagnostico: DiagnosticoFalso

    resuelto: bool = False
    reparacion_iniciada: bool = False
    resultado_reparacion: object = None


class PoliticaFalsa:

    class Resultado:

        permitido = True
        motivo = "Permitido."

        riesgo = type(
            "Riesgo",
            (),
            {
                "value": "bajo"
            },
        )()

    def evaluar_modificacion(
        self,
        archivo,
    ):

        return self.Resultado()


class DesarrolloFalso:

    def __init__(
        self,
    ):
        self.politica = (
            PoliticaFalsa()
        )


def main():

    print()
    print("=" * 80)
    print(" MOTOR DE AUTORREPARACIÓN - ATENAS")
    print("=" * 80)

    desarrollo = (
        DesarrolloFalso()
    )

    motor = (
        MotorAutorreparacion(
            desarrollo=desarrollo,

            max_intentos_por_error=2,

            cooldown_segundos=0,

            autoaplicar_bajo_riesgo=True,
        )
    )

    # =====================================================
    # CASO 1: ERROR REPARABLE
    # =====================================================

    evento_reparable = EventoFalso(
        tipo="AttributeError",

        mensaje=(
            "Objeto no tiene atributo buscar"
        ),

        traceback=(
            "Traceback..."
        ),

        componente="memoria",

        diagnostico=(
            DiagnosticoFalso(
                categoria="atributo",

                archivo_principal=(
                    "src/atenas/cerebro/"
                    "memoria/recuperador.py"
                ),
            )
        ),
    )

    decision = (
        motor.evaluar(
            evento_reparable
        )
    )

    print()
    print("CASO REPARABLE")
    print(
        "Intentar:",
        decision.intentar
    )
    print(
        "Motivo:",
        decision.motivo
    )
    print(
        "Archivo:",
        decision.archivo
    )
    print(
        "Categoría:",
        decision.categoria
    )
    print(
        "Autoaplicar:",
        decision.autoaplicar_bajo_riesgo
    )

    assert decision.intentar
    assert (
        decision.categoria
        == "atributo"
    )

    # =====================================================
    # CASO 2: ERROR EXTERNO
    # =====================================================

    evento_externo = EventoFalso(
        tipo="AttributeError",

        mensaje="error externo",

        traceback="Traceback...",

        componente="externo",

        diagnostico=(
            DiagnosticoFalso(
                categoria="atributo",

                archivo_principal=(
                    "C:/Python311/"
                    "site-packages/libreria.py"
                ),
            )
        ),
    )

    decision_externa = (
        motor.evaluar(
            evento_externo
        )
    )

    print()
    print("CASO EXTERNO")
    print(
        "Intentar:",
        decision_externa.intentar
    )
    print(
        "Motivo:",
        decision_externa.motivo
    )

    assert (
        decision_externa.intentar
        is False
    )

    # =====================================================
    # CASO 3: SISTEMA PROTEGIDO
    # =====================================================

    evento_protegido = EventoFalso(
        tipo="AttributeError",

        mensaje="error en política",

        traceback="Traceback...",

        componente="politica",

        diagnostico=(
            DiagnosticoFalso(
                categoria="atributo",

                archivo_principal=(
                    "src/atenas/cerebro/"
                    "desarrollo/politica.py"
                ),
            )
        ),
    )

    decision_protegida = (
        motor.evaluar(
            evento_protegido
        )
    )

    print()
    print("CASO PROTEGIDO")
    print(
        "Intentar:",
        decision_protegida.intentar
    )
    print(
        "Motivo:",
        decision_protegida.motivo
    )

    assert (
        decision_protegida.intentar
        is False
    )

    # =====================================================
    # CASO 4: ERROR NO REPARABLE
    # =====================================================

    evento_runtime = EventoFalso(
        tipo="ConnectionError",

        mensaje="sin conexión",

        traceback="Traceback...",

        componente="internet",

        diagnostico=(
            DiagnosticoFalso(
                categoria="runtime",

                archivo_principal=(
                    "src/atenas/cerebro/"
                    "investigacion/investigador.py"
                ),
            )
        ),
    )

    decision_runtime = (
        motor.evaluar(
            evento_runtime
        )
    )

    print()
    print("CASO RUNTIME")
    print(
        "Intentar:",
        decision_runtime.intentar
    )
    print(
        "Motivo:",
        decision_runtime.motivo
    )

    assert (
        decision_runtime.intentar
        is False
    )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()