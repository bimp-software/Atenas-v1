from __future__ import annotations

from src.atenas.cerebro.desarrollo import (
    InspectorCodigo,
    MapaProyecto,
)


def main():

    print()
    print("=" * 70)
    print(" MAPA DEL PROYECTO - ATENAS")
    print("=" * 70)

    inspector = InspectorCodigo(
        raiz_proyecto="."
    )

    mapa = MapaProyecto(
        inspector=inspector
    )

    proyecto = (
        mapa.construir()
    )

    print()
    print(
        "Archivos analizados:",
        len(proyecto)
    )

    assert proyecto

    # =====================================================
    # BUSCAR NÚCLEO
    # =====================================================

    encontrados = []

    for ruta, archivo in (
        proyecto.items()
    ):

        for clase in archivo.clases:

            if (
                clase.nombre
                == "NucleoConversacional"
            ):

                encontrados.append(
                    (
                        ruta,
                        clase,
                    )
                )

    print()
    print(
        "NucleoConversacional encontrado:"
    )

    for ruta, clase in encontrados:

        print()
        print(
            "Archivo:",
            ruta
        )

        print(
            "Línea:",
            clase.linea
        )

        print(
            "Métodos:"
        )

        for metodo in clase.metodos:

            print(
                "-",
                metodo.nombre,
                metodo.argumentos,
            )

    assert encontrados

    # =====================================================
    # MOSTRAR CONTEXTO
    # =====================================================

    print()
    print("=" * 70)
    print(" CONTEXTO PARA QWEN")
    print("=" * 70)

    print()
    print(
        mapa.contexto_para_llm(
            max_archivos=20
        )
    )

    print()
    print("=" * 70)
    print(" TEST CORRECTO")
    print("=" * 70)


if __name__ == "__main__":
    main()