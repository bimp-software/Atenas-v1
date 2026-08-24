from __future__ import annotations

import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    GestorParches,
    NivelRiesgo,
    PoliticaDesarrollo,
    SandboxCodigo,
    VerificadorCambio,
)


def main():

    print()
    print("=" * 70)
    print(" VERIFICADOR DE CAMBIOS - ATENAS")
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

        archivo = (
            proyecto
            / "modulo.py"
        )

        original = (
            "def sumar(a, b):\n"
            "    return a - b\n"
        )

        nuevo = (
            "def sumar(a, b):\n"
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
            / "test_modulo.py"
        ).write_text(
            (
                "from modulo import sumar\n\n"
                "def main():\n"
                "    assert sumar(2, 2) == 4\n\n"
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

        gestor = (
            GestorParches(
                raiz_proyecto=(
                    proyecto
                ),
                politica=politica,
            )
        )

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

        verificador = (
            VerificadorCambio(
                politica=politica
            )
        )

        # =====================================================
        # CAMBIO
        # =====================================================

        cambio = (
            gestor.preparar_cambio(
                archivo="modulo.py",

                contenido_original=(
                    original
                ),

                contenido_nuevo=(
                    nuevo
                ),

                razon=(
                    "Corregir función sumar."
                ),
            )
        )

        entorno = (
            sandbox.crear()
        )

        resultado_sandbox = (
            sandbox.probar_cambio(
                entorno=entorno,

                cambio=cambio,

                tests=[
                    "tests.test_modulo"
                ],
            )
        )

        assert (
            resultado_sandbox.ok
        )

        # =====================================================
        # VERIFICAR
        # =====================================================

        resultado = (
            verificador.verificar(
                cambio=(
                    cambio
                ),

                resultado_sandbox=(
                    resultado_sandbox
                ),
            )
        )

        print()
        print(
            "Válido:",
            resultado.valido
        )

        print(
            "Riesgo:",
            resultado.riesgo
        )

        print(
            "Requiere confirmación:",
            resultado.requiere_confirmacion
        )

        print(
            "Autoaplicable:",
            resultado.autoaplicable
        )

        print(
            "Motivos:",
            resultado.motivos
        )

        print(
            "Advertencias:",
            resultado.advertencias
        )

        assert resultado.valido

        assert (
            resultado.riesgo
            == NivelRiesgo.BAJO
        )

        assert (
            resultado.autoaplicable
            is True
        )

        print()
        print("=" * 70)
        print(" TEST CORRECTO")
        print("=" * 70)


if __name__ == "__main__":
    main()