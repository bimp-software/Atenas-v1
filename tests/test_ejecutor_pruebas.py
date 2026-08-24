from __future__ import annotations

from src.atenas.cerebro.desarrollo import (
    EjecutorPruebas,
)


def main():

    print()
    print("=" * 70)
    print(" EJECUTOR DE PRUEBAS - ATENAS")
    print("=" * 70)

    ejecutor = EjecutorPruebas(
        raiz_proyecto="."
    )

    # =====================================================
    # COMPILAR ARCHIVO
    # =====================================================

    print()
    print(
        "Comprobando sintaxis de main.py..."
    )

    sintaxis = (
        ejecutor.comprobar_sintaxis(
            "main.py"
        )
    )

    print(
        "OK:",
        sintaxis.ok
    )

    print(
        "Return code:",
        sintaxis.returncode
    )

    print(
        "Duración:",
        round(
            sintaxis.duracion,
            3,
        )
    )

    if sintaxis.stderr:

        print(
            "STDERR:",
            sintaxis.stderr
        )

    assert sintaxis.ok

    # =====================================================
    # EJECUTAR TEST CONOCIDO
    # =====================================================

    print()
    print(
        "Ejecutando test del inspector..."
    )

    prueba = (
        ejecutor.ejecutar_test(
            "tests.test_inspector_codigo",
            timeout=60,
        )
    )

    print(
        "OK:",
        prueba.ok
    )

    print(
        "Return code:",
        prueba.returncode
    )

    print(
        "Duración:",
        round(
            prueba.duracion,
            3,
        )
    )

    print()
    print("STDOUT:")
    print(
        prueba.stdout[-2000:]
    )

    if prueba.stderr:

        print()
        print("STDERR:")
        print(
            prueba.stderr[-2000:]
        )

    assert prueba.ok

    # =====================================================
    # BLOQUEO DE MÓDULOS QUE NO SON TEST
    # =====================================================

    try:

        ejecutor.ejecutar_test(
            "src.atenas.main"
        )

        bloqueo_correcto = False

    except ValueError:

        bloqueo_correcto = True

    print()
    print(
        "Bloqueo de módulo no-test:",
        bloqueo_correcto
    )

    assert bloqueo_correcto

    print()
    print("=" * 70)
    print(" TEST CORRECTO")
    print("=" * 70)


if __name__ == "__main__":
    main()