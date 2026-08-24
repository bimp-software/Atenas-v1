from __future__ import annotations

import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    PoliticaDesarrollo,
    GestorParches,
)


def main():

    print()
    print("=" * 70)
    print(" GESTOR DE PARCHES - ATENAS")
    print("=" * 70)

    # =====================================================
    # PROYECTO TEMPORAL
    # =====================================================

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        archivo = (
            raiz
            / "modulo.py"
        )

        contenido_original = (
            "def sumar(a, b):\n"
            "    return a - b\n"
        )

        contenido_nuevo = (
            "def sumar(a, b):\n"
            "    return a + b\n"
        )

        archivo.write_text(
            contenido_original,
            encoding="utf-8",
        )

        politica = (
            PoliticaDesarrollo(
                raiz
            )
        )

        gestor = (
            GestorParches(
                raiz_proyecto=raiz,
                politica=politica,
            )
        )

        # =================================================
        # PREPARAR
        # =================================================

        cambio = (
            gestor.preparar_cambio(
                archivo="modulo.py",

                contenido_original=(
                    contenido_original
                ),

                contenido_nuevo=(
                    contenido_nuevo
                ),

                razon=(
                    "La función estaba restando "
                    "en vez de sumar."
                ),
            )
        )

        print()
        print("Archivo:")
        print(
            cambio.archivo
        )

        print()
        print("Hash original:")
        print(
            cambio
            .contenido_original_hash
        )

        print()
        print("Riesgo:")
        print(
            cambio.riesgo
        )

        print()
        print("DIFF:")
        print(
            cambio.diff
        )

        # =================================================
        # VALIDAR
        # =================================================

        validacion = (
            gestor.validar(
                cambio
            )
        )

        print()
        print(
            "Válido:",
            validacion.valido
        )

        print(
            "Motivo:",
            validacion.motivo
        )

        assert (
            validacion.valido
            is True
        )

        # =================================================
        # APLICAR EN TEMPORAL
        # =================================================

        aplicacion = (
            gestor.aplicar(
                cambio
            )
        )

        print()
        print(
            "Aplicado:",
            aplicacion.ok
        )

        print(
            "Hash antes:",
            aplicacion.hash_antes
        )

        print(
            "Hash después:",
            aplicacion.hash_despues
        )

        assert aplicacion.ok

        resultado = (
            archivo.read_text(
                encoding="utf-8"
            )
        )

        assert (
            "return a + b"
            in resultado
        )

        # =================================================
        # EVITAR APLICAR EL MISMO PARCHE OTRA VEZ
        # =================================================

        segunda = (
            gestor.aplicar(
                cambio
            )
        )

        print()
        print(
            "Segunda aplicación:",
            segunda.ok
        )

        print(
            "Motivo:",
            segunda.mensaje
        )

        assert (
            segunda.ok
            is False
        )

    print()
    print("=" * 70)
    print(" TEST CORRECTO")
    print("=" * 70)


if __name__ == "__main__":
    main()