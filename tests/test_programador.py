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
)


class LLMFalso:
    """
    Simula Qwen para probar ProgramadorAtenas
    de forma determinista.
    """

    def chat(
        self,
        mensajes: list[dict],
    ) -> str:

        return json.dumps(
            {
                "archivo": "modulo.py",

                "razon": (
                    "La operación debe sumar "
                    "en lugar de restar."
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
    print(" PROGRAMADOR INTERNO - ATENAS")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        # =================================================
        # ARCHIVO CON ERROR
        # =================================================

        archivo = (
            raiz
            / "modulo.py"
        )

        archivo.write_text(
            (
                "def sumar(a, b):\n"
                "    return a - b\n"
            ),
            encoding="utf-8",
        )

        # =================================================
        # COMPONENTES
        # =================================================

        politica = (
            PoliticaDesarrollo(
                raiz
            )
        )

        inspector = (
            InspectorCodigo(
                raiz_proyecto=raiz,
                politica=politica,
            )
        )

        mapa = (
            MapaProyecto(
                inspector=inspector
            )
        )

        diagnostico_motor = (
            DiagnosticoCodigo(
                inspector=inspector,
                mapa=mapa,
            )
        )

        gestor = (
            GestorParches(
                raiz_proyecto=raiz,
                politica=politica,
            )
        )

        programador = (
            ProgramadorAtenas(
                llm=LLMFalso(),

                inspector=inspector,

                diagnostico=(
                    diagnostico_motor
                ),

                mapa=mapa,

                politica=politica,

                gestor_parches=gestor,
            )
        )

        # =================================================
        # DIAGNÓSTICO SIMULADO
        # =================================================

        traceback = (
            'Traceback (most recent call last):\n'
            f'  File "{archivo}", line 2, in sumar\n'
            '    return a - b\n'
            'AssertionError: '
            'sumar(2, 2) debería retornar 4'
        )

        diagnostico = (
            diagnostico_motor
            .analizar(
                traceback
            )
        )

        print()
        print(
            "Diagnóstico:"
        )

        print(
            diagnostico.resumen
        )

        # =================================================
        # PROPONER CAMBIO
        # =================================================

        resultado = (
            programador
            .proponer_correccion(
                diagnostico
            )
        )

        print()
        print(
            "Programación OK:",
            resultado.ok
        )

        print(
            "Mensaje:",
            resultado.mensaje
        )

        assert resultado.ok

        assert (
            resultado.cambio
            is not None
        )

        cambio = (
            resultado.cambio
        )

        print()
        print(
            "Archivo:",
            cambio.archivo
        )

        print()
        print(
            "Razón:",
            cambio.razon
        )

        print()
        print("DIFF:")
        print(
            cambio.diff
        )

        assert (
            "return a + b"
            in cambio.contenido_nuevo
        )

        # =================================================
        # LO MÁS IMPORTANTE
        #
        # El Programador NO debe haber modificado
        # el archivo todavía.
        # =================================================

        contenido_actual = (
            archivo.read_text(
                encoding="utf-8"
            )
        )

        assert (
            "return a - b"
            in contenido_actual
        )

        assert (
            "return a + b"
            not in contenido_actual
        )

        print()
        print(
            "Archivo original intacto: SÍ"
        )

    print()
    print("=" * 70)
    print(" TEST CORRECTO")
    print("=" * 70)


if __name__ == "__main__":
    main()