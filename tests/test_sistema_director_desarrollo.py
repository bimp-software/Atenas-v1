from __future__ import annotations

import tempfile

from dataclasses import dataclass, field
from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    SistemaDesarrolloAtenas,
    TipoIniciativaDesarrollo,
)


class LLMFalso:
    pass


class Riesgo:
    value = "bajo"


class TipoHallazgo:
    value = "funcion_grande"


@dataclass
class Hallazgo:
    archivo: str = "src/atenas/ejemplo.py"
    simbolo: str = "procesar"
    tipo: object = field(
        default_factory=TipoHallazgo
    )
    severidad: float = 0.93
    confianza: float = 0.96
    riesgo_estimado: object = field(
        default_factory=Riesgo
    )
    requiere_confirmacion: bool = False


@dataclass
class Informe:
    hallazgos: list = field(
        default_factory=lambda: [
            Hallazgo()
        ]
    )


@dataclass
class ResultadoCiclo:
    ok: bool = True
    mensaje: str = "Trabajo preparado."
    error: str | None = None


def main():

    print()
    print("=" * 80)
    print(" SISTEMA + DIRECTOR DE DESARROLLO - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        proyecto = (
            raiz
            / "proyecto"
        )

        (
            proyecto
            / "src"
            / "atenas"
        ).mkdir(
            parents=True
        )

        (
            proyecto
            / "src"
            / "__init__.py"
        ).write_text(
            "",
            encoding="utf-8",
        )

        (
            proyecto
            / "src"
            / "atenas"
            / "__init__.py"
        ).write_text(
            "",
            encoding="utf-8",
        )

        sistema = (
            SistemaDesarrolloAtenas(
                llm=LLMFalso(),
                raiz_proyecto=proyecto,
                db_historial=(
                    raiz
                    / "historial.db"
                ),
            )
        )

        # Evitamos depender del análisis AST en este test:
        # inyectamos un estado de proyecto controlado.
        sistema.analizar_mejoras = (
            lambda: Informe()
        )

        llamadas = {
            "ciclo": 0,
        }

        def ciclo_falso(
            tests=None,
            permitir_aplicacion=False,
            limite_archivos=None,
        ):

            llamadas[
                "ciclo"
            ] += 1

            assert (
                permitir_aplicacion
                is False
            )

            return ResultadoCiclo()

        sistema.ejecutar_ciclo_automejora = (
            ciclo_falso
        )

        decision = (
            sistema
            .decidir_siguiente_trabajo_desarrollo()
        )

        print()
        print(
            "Decisión:",
            decision.tipo
        )

        print(
            "Descripción:",
            decision.descripcion
        )

        assert (
            decision.tipo
            == TipoIniciativaDesarrollo
            .ORGANIZAR_PROYECTO
        )

        resultado = (
            sistema
            .ejecutar_siguiente_trabajo_desarrollo(
                permitir_aplicacion=False
            )
        )

        print()
        print(
            "Ejecutada:",
            resultado.ejecutada
        )

        print(
            "Mensaje:",
            resultado.mensaje
        )

        assert resultado.ok
        assert resultado.ejecutada
        assert (
            llamadas[
                "ciclo"
            ]
            == 1
        )

        estado = (
            sistema.estado()
        )

        assert (
            estado.director_desarrollo
        )

        assert (
            estado.reanudacion_propuestas
        )

        print()
        print(
            "Director activo:",
            estado.director_desarrollo
        )

        print(
            "Reanudación activa:",
            estado.reanudacion_propuestas
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()