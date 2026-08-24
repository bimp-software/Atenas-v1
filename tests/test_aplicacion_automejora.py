from __future__ import annotations

import json
import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    AplicadorMejoras,
    GestorParches,
    HistorialCambios,
    InspectorCodigo,
    MapaProyecto,
    PlanificadorMejoras,
    PoliticaAplicacionMejoras,
    PoliticaDesarrollo,
    SandboxCodigo,
    VerificadorCambio,
    HallazgoMejora,
    TipoHallazgo,
    NivelRiesgo,
    GestorRollback,
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
                    "Extraer una validación "
                    "repetible a un helper."
                ),
                "contenido_nuevo": (
                    "def _es_numero(valor):\n"
                    "    return isinstance(valor, (int, float))\n"
                    "\n"
                    "\n"
                    "def sumar(a, b):\n"
                    "    if not _es_numero(a):\n"
                    "        raise TypeError('a inválido')\n"
                    "    if not _es_numero(b):\n"
                    "        raise TypeError('b inválido')\n"
                    "    return a + b\n"
                ),
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" APLICACIÓN SEGURA DE AUTOMEJORA - ATENAS")
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
                "        raise AssertionError('debe fallar')\n"
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

        historial = (
            HistorialCambios(
                db_path=(
                    raiz
                    / "historial.db"
                )
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

        hallazgo = HallazgoMejora(
            tipo=(
                TipoHallazgo.FUNCION_GRANDE
            ),
            archivo=(
                "src/atenas/ejemplo/"
                "calculadora.py"
            ),
            descripcion=(
                "Separar validación."
            ),
            severidad=0.80,
            confianza=0.95,
            linea=1,
            simbolo="sumar",
            riesgo_estimado=(
                NivelRiesgo.BAJO
            ),
            requiere_confirmacion=False,
        )

        propuesta = (
            planificador.proponer(
                hallazgo=hallazgo,
                tests=[
                    "tests.test_calculadora"
                ],
            )
        )

        assert propuesta.ok
        assert propuesta.sandbox is not None
        assert propuesta.sandbox.ok
        assert propuesta.verificacion is not None
        assert propuesta.verificacion.valido

        politica_mejoras = (
            PoliticaAplicacionMejoras(
                politica=politica
            )
        )

        aplicador = (
            AplicadorMejoras(
                politica_aplicacion=(
                    politica_mejoras
                ),
                gestor_parches=gestor,
                historial=historial,
            )
        )

        decision = (
            politica_mejoras.evaluar(
                propuesta
            )
        )

        print()
        print(
            "Aplicar:",
            decision.aplicar
        )

        print(
            "Motivo:",
            decision.motivo
        )

        print(
            "Líneas modificadas:",
            decision.lineas_modificadas
        )

        print(
            "Proporción:",
            round(
                decision.proporcion_cambio,
                3,
            )
        )

        assert decision.aplicar

        resultado = (
            aplicador.aplicar(
                propuesta
            )
        )

        print()
        print(
            "OK:",
            resultado.ok
        )

        print(
            "Aplicada:",
            resultado.aplicada
        )

        print(
            "Cambio ID:",
            resultado.cambio_id
        )

        print(
            "Mensaje:",
            resultado.mensaje
        )

        assert resultado.ok
        assert resultado.aplicada
        assert resultado.cambio_id

        nuevo = (
            archivo.read_text(
                encoding="utf-8"
            )
        )

        assert nuevo != original
        assert "_es_numero" in nuevo

        registro = (
            historial.obtener(
                resultado.cambio_id
            )
        )

        assert registro
        assert (
            registro["estado"]
            == "aplicado"
        )

        rollback = (
            GestorRollback(
                raiz_proyecto=proyecto,
                historial=historial,
                politica=politica,
            )
        )

        revertido = (
            rollback.revertir(
                resultado.cambio_id
            )
        )

        print()
        print(
            "Rollback:",
            revertido.ok
        )

        assert revertido.ok

        restaurado = (
            archivo.read_text(
                encoding="utf-8"
            )
        )

        assert restaurado == original

        print(
            "Original restaurado: SÍ"
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()