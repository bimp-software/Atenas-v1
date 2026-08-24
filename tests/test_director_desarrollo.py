from __future__ import annotations

from dataclasses import dataclass, field

from src.atenas.cerebro.desarrollo.director_desarrollo import (
    DirectorDesarrolloAutonomo,
    TipoIniciativaDesarrollo,
)


class Riesgo:
    value = "bajo"


class TipoHallazgo:
    value = "funcion_grande"


@dataclass
class Hallazgo:
    archivo: str = "src/atenas/modulo.py"
    simbolo: str = "procesar"
    tipo: object = field(default_factory=TipoHallazgo)
    severidad: float = 0.91
    confianza: float = 0.96
    riesgo_estimado: object = field(default_factory=Riesgo)
    requiere_confirmacion: bool = False


@dataclass
class Informe:
    hallazgos: list = field(default_factory=lambda: [Hallazgo()])


class RegistroVacio:
    def pendientes(self, limite=10):
        return []


@dataclass
class ResultadoCiclo:
    ok: bool = True
    mensaje: str = "Propuesta preparada."
    error: str | None = None


class DesarrolloFalso:
    def __init__(self):
        self.registro_propuestas = RegistroVacio()
        self.llamadas = 0

    def analizar_mejoras(self):
        return Informe()

    def ejecutar_ciclo_automejora(self, tests=None, permitir_aplicacion=False):
        self.llamadas += 1
        assert permitir_aplicacion is False
        return ResultadoCiclo()


def main():
    print()
    print("=" * 80)
    print(" DIRECTOR AUTÓNOMO DE DESARROLLO - ATENAS")
    print("=" * 80)

    desarrollo = DesarrolloFalso()

    director = DirectorDesarrolloAutonomo(
        desarrollo=desarrollo,
        supervisor_errores=None,
    )

    iniciativa = director.decidir()

    print()
    print("Tipo:", iniciativa.tipo)
    print("Descripción:", iniciativa.descripcion)
    print("Prioridad:", iniciativa.prioridad)
    print("Confianza:", iniciativa.confianza)
    print("Puede ejecutarse sola:", iniciativa.puede_ejecutarse_sola)

    assert (
        iniciativa.tipo
        == TipoIniciativaDesarrollo.ORGANIZAR_PROYECTO
    )

    resultado = director.ejecutar(
        permitir_aplicacion=False
    )

    assert resultado.ok
    assert resultado.ejecutada
    assert desarrollo.llamadas == 1

    print()
    print("Resultado:", resultado.mensaje)

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()
