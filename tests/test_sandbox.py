from __future__ import annotations

import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    GestorParches,
    SandboxCodigo,
)


def main():

    print()
    print("=" * 70)
    print(" SANDBOX DE CÓDIGO - ATENAS")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        proyecto = (
            raiz
            / "proyecto_original"
        )

        proyecto.mkdir()

        # =====================================================
        # ARCHIVO
        # =====================================================

        modulo = (
            proyecto
            / "modulo.py"
        )

        original = (
            "def sumar(a, b):\n"
            "    return a - b\n"
        )

        corregido = (
            "def sumar(a, b):\n"
            "    return a + b\n"
        )

        modulo.write_text(
            original,
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
                "    print('TEST MODULO CORRECTO')\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
            ),
            encoding="utf-8",
        )

        # =====================================================
        # PREPARAR CAMBIO
        # =====================================================

        gestor_original = (
            GestorParches(
                raiz_proyecto=(
                    proyecto
                )
            )
        )

        cambio = (
            gestor_original
            .preparar_cambio(
                archivo="modulo.py",

                contenido_original=(
                    original
                ),

                contenido_nuevo=(
                    corregido
                ),

                razon=(
                    "Corregir operación "
                    "de suma."
                ),
            )
        )

        # =====================================================
        # SANDBOX
        # =====================================================

        sandbox = (
            SandboxCodigo(
                raiz_proyecto=(
                    proyecto
                ),

                raiz_sandboxes=(
                    raiz
                    / "sandboxes"
                ),
            )
        )

        entorno = (
            sandbox.crear()
        )

        print()
        print(
            "Sandbox:",
            entorno.id
        )

        print(
            "Ruta:",
            entorno.proyecto
        )

        # =====================================================
        # ORIGINAL NO CAMBIADO
        # =====================================================

        assert (
            modulo.read_text(
                encoding="utf-8"
            )
            == original
        )

        # =====================================================
        # PROBAR
        # =====================================================

        resultado = (
            sandbox.probar_cambio(
                entorno=entorno,

                cambio=cambio,

                tests=[
                    "tests.test_modulo"
                ],
            )
        )

        print()
        print(
            "Resultado sandbox:",
            resultado.ok
        )

        print(
            "Mensaje:",
            resultado.mensaje
        )

        print(
            "Errores:",
            resultado.errores
        )

        if resultado.sintaxis:

            print(
                "Sintaxis:",
                resultado.sintaxis.ok
            )

        for prueba in (
            resultado.pruebas
        ):

            print()
            print(
                "Test:",
                prueba.comando
            )

            print(
                "OK:",
                prueba.ok
            )

            print(
                prueba.stdout
            )

            if prueba.stderr:

                print(
                    prueba.stderr
                )

        assert (
            resultado.ok
        )

        # =====================================================
        # SANDBOX SÍ CAMBIÓ
        # =====================================================

        sandbox_modulo = (
            entorno.proyecto
            / "modulo.py"
        )

        assert (
            "return a + b"
            in sandbox_modulo.read_text(
                encoding="utf-8"
            )
        )

        # =====================================================
        # PRODUCCIÓN SIGUE IGUAL
        # =====================================================

        assert (
            "return a - b"
            in modulo.read_text(
                encoding="utf-8"
            )
        )

        print()
        print(
            "Proyecto original intacto: SÍ"
        )

        print(
            "Sandbox corregido: SÍ"
        )

    print()
    print("=" * 70)
    print(" TEST CORRECTO")
    print("=" * 70)


if __name__ == "__main__":
    main()