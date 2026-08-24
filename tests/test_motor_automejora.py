from __future__ import annotations

import json
import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    AutoMejora,
    GestorParches,
    InspectorCodigo,
    MapaProyecto,
    MotorAutoMejora,
    PlanificadorMejoras,
    PoliticaDesarrollo,
    SandboxCodigo,
    TipoHallazgo,
    VerificadorCambio,
)


class LLMFalso:

    def chat(
        self,
        mensajes,
    ):

        return json.dumps(
            {
                "puede_mejorarse": True,
                "archivo": (
                    "src/atenas/ejemplo/"
                    "proceso.py"
                ),
                "razon": (
                    "Extraer parte del cálculo "
                    "a una función auxiliar."
                ),
                "contenido_nuevo": (
                    "def _valor_final():\n"
                    "    return 99\n"
                    "\n"
                    "\n"
                    "def proceso_largo():\n"
                    "    return _valor_final()\n"
                ),
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" MOTOR DE AUTOMEJORA - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        proyecto = (
            raiz
            / "proyecto"
        )

        modulo_dir = (
            proyecto
            / "src"
            / "atenas"
            / "ejemplo"
        )

        modulo_dir.mkdir(
            parents=True
        )

        for carpeta in (
            proyecto / "src",
            proyecto / "src" / "atenas",
            modulo_dir,
        ):

            (
                carpeta
                / "__init__.py"
            ).write_text(
                "",
                encoding="utf-8",
            )

        archivo = (
            modulo_dir
            / "proceso.py"
        )

        lineas = [
            "def proceso_largo():"
        ]

        for indice in range(100):

            lineas.append(
                f"    valor_{indice} = {indice}"
            )

        lineas.append(
            "    return valor_99"
        )

        original = (
            "\n".join(lineas)
            + "\n"
        )

        archivo.write_text(
            original,
            encoding="utf-8",
        )

        tests_dir = (
            proyecto
            / "tests"
        )

        tests_dir.mkdir()

        (
            tests_dir
            / "__init__.py"
        ).write_text(
            "",
            encoding="utf-8",
        )

        (
            tests_dir
            / "test_proceso.py"
        ).write_text(
            (
                "from src.atenas.ejemplo.proceso "
                "import proceso_largo\n\n"
                "def main():\n"
                "    assert proceso_largo() == 99\n"
                "    print('TEST PROCESO CORRECTO')\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            encoding="utf-8",
        )

        politica = (
            PoliticaDesarrollo(
                raiz_proyecto=proyecto
            )
        )

        inspector = (
            InspectorCodigo(
                raiz_proyecto=proyecto,
                politica=politica,
            )
        )

        mapa = (
            MapaProyecto(
                inspector=inspector
            )
        )

        gestor = (
            GestorParches(
                raiz_proyecto=proyecto,
                politica=politica,
            )
        )

        sandbox = (
            SandboxCodigo(
                raiz_proyecto=proyecto,
                raiz_sandboxes=(
                    raiz
                    / "sandboxes"
                ),
            )
        )

        verificador = (
            VerificadorCambio(
                politica=politica
            )
        )

        automejora = (
            AutoMejora(
                inspector=inspector,
                mapa=mapa,
                politica=politica,
                historial=None,
            )
        )

        planificador = (
            PlanificadorMejoras(
                llm=LLMFalso(),
                inspector=inspector,
                politica=politica,
                gestor_parches=gestor,
                sandbox=sandbox,
                verificador=verificador,
            )
        )

        motor = (
            MotorAutoMejora(
                politica=politica,
                planificador=planificador,
                severidad_minima=0.55,
                confianza_minima=0.75,
                permitir_riesgo_medio=False,
            )
        )

        informe = (
            automejora
            .analizar_proyecto()
        )

        decision = (
            motor.decidir(
                informe
            )
        )

        print()
        print(
            "Intentar:",
            decision.intentar
        )

        print(
            "Motivo:",
            decision.motivo
        )

        print(
            "Score:",
            round(
                decision.score,
                3,
            )
        )

        assert decision.intentar
        assert decision.hallazgo is not None

        print(
            "Hallazgo:",
            decision.hallazgo.tipo.value
        )

        print(
            "Archivo:",
            decision.hallazgo.archivo
        )

        assert (
            decision.hallazgo.tipo
            == TipoHallazgo.FUNCION_GRANDE
        )

        resultado = (
            motor.procesar(
                informe=informe,
                tests=[
                    "tests.test_proceso"
                ],
            )
        )

        print()
        print(
            "Procesado:",
            resultado.procesado
        )

        print(
            "Error:",
            resultado.error
        )

        assert resultado.procesado
        assert resultado.error is None
        assert resultado.propuesta is not None
        assert resultado.propuesta.ok
        assert resultado.propuesta.sandbox is not None
        assert resultado.propuesta.sandbox.ok
        assert resultado.propuesta.verificacion is not None
        assert resultado.propuesta.verificacion.valido
        assert (
            resultado.propuesta.aplicada
            is False
        )

        print()
        print(
            "Propuesta:",
            resultado.propuesta.mensaje
        )

        print()
        print("DIFF:")
        print(
            resultado
            .propuesta
            .cambio
            .diff
        )

        # El proyecto real debe seguir intacto.
        actual = (
            archivo.read_text(
                encoding="utf-8"
            )
        )

        assert (
            actual
            == original
        )

        print()
        print(
            "Proyecto real intacto: SÍ"
        )

        print(
            "Mejora validada en sandbox: SÍ"
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()