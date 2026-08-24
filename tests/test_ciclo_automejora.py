from __future__ import annotations

import json
import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    AplicadorMejoras,
    AutoMejora,
    CicloAutoMejora,
    GestorParches,
    GestorRollback,
    HistorialCambios,
    InspectorCodigo,
    MapaProyecto,
    MotorAutoMejora,
    PlanificadorMejoras,
    PoliticaAplicacionMejoras,
    PoliticaDesarrollo,
    SandboxCodigo,
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
                    "Reducir una función extensa "
                    "manteniendo el mismo resultado."
                ),

                "contenido_nuevo": (
                    "def _resultado_final():\n"
                    "    return 99\n"
                    "\n"
                    "\n"
                    "def proceso_largo():\n"
                    "    return _resultado_final()\n"
                ),
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" CICLO AUTÓNOMO DE AUTOMEJORA - ATENAS")
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
            "\n".join(
                lineas
            )
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

        # =====================================================
        # COMPONENTES
        # =====================================================

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

        analizador = (
            AutoMejora(
                inspector=inspector,
                mapa=mapa,
                politica=politica,
                historial=historial,
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

        ciclo = (
            CicloAutoMejora(
                analizador=analizador,
                motor=motor,
                politica_aplicacion=(
                    politica_mejoras
                ),
                aplicador=aplicador,
            )
        )

        # =====================================================
        # 1. CICLO SIN PERMITIR APLICACIÓN
        # =====================================================

        resultado_previo = (
            ciclo.ejecutar(
                tests=[
                    "tests.test_proceso"
                ],
                permitir_aplicacion=False,
            )
        )

        print()
        print(
            "Primer estado:",
            resultado_previo.estado
        )

        print(
            "Aplicada:",
            resultado_previo.aplicada
        )

        assert resultado_previo.ok
        assert (
            resultado_previo.estado
            == "propuesta_validada"
        )
        assert (
            resultado_previo.aplicada
            is False
        )

        # Proyecto real sigue intacto.
        assert (
            archivo.read_text(
                encoding="utf-8"
            )
            == original
        )

        # =====================================================
        # 2. CICLO CON APLICACIÓN PERMITIDA
        # =====================================================

        resultado = (
            ciclo.ejecutar(
                tests=[
                    "tests.test_proceso"
                ],
                permitir_aplicacion=True,
            )
        )

        print()
        print(
            "Estado final:",
            resultado.estado
        )

        print(
            "Aplicada:",
            resultado.aplicada
        )

        print(
            "Mensaje:",
            resultado.mensaje
        )

        assert resultado.ok
        assert resultado.aplicada
        assert (
            resultado.estado
            == "aplicado"
        )

        actual = (
            archivo.read_text(
                encoding="utf-8"
            )
        )

        assert actual != original

        print()
        print(
            "Mejora aplicada al proyecto temporal: SÍ"
        )

        # =====================================================
        # 3. HISTORIAL
        # =====================================================

        assert (
            resultado.aplicacion
            is not None
        )

        cambio_id = (
            resultado.aplicacion
            .cambio_id
        )

        assert cambio_id

        registro = (
            historial.obtener(
                cambio_id
            )
        )

        assert registro
        assert (
            registro["estado"]
            == "aplicado"
        )

        print(
            "Cambio registrado:",
            cambio_id
        )

        # =====================================================
        # 4. ROLLBACK
        # =====================================================

        rollback = (
            GestorRollback(
                raiz_proyecto=proyecto,
                historial=historial,
                politica=politica,
            )
        )

        revertido = (
            rollback.revertir(
                cambio_id
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

        assert (
            restaurado
            == original
        )

        print(
            "Código original restaurado: SÍ"
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()