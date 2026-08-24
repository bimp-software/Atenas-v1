from __future__ import annotations

import json
import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    AutoMejora,
    GestorParches,
    InspectorCodigo,
    MapaProyecto,
    PlanificadorMejoras,
    PoliticaDesarrollo,
    SandboxCodigo,
    VerificadorCambio,
    TipoHallazgo,
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
                    "calculadora.py"
                ),
                "razon": (
                    "Separar la validación "
                    "en una función auxiliar."
                ),
                "contenido_nuevo": (
                    "def _validar_numeros(a, b):\n"
                    "    if not isinstance(a, (int, float)):\n"
                    "        raise TypeError('a inválido')\n"
                    "    if not isinstance(b, (int, float)):\n"
                    "        raise TypeError('b inválido')\n"
                    "\n"
                    "\n"
                    "def sumar(a, b):\n"
                    "    _validar_numeros(a, b)\n"
                    "    return a + b\n"
                ),
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" PLANIFICADOR DE MEJORAS - ATENAS")
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
            / "calculadora.py"
        )

        original = (
            "def sumar(a, b):\n"
            "    if not isinstance(a, (int, float)):\n"
            "        raise TypeError('a inválido')\n"
            "    if not isinstance(b, (int, float)):\n"
            "        raise TypeError('b inválido')\n"
            "    return a + b\n"
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
            / "test_calculadora.py"
        ).write_text(
            (
                "from src.atenas.ejemplo.calculadora "
                "import sumar\n\n"
                "def main():\n"
                "    assert sumar(2, 3) == 5\n"
                "    try:\n"
                "        sumar('2', 3)\n"
                "    except TypeError:\n"
                "        pass\n"
                "    else:\n"
                "        raise AssertionError("
                "'debe fallar con texto')\n"
                "    print('TEST CORRECTO')\n\n"
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

        # Creamos un hallazgo controlado.
        informe = (
            automejora
            .analizar_proyecto()
        )

        hallazgo = next(
            (
                item
                for item
                in informe.hallazgos
                if (
                    item.tipo
                    == TipoHallazgo.TEST_FALTANTE
                    and item.archivo
                    == (
                        "src/atenas/ejemplo/"
                        "calculadora.py"
                    )
                )
            ),
            None,
        )

        # El archivo sí tiene test, así que el detector puede
        # no crear TEST_FALTANTE. Para este test del planificador
        # construimos un hallazgo equivalente si hace falta.
        if hallazgo is None:

            from src.atenas.cerebro.desarrollo import (
                HallazgoMejora,
                NivelRiesgo,
            )

            hallazgo = HallazgoMejora(
                tipo=(
                    TipoHallazgo.FUNCION_GRANDE
                ),
                archivo=(
                    "src/atenas/ejemplo/"
                    "calculadora.py"
                ),
                descripcion=(
                    "La función concentra validación "
                    "y operación."
                ),
                severidad=0.70,
                confianza=0.90,
                linea=1,
                simbolo="sumar",
                riesgo_estimado=(
                    NivelRiesgo.BAJO
                ),
                requiere_confirmacion=False,
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

        propuesta = (
            planificador
            .proponer(
                hallazgo=hallazgo,
                tests=[
                    "tests.test_calculadora"
                ],
            )
        )

        print()
        print(
            "OK:",
            propuesta.ok
        )

        print(
            "Mensaje:",
            propuesta.mensaje
        )

        assert propuesta.ok
        assert propuesta.cambio is not None
        assert propuesta.sandbox is not None
        assert propuesta.sandbox.ok
        assert propuesta.verificacion is not None
        assert propuesta.verificacion.valido
        assert propuesta.aplicada is False

        print()
        print("DIFF:")
        print(
            propuesta.cambio.diff
        )

        # El proyecto real NO debe cambiar.
        actual = (
            archivo.read_text(
                encoding="utf-8"
            )
        )

        assert actual == original

        print()
        print(
            "Proyecto real intacto: SÍ"
        )

        print(
            "Sandbox validado: SÍ"
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()