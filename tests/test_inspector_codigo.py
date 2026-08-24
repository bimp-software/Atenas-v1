from __future__ import annotations

from src.atenas.cerebro.desarrollo import (
    InspectorCodigo,
    PoliticaDesarrollo,
)


def main():

    print()
    print("=" * 70)
    print(" INSPECTOR DE CÓDIGO - ATENAS")
    print("=" * 70)

    politica = PoliticaDesarrollo(
        "."
    )

    inspector = InspectorCodigo(
        raiz_proyecto=".",
        politica=politica,
    )

    # =====================================================
    # ARCHIVOS PYTHON
    # =====================================================

    archivos = (
        inspector.listar_python()
    )

    print()
    print(
        "Archivos Python:",
        len(archivos)
    )

    for archivo in archivos[:15]:

        print(
            "-",
            archivo.ruta,
            f"({archivo.lineas} líneas)",
        )

    assert len(
        archivos
    ) > 0

    # =====================================================
    # LEER MAIN
    # =====================================================

    lectura = (
        inspector.leer_archivo(
            "main.py"
        )
    )

    assert lectura["ok"]

    print()
    print(
        "main.py:",
        lectura["lineas"],
        "líneas",
    )

    # =====================================================
    # BUSCAR CLASE
    # =====================================================

    resultados = (
        inspector.buscar_simbolo(
            "NucleoConversacional"
        )
    )

    print()
    print(
        "NucleoConversacional:"
    )

    for resultado in resultados:
        print(resultado)

    assert resultados

    # =====================================================
    # BLOQUEAR SALIDA DEL PROYECTO
    # =====================================================

    bloqueada = (
        inspector.leer_archivo(
            "../../archivo.txt"
        )
    )

    print()
    print(
        "Ruta externa:",
        bloqueada
    )

    assert not bloqueada["ok"]

    # =====================================================
    # ARCHIVO PROTEGIDO
    # =====================================================

    resultado_politica = (
        politica.evaluar_modificacion(
            "src/atenas/cerebro/"
            "desarrollo/politica.py"
        )
    )

    print()
    print(
        "Modificar politica.py:",
        resultado_politica
    )

    assert (
        resultado_politica.permitido
        is False
    )

    print()
    print("=" * 70)
    print(" TEST CORRECTO")
    print("=" * 70)


if __name__ == "__main__":
    main()