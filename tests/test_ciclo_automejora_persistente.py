from __future__ import annotations

import tempfile

from dataclasses import dataclass, field
from pathlib import Path

from src.atenas.cerebro.desarrollo.ciclo_automejora import (
    CicloAutoMejora,
)

from src.atenas.cerebro.desarrollo.registro_propuestas import (
    EstadoPropuesta,
    RegistroPropuestasMejora,
)


@dataclass
class Informe:
    hallazgos: list = field(
        default_factory=lambda: [
            object()
        ]
    )


class AnalizadorFalso:

    def analizar_proyecto(
        self,
        limite_archivos=None,
    ):

        return Informe()


class Tipo:
    value = "funcion_grande"


class Riesgo:
    value = "bajo"


@dataclass
class Hallazgo:
    archivo: str = "src/atenas/ejemplo.py"
    tipo: object = field(
        default_factory=Tipo
    )
    descripcion: str = "Función grande."
    severidad: float = 0.90
    confianza: float = 0.95


@dataclass
class Cambio:
    archivo: str = "src/atenas/ejemplo.py"
    razon: str = "Separar responsabilidades."
    diff: str = "--- a\\n+++ b\\n-old\\n+new\\n"
    contenido_nuevo: str = (
        "def ejemplo():\\n"
        "    return 1\\n"
    )


@dataclass
class Verificacion:
    riesgo: object = field(
        default_factory=Riesgo
    )
    requiere_confirmacion: bool = False


@dataclass
class Sandbox:
    ok: bool = True
    pruebas: list = field(
        default_factory=list
    )


@dataclass
class Propuesta:
    ok: bool = True
    hallazgo: object = field(
        default_factory=Hallazgo
    )
    cambio: object = field(
        default_factory=Cambio
    )
    verificacion: object = field(
        default_factory=Verificacion
    )
    sandbox: object = field(
        default_factory=Sandbox
    )
    mensaje: str = "Propuesta validada."
    error: str | None = None


@dataclass
class DecisionMotor:
    motivo: str = "Hallazgo seleccionado."
    score: float = 0.91
    requiere_confirmacion: bool = False


@dataclass
class ResultadoMotor:
    procesado: bool = True
    error: str | None = None
    propuesta: object = field(
        default_factory=Propuesta
    )
    decision: object = field(
        default_factory=DecisionMotor
    )


class MotorFalso:

    def procesar(
        self,
        informe,
        tests=None,
    ):

        return ResultadoMotor()


@dataclass
class DecisionAplicacion:
    aplicar: bool = False
    requiere_confirmacion: bool = False
    motivo: str = "Solo preparar."


class PoliticaFalsa:

    def evaluar(
        self,
        propuesta,
    ):

        return DecisionAplicacion()


class AplicadorFalso:

    def aplicar(
        self,
        propuesta,
    ):

        raise AssertionError(
            "No debe aplicarse en este test."
        )


def main():

    print()
    print("=" * 80)
    print(" CICLO AUTOMEJORA + PERSISTENCIA - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        db = (
            Path(temporal)
            / "propuestas.db"
        )

        registro = (
            RegistroPropuestasMejora(
                db_path=db
            )
        )

        ciclo = (
            CicloAutoMejora(
                analizador=(
                    AnalizadorFalso()
                ),
                motor=(
                    MotorFalso()
                ),
                politica_aplicacion=(
                    PoliticaFalsa()
                ),
                aplicador=(
                    AplicadorFalso()
                ),
                registro_propuestas=(
                    registro
                ),
            )
        )

        resultado = (
            ciclo.ejecutar(
                permitir_aplicacion=False
            )
        )

        print()
        print(
            "Estado:",
            resultado.estado
        )

        print(
            "Propuesta ID:",
            resultado.propuesta_id
        )

        assert resultado.ok
        assert (
            resultado.estado
            == "propuesta_validada"
        )

        assert (
            resultado.propuesta_id
            is not None
        )

        # =====================================================
        # REINICIO SIMULADO
        # =====================================================

        registro_2 = (
            RegistroPropuestasMejora(
                db_path=db
            )
        )

        pendientes = (
            registro_2.pendientes()
        )

        print()
        print(
            "Pendientes tras reinicio:",
            len(pendientes)
        )

        assert len(pendientes) == 1

        propuesta = pendientes[0]

        assert (
            propuesta.id
            == resultado.propuesta_id
        )

        assert (
            propuesta.estado
            == EstadoPropuesta.VALIDADA
        )

        print(
            "Archivo:",
            propuesta.archivo
        )

        print(
            "Estado persistido:",
            propuesta.estado
        )

        print()
        print(
            registro_2
            .contexto_para_llm()
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()