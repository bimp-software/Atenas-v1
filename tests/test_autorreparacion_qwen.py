from __future__ import annotations

import tempfile

from pathlib import Path

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from src.config.settings import settings

from src.atenas.cerebro.desarrollo import (
    PoliticaDesarrollo,
    InspectorCodigo,
    MapaProyecto,
    DiagnosticoCodigo,
    GestorParches,
    ProgramadorAtenas,
    SandboxCodigo,
    VerificadorCambio,
    HistorialCambios,
    GestorRollback,
    Autorreparacion,
)


def main():

    print()
    print("=" * 80)
    print(" AUTORREPARACIÓN CON QWEN REAL - ATENAS")
    print("=" * 80)

    # =========================================================
    # PROYECTO TEMPORAL
    # =========================================================

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        proyecto = (
            raiz
            / "proyecto"
        )

        proyecto.mkdir()

        # =====================================================
        # ARCHIVO CON ERROR
        # =====================================================

        modulo = (
            proyecto
            / "modulo.py"
        )

        contenido_original = (
            "def sumar(a, b):\n"
            "    return a - b\n"
        )

        modulo.write_text(
            contenido_original,
            encoding="utf-8",
        )

        # =====================================================
        # TEST DEL PROYECTO
        # =====================================================

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
            / "test_modulo.py"
        ).write_text(
            (
                "from modulo import sumar\n\n"
                "\n"
                "def main():\n"
                "    resultado = sumar(2, 2)\n"
                "\n"
                "    assert resultado == 4, (\n"
                "        f'Esperaba 4, obtuvo {resultado}'\n"
                "    )\n"
                "\n"
                "    print('TEST MODULO CORRECTO')\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            encoding="utf-8",
        )

        # =====================================================
        # LLM REAL
        # =====================================================

        print()
        print(
            "[ATENAS][LLM] "
            "Inicializando Qwen..."
        )

        llm = OllamaClient(
            config=settings.llm
        )

        # =====================================================
        # POLÍTICA
        # =====================================================

        politica = (
            PoliticaDesarrollo(
                raiz_proyecto=proyecto
            )
        )

        # =====================================================
        # INSPECTOR
        # =====================================================

        inspector = (
            InspectorCodigo(
                raiz_proyecto=proyecto,
                politica=politica,
            )
        )

        # =====================================================
        # MAPA
        # =====================================================

        mapa = (
            MapaProyecto(
                inspector=inspector
            )
        )

        # =====================================================
        # DIAGNÓSTICO
        # =====================================================

        diagnostico_motor = (
            DiagnosticoCodigo(
                inspector=inspector,
                mapa=mapa,
            )
        )

        # =====================================================
        # PARCHES
        # =====================================================

        gestor_parches = (
            GestorParches(
                raiz_proyecto=proyecto,
                politica=politica,
            )
        )

        # =====================================================
        # PROGRAMADOR REAL
        # =====================================================

        programador = (
            ProgramadorAtenas(
                llm=llm,

                inspector=inspector,

                diagnostico=(
                    diagnostico_motor
                ),

                mapa=mapa,

                politica=politica,

                gestor_parches=(
                    gestor_parches
                ),
            )
        )

        # =====================================================
        # SANDBOX
        # =====================================================

        sandbox = (
            SandboxCodigo(
                raiz_proyecto=proyecto,

                raiz_sandboxes=(
                    raiz
                    / "sandboxes"
                ),
            )
        )

        # =====================================================
        # VERIFICADOR
        # =====================================================

        verificador = (
            VerificadorCambio(
                politica=politica
            )
        )

        # =====================================================
        # HISTORIAL
        # =====================================================

        historial = (
            HistorialCambios(
                db_path=(
                    raiz
                    / "historial.db"
                )
            )
        )

        # =====================================================
        # AUTORREPARACIÓN
        # =====================================================

        autorreparacion = (
            Autorreparacion(
                raiz_proyecto=proyecto,

                inspector=inspector,

                diagnostico=(
                    diagnostico_motor
                ),

                programador=programador,

                sandbox=sandbox,

                verificador=verificador,

                politica=politica,

                historial=historial,
            )
        )

        # =====================================================
        # TRACEBACK SIMULADO
        #
        # Qwen NO recibe la solución.
        # Solo recibe:
        #
        # - error;
        # - archivo;
        # - código actual;
        # - test.
        # =====================================================

        traceback_texto = (
            "Traceback (most recent call last):\n"
            f'  File "{modulo}", line 2, in sumar\n'
            "    return a - b\n"
            "AssertionError: "
            "sumar(2, 2) debería retornar 4"
        )

        print()
        print("=" * 80)
        print(" ERROR ENTREGADO A ATENAS")
        print("=" * 80)
        print()
        print(
            traceback_texto
        )

        # =====================================================
        # EJECUTAR AUTORREPARACIÓN
        # =====================================================

        print()
        print("=" * 80)
        print(" INICIANDO AUTORREPARACIÓN")
        print("=" * 80)

        resultado = (
            autorreparacion.reparar(
                traceback_texto=(
                    traceback_texto
                ),

                tests=[
                    "tests.test_modulo"
                ],

                # Es un proyecto temporal.
                # Podemos permitir aplicación automática.
                aplicar_bajo_riesgo=True,
            )
        )

        # =====================================================
        # RESULTADO
        # =====================================================

        print()
        print("=" * 80)
        print(" RESULTADO")
        print("=" * 80)

        print()
        print(
            "OK:",
            resultado.ok
        )

        print(
            "Estado:",
            resultado.estado
        )

        print(
            "Aplicado:",
            resultado.aplicado
        )

        print(
            "Requiere confirmación:",
            resultado.requiere_confirmacion
        )

        print(
            "Cambio ID:",
            resultado.cambio_id
        )

        if resultado.error:

            print()
            print(
                "ERROR:",
                resultado.error
            )

        # =====================================================
        # MENSAJES INTERNOS
        # =====================================================

        print()
        print("-" * 80)
        print("PROCESO INTERNO")
        print("-" * 80)

        for mensaje in (
            resultado.mensajes
        ):

            print(
                mensaje
            )

        # =====================================================
        # DIAGNÓSTICO
        # =====================================================

        if resultado.diagnostico:

            print()
            print("-" * 80)
            print("DIAGNÓSTICO")
            print("-" * 80)

            print(
                "Tipo:",
                resultado.diagnostico.tipo_error
            )

            print(
                "Categoría:",
                resultado.diagnostico.categoria
            )

            print(
                "Archivo:",
                resultado.diagnostico.archivo_principal
            )

            print(
                "Línea:",
                resultado.diagnostico.linea_principal
            )

            print(
                "Confianza:",
                resultado.diagnostico.confianza
            )

        # =====================================================
        # CAMBIO GENERADO POR QWEN
        # =====================================================

        if resultado.cambio:

            print()
            print("-" * 80)
            print("CAMBIO GENERADO POR QWEN")
            print("-" * 80)

            print()
            print(
                "Archivo:",
                resultado.cambio.archivo
            )

            print(
                "Razón:",
                resultado.cambio.razon
            )

            print()
            print("DIFF:")
            print(
                resultado.cambio.diff
            )

            print()
            print(
                "Contenido nuevo:"
            )

            print(
                resultado.cambio.contenido_nuevo
            )

        # =====================================================
        # SANDBOX
        # =====================================================

        if resultado.sandbox:

            print()
            print("-" * 80)
            print("SANDBOX")
            print("-" * 80)

            print()
            print(
                "OK:",
                resultado.sandbox.ok
            )

            print(
                "ID:",
                resultado.sandbox.sandbox_id
            )

            print(
                "Errores:",
                resultado.sandbox.errores
            )

            if resultado.sandbox.sintaxis:

                print(
                    "Sintaxis:",
                    resultado.sandbox.sintaxis.ok
                )

            for numero, prueba in enumerate(
                resultado.sandbox.pruebas,
                start=1,
            ):

                print()
                print(
                    f"Test {numero}:"
                )

                print(
                    "OK:",
                    prueba.ok
                )

                print(
                    "Return code:",
                    prueba.returncode
                )

                if prueba.stdout:

                    print(
                        "STDOUT:"
                    )

                    print(
                        prueba.stdout
                    )

                if prueba.stderr:

                    print(
                        "STDERR:"
                    )

                    print(
                        prueba.stderr
                    )

        # =====================================================
        # VERIFICACIÓN
        # =====================================================

        if resultado.verificacion:

            print()
            print("-" * 80)
            print("VERIFICACIÓN")
            print("-" * 80)

            print()
            print(
                "Válido:",
                resultado.verificacion.valido
            )

            print(
                "Riesgo:",
                resultado.verificacion.riesgo
            )

            print(
                "Autoaplicable:",
                resultado.verificacion.autoaplicable
            )

            print(
                "Requiere confirmación:",
                resultado.verificacion.requiere_confirmacion
            )

            print(
                "Motivos:",
                resultado.verificacion.motivos
            )

            print(
                "Advertencias:",
                resultado.verificacion.advertencias
            )

        # =====================================================
        # VALIDACIONES
        # =====================================================

        print()
        print("=" * 80)
        print(" VALIDACIONES")
        print("=" * 80)

        assert resultado.ok, (
            resultado.error
            or resultado.estado
        )

        assert (
            resultado.cambio
            is not None
        )

        assert (
            resultado.sandbox
            is not None
        )

        assert (
            resultado.sandbox.ok
        )

        assert (
            resultado.verificacion
            is not None
        )

        assert (
            resultado.verificacion.valido
        )

        assert (
            resultado.aplicado
        )

        # =====================================================
        # COMPROBAR QUE QWEN REALMENTE LO CORRIGIÓ
        # =====================================================

        contenido_reparado = (
            modulo.read_text(
                encoding="utf-8"
            )
        )

        print()
        print(
            "Contenido actualmente "
            "en modulo.py:"
        )

        print()
        print(
            contenido_reparado
        )

        # No exigimos una implementación textual exacta.
        # Qwen puede escribir:
        #
        # return a + b
        #
        # o una solución equivalente.
        #
        # El TEST es quien determina si funciona.

        assert (
            contenido_reparado
            != contenido_original
        )

        # =====================================================
        # EJECUTAR EL TEST UNA VEZ MÁS EN PRODUCCIÓN TEMPORAL
        # =====================================================

        from src.atenas.cerebro.desarrollo import (
            EjecutorPruebas,
        )

        ejecutor_final = (
            EjecutorPruebas(
                raiz_proyecto=proyecto
            )
        )

        prueba_final = (
            ejecutor_final
            .ejecutar_test(
                "tests.test_modulo"
            )
        )

        print()
        print(
            "Test después de reparar:",
            prueba_final.ok
        )

        print(
            prueba_final.stdout
        )

        if prueba_final.stderr:

            print(
                prueba_final.stderr
            )

        assert prueba_final.ok

        # =====================================================
        # HISTORIAL
        # =====================================================

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

        print()
        print(
            "Historial:",
            registro["estado"]
        )

        # =====================================================
        # ROLLBACK
        # =====================================================

        rollback = (
            GestorRollback(
                raiz_proyecto=proyecto,

                historial=historial,

                politica=politica,
            )
        )

        resultado_rollback = (
            rollback.revertir(
                resultado.cambio_id
            )
        )

        print()
        print("=" * 80)
        print(" ROLLBACK")
        print("=" * 80)

        print()
        print(
            "OK:",
            resultado_rollback.ok
        )

        print(
            resultado_rollback.mensaje
        )

        assert (
            resultado_rollback.ok
        )

        # =====================================================
        # COMPROBAR RESTAURACIÓN
        # =====================================================

        contenido_restaurado = (
            modulo.read_text(
                encoding="utf-8"
            )
        )

        assert (
            contenido_restaurado
            == contenido_original
        )

        print()
        print(
            "Código original restaurado: SÍ"
        )

    print()
    print("=" * 80)
    print(" TEST QWEN COMPLETADO CORRECTAMENTE")
    print("=" * 80)


if __name__ == "__main__":
    main()