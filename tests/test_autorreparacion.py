from __future__ import annotations

import json
import tempfile

from pathlib import Path

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


class LLMFalso:

    def chat(
        self,
        mensajes: list[dict],
    ) -> str:

        return json.dumps(
            {
                "archivo": "modulo.py",

                "razon": (
                    "La función sumar estaba "
                    "restando en vez de sumar."
                ),

                "contenido_nuevo": (
                    "def sumar(a, b):\n"
                    "    return a + b\n"
                ),
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 70)
    print(" AUTORREPARACIÓN COMPLETA - ATENAS")
    print("=" * 70)

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
        # ARCHIVO ROTO
        # =====================================================

        modulo = (
            proyecto
            / "modulo.py"
        )

        modulo.write_text(
            (
                "def sumar(a, b):\n"
                "    return a - b\n"
            ),
            encoding="utf-8",
        )

        # =====================================================
        # TEST
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
                "def main():\n"
                "    assert sumar(2, 2) == 4\n"
                "    print('TEST CORRECTO')\n\n"
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
                proyecto
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

        diagnostico = (
            DiagnosticoCodigo(
                inspector=inspector,
                mapa=mapa,
            )
        )

        gestor = (
            GestorParches(
                raiz_proyecto=proyecto,
                politica=politica,
            )
        )

        programador = (
            ProgramadorAtenas(
                llm=LLMFalso(),

                inspector=inspector,
                diagnostico=diagnostico,
                mapa=mapa,

                politica=politica,
                gestor_parches=gestor,
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

        autorreparacion = (
            Autorreparacion(
                raiz_proyecto=proyecto,

                inspector=inspector,
                diagnostico=diagnostico,
                programador=programador,

                sandbox=sandbox,
                verificador=verificador,

                politica=politica,
                historial=historial,
            )
        )

        # =====================================================
        # ERROR
        # =====================================================

        traceback = (
            'Traceback (most recent call last):\n'
            f'  File "{modulo}", line 2, in sumar\n'
            '    return a - b\n'
            'AssertionError: '
            'sumar(2, 2) debería retornar 4'
        )

        # =====================================================
        # AUTORREPARAR
        # =====================================================

        resultado = (
            autorreparacion.reparar(
                traceback_texto=traceback,

                tests=[
                    "tests.test_modulo"
                ],

                aplicar_bajo_riesgo=True,
            )
        )

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
            "Cambio ID:",
            resultado.cambio_id
        )

        print()

        for mensaje in (
            resultado.mensajes
        ):
            print(
                mensaje
            )

        assert resultado.ok
        assert resultado.aplicado

        # =====================================================
        # COMPROBAR PRODUCCIÓN
        # =====================================================

        contenido = (
            modulo.read_text(
                encoding="utf-8"
            )
        )

        assert (
            "return a + b"
            in contenido
        )

        print()
        print(
            "Archivo reparado: SÍ"
        )

        # =====================================================
        # HISTORIAL
        # =====================================================

        registro = (
            historial.obtener(
                resultado.cambio_id
            )
        )

        assert registro

        print()
        print(
            "Estado historial:",
            registro["estado"]
        )

        assert (
            registro["estado"]
            == "aplicado"
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
        print(
            "Rollback:",
            resultado_rollback.ok
        )

        print(
            resultado_rollback.mensaje
        )

        assert (
            resultado_rollback.ok
        )

        contenido_revertido = (
            modulo.read_text(
                encoding="utf-8"
            )
        )

        assert (
            "return a - b"
            in contenido_revertido
        )

        print(
            "Archivo original restaurado: SÍ"
        )

    print()
    print("=" * 70)
    print(" TEST CORRECTO")
    print("=" * 70)


if __name__ == "__main__":
    main()