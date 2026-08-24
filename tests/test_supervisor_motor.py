from __future__ import annotations

from dataclasses import dataclass

from src.atenas.cerebro.desarrollo import (
    SupervisorErrores,
    ResultadoMotorAutorreparacion,
    DecisionAutorreparacion,
)


@dataclass
class ReparacionFalsa:
    aplicado: bool = True


class MotorFalso:

    def __init__(self):
        self.llamadas = 0

    def procesar(
        self,
        evento,
        tests=None,
    ):

        self.llamadas += 1

        return ResultadoMotorAutorreparacion(
            procesado=True,
            decision=DecisionAutorreparacion(
                intentar=True,
                motivo="Test",
                confianza=1.0,
                categoria="test",
                archivo="src/atenas/modulo.py",
                autoaplicar_bajo_riesgo=True,
            ),
            resultado_reparacion=(
                ReparacionFalsa(
                    aplicado=True
                )
            ),
            error=None,
        )


class DesarrolloFalso:

    def diagnosticar(
        self,
        traceback_texto,
    ):

        return type(
            "Diagnostico",
            (),
            {
                "categoria": "test",
                "archivo_principal":
                    "src/atenas/modulo.py",
                "linea_principal": 1,
                "confianza": 0.95,
            },
        )()


def funcion_rota():

    raise AssertionError(
        "fallo de prueba"
    )


def main():

    print()
    print("=" * 80)
    print(" SUPERVISOR + MOTOR AUTORREPARACIÓN - ATENAS")
    print("=" * 80)

    motor = MotorFalso()

    supervisor = SupervisorErrores(
        desarrollo=DesarrolloFalso(),
        motor=motor,
        reparar_automaticamente=True,
    )

    resultado = supervisor.ejecutar(
        funcion_rota,
        modulo="src.atenas.modulo",
        nombre_funcion="funcion_rota",
        componente="prueba",
    )

    assert not resultado["ok"]

    evento = resultado["evento"]

    assert evento is not None
    assert evento.diagnosticado
    assert evento.reparacion_iniciada
    assert evento.resuelto
    assert motor.llamadas == 1

    print()
    print("Diagnosticado:", evento.diagnosticado)
    print("Reparación iniciada:", evento.reparacion_iniciada)
    print("Resuelto:", evento.resuelto)
    print("Llamadas al motor:", motor.llamadas)

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()