from __future__ import annotations

from src.atenas.cerebro.desarrollo import (
    InspectorCodigo,
    MapaProyecto,
    DiagnosticoCodigo,
)


def main():

    print()
    print("=" * 70)
    print(" DIAGNÓSTICO DE CÓDIGO - ATENAS")
    print("=" * 70)

    inspector = InspectorCodigo(
        raiz_proyecto="."
    )

    mapa = MapaProyecto(
        inspector=inspector
    )

    diagnostico = DiagnosticoCodigo(
        inspector=inspector,
        mapa=mapa,
    )

    # =====================================================
    # ERROR REALISTA: IMPORT CIRCULAR
    # =====================================================

    traceback_prueba = r"""
Traceback (most recent call last):
  File "C:\Users\benja\Documents\GitHub\Atenas-v1\main.py", line 1, in <module>
    from src.atenas.cerebro.nucleo_conversacional import NucleoConversacional
  File "C:\Users\benja\Documents\GitHub\Atenas-v1\src\atenas\cerebro\memoria\hipocampo.py", line 5, in <module>
    from .deduplicador import DeduplicadorMemoria
  File "C:\Users\benja\Documents\GitHub\Atenas-v1\src\atenas\cerebro\memoria\deduplicador.py", line 6, in <module>
    from .deduplicador import DeduplicadorMemoria
ImportError: cannot import name 'DeduplicadorMemoria' from partially initialized module 'src.atenas.cerebro.memoria.deduplicador' (most likely due to a circular import)
""".strip()

    resultado = (
        diagnostico.analizar(
            traceback_prueba
        )
    )

    print()
    print(
        "Tipo:",
        resultado.tipo_error
    )

    print(
        "Categoría:",
        resultado.categoria
    )

    print(
        "Mensaje:",
        resultado.mensaje
    )

    print(
        "Archivo:",
        resultado.archivo_principal
    )

    print(
        "Línea:",
        resultado.linea_principal
    )

    print(
        "Función:",
        resultado.funcion_principal
    )

    print(
        "Confianza:",
        resultado.confianza
    )

    print()
    print("Archivos relacionados:")

    for archivo in (
        resultado.archivos_relacionados
    ):
        print(
            "-",
            archivo
        )

    print()
    print("Símbolos:")

    for simbolo in (
        resultado.simbolos_relacionados
    ):
        print(
            "-",
            simbolo
        )

    print()
    print("=" * 70)
    print(" CONTEXTO PARA QWEN")
    print("=" * 70)

    print()
    print(
        diagnostico.contexto_para_llm(
            resultado
        )
    )

    assert (
        resultado.tipo_error
        == "ImportError"
    )

    assert (
        resultado.categoria
        == "import_circular"
    )

    assert (
        resultado.archivo_principal
        == (
            "src/atenas/cerebro/"
            "memoria/deduplicador.py"
        )
    )

    assert (
        "DeduplicadorMemoria"
        in resultado.simbolos_relacionados
    )

    print()
    print("=" * 70)
    print(" TEST CORRECTO")
    print("=" * 70)


if __name__ == "__main__":
    main()