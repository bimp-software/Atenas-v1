from __future__ import annotations

import tempfile

from importlib.util import (
    module_from_spec,
    spec_from_file_location,
)

from pathlib import Path

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from src.config.settings import settings

from src.atenas.cerebro.desarrollo import (
    SistemaDesarrolloAtenas,
    SupervisorErrores,
    MotorAutorreparacion,
)


def main():

    print()
    print("=" * 80)
    print(" AUTORREPARACIÓN AUTOMÁTICA - ATENAS")
    print("=" * 80)

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
        # ESTRUCTURA DEL PROYECTO TEMPORAL
        # =====================================================

        src_root = (
            proyecto
            / "src"
        )

        atenas_root = (
            src_root
            / "atenas"
        )

        modulo_root = (
            atenas_root
            / "modulo_prueba"
        )

        modulo_root.mkdir(
            parents=True
        )

        for carpeta in (
            src_root,
            atenas_root,
            modulo_root,
        ):

            (
                carpeta
                / "__init__.py"
            ).write_text(
                "",
                encoding="utf-8",
            )

        # =====================================================
        # MÓDULO ROTO
        #
        # IMPORTANTE:
        #
        # El AssertionError se produce DENTRO del módulo
        # temporal de ATENAS.
        #
        # En la versión anterior el assert estaba dentro
        # de este archivo de test real:
        #
        # tests/test_autorreparacion_automatica.py
        #
        # Por eso DiagnosticoCodigo apuntaba al repositorio
        # real en vez del proyecto temporal.
        # =====================================================

        modulo = (
            modulo_root
            / "calculadora.py"
        )

        contenido_original = (
            "def sumar(a, b):\n"
            "    resultado = a - b\n"
            "\n"
            "    if resultado != a + b:\n"
            "        raise AssertionError(\n"
            "            f'sumar({a}, {b}) debería retornar {a + b}, '\n"
            "            f'pero retornó {resultado}'\n"
            "        )\n"
            "\n"
            "    return resultado\n"
        )

        modulo.write_text(
            contenido_original,
            encoding="utf-8",
        )

        # =====================================================
        # TEST DEL PROYECTO TEMPORAL
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
            / "test_calculadora.py"
        ).write_text(
            (
                "from src.atenas.modulo_prueba.calculadora "
                "import sumar\n\n"
                "\n"
                "def main():\n"
                "    resultado = sumar(10, 5)\n"
                "\n"
                "    assert resultado == 15, (\n"
                "        f'Esperaba 15, obtuvo {resultado}'\n"
                "    )\n"
                "\n"
                "    print('TEST CALCULADORA CORRECTO')\n"
                "\n"
                "\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            encoding="utf-8",
        )

        # =====================================================
        # QWEN REAL
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
        # SISTEMA DE DESARROLLO
        # =====================================================

        desarrollo = (
            SistemaDesarrolloAtenas(
                llm=llm,
                raiz_proyecto=proyecto,
                db_historial=(
                    raiz
                    / "historial.db"
                ),
            )
        )

        # =====================================================
        # SUPERVISOR
        # =====================================================

        supervisor = (
            SupervisorErrores(
                desarrollo=desarrollo
            )
        )

        # =====================================================
        # MOTOR
        # =====================================================

        motor = (
            MotorAutorreparacion(
                desarrollo=desarrollo,
                max_intentos_por_error=2,
                cooldown_segundos=0,
                autoaplicar_bajo_riesgo=True,
            )
        )

        # =====================================================
        # CARGAR MÓDULO TEMPORAL
        # =====================================================

        spec = spec_from_file_location(
            "src.atenas.modulo_prueba.calculadora",
            modulo,
        )

        if (
            spec is None
            or spec.loader is None
        ):

            raise RuntimeError(
                "No fue posible cargar "
                "el módulo temporal."
            )

        modulo_python = (
            module_from_spec(
                spec
            )
        )

        spec.loader.exec_module(
            modulo_python
        )

        # =====================================================
        # PROVOCAR EL ERROR REAL DENTRO DEL MÓDULO TEMPORAL
        # =====================================================

        evento = None

        try:

            modulo_python.sumar(
                10,
                5,
            )

        except Exception as error:

            evento = (
                supervisor.crear_evento(
                    error=error,
                    modulo=(
                        "src.atenas."
                        "modulo_prueba.calculadora"
                    ),
                    funcion="sumar",
                    componente="modulo_prueba",
                    diagnosticar=True,
                )
            )

        if evento is None:

            raise AssertionError(
                "El módulo roto no produjo "
                "el error esperado."
            )

        # =====================================================
        # ERROR DETECTADO
        # =====================================================

        print()
        print("=" * 80)
        print(" ERROR DETECTADO")
        print("=" * 80)

        print()

        supervisor.mostrar_evento(
            evento
        )

        print()
        print(
            "Evento ID:",
            evento.id
        )

        print(
            "Tipo:",
            evento.tipo
        )

        assert evento.diagnosticado

        assert (
            evento.diagnostico
            is not None
        )

        print(
            "Categoría:",
            evento.diagnostico.categoria
        )

        print(
            "Archivo:",
            evento.diagnostico.archivo_principal
        )

        # Esta es la validación clave que fallaba antes.
        assert (
            evento.diagnostico.archivo_principal
            == (
                "src/atenas/"
                "modulo_prueba/"
                "calculadora.py"
            )
        ), (
            "DiagnosticoCodigo debe apuntar al módulo "
            "temporal roto, no al archivo de test real."
        )

        # =====================================================
        # DECISIÓN AUTÓNOMA
        # =====================================================

        print()
        print("=" * 80)
        print(" DECISIÓN AUTÓNOMA")
        print("=" * 80)

        decision = (
            motor.evaluar(
                evento
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
            "Confianza:",
            decision.confianza
        )

        print(
            "Categoría:",
            decision.categoria
        )

        print(
            "Archivo:",
            decision.archivo
        )

        print(
            "Autoaplicar bajo riesgo:",
            decision.autoaplicar_bajo_riesgo
        )

        assert (
            decision.intentar
        ), decision.motivo

        assert (
            decision.archivo
            == (
                "src/atenas/"
                "modulo_prueba/"
                "calculadora.py"
            )
        )

        # =====================================================
        # MOTOR ACTUANDO
        #
        # No llamamos directamente a:
        #
        # desarrollo.reparar_error(...)
        #
        # Es MotorAutorreparacion quien inicia el proceso.
        # =====================================================

        print()
        print("=" * 80)
        print(" MOTOR ACTUANDO")
        print("=" * 80)

        resultado_motor = (
            motor.procesar(
                evento=evento,
                tests=[
                    "tests.test_calculadora"
                ],
            )
        )

        print()
        print(
            "Procesado:",
            resultado_motor.procesado
        )

        print(
            "Error motor:",
            resultado_motor.error
        )

        assert (
            resultado_motor.procesado
        )

        assert (
            resultado_motor.error
            is None
        )

        reparacion = (
            resultado_motor
            .resultado_reparacion
        )

        assert (
            reparacion
            is not None
        )

        # =====================================================
        # RESULTADO
        # =====================================================

        print()
        print("=" * 80)
        print(" RESULTADO DE LA REPARACIÓN")
        print("=" * 80)

        print()
        print(
            "OK:",
            reparacion.ok
        )

        print(
            "Estado:",
            reparacion.estado
        )

        print(
            "Aplicado:",
            reparacion.aplicado
        )

        print(
            "Cambio ID:",
            reparacion.cambio_id
        )

        for mensaje in (
            reparacion.mensajes
        ):

            print(
                mensaje
            )

        assert reparacion.ok
        assert reparacion.aplicado

        # =====================================================
        # CÓDIGO REPARADO
        # =====================================================

        contenido_actual = (
            modulo.read_text(
                encoding="utf-8"
            )
        )

        print()
        print("=" * 80)
        print(" CÓDIGO DESPUÉS DE AUTORREPARAR")
        print("=" * 80)

        print()
        print(
            contenido_actual
        )

        assert (
            contenido_actual
            != contenido_original
        )

        # =====================================================
        # TEST FINAL
        # =====================================================

        prueba_final = (
            desarrollo.pruebas
            .ejecutar_test(
                "tests.test_calculadora"
            )
        )

        print()
        print(
            "Test final:",
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
        # EVENTO RESUELTO
        # =====================================================

        print()
        print(
            "Evento resuelto:",
            evento.resuelto
        )

        assert evento.resuelto

        # =====================================================
        # HISTORIAL
        # =====================================================

        cambios = (
            desarrollo
            .ultimos_cambios(
                limite=5
            )
        )

        print()
        print(
            "Cambios registrados:",
            len(cambios)
        )

        assert cambios

        print(
            "Último estado:",
            cambios[0]["estado"]
        )

        assert (
            cambios[0]["estado"]
            == "aplicado"
        )

        # =====================================================
        # ROLLBACK
        # =====================================================

        resultado_rollback = (
            desarrollo
            .revertir_cambio(
                reparacion.cambio_id
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

        restaurado = (
            modulo.read_text(
                encoding="utf-8"
            )
        )

        assert (
            restaurado
            == contenido_original
        )

        print()
        print(
            "Código original restaurado: SÍ"
        )

    print()
    print("=" * 80)
    print(
        " TEST DE AUTORREPARACIÓN "
        "AUTÓNOMA COMPLETADO"
    )
    print("=" * 80)


if __name__ == "__main__":
    main()