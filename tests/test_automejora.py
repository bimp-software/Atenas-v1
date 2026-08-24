from __future__ import annotations

import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    AutoMejora,
    InspectorCodigo,
    MapaProyecto,
    PoliticaDesarrollo,
    TipoHallazgo,
)


def main():

    print()
    print("=" * 80)
    print(" AUTOMEJORA ESTÁTICA - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        src = (
            raiz
            / "src"
            / "atenas"
            / "ejemplo"
        )

        src.mkdir(
            parents=True
        )

        for carpeta in (
            raiz / "src",
            raiz / "src" / "atenas",
            src,
        ):

            (
                carpeta
                / "__init__.py"
            ).write_text(
                "",
                encoding="utf-8",
            )

        # =====================================================
        # MÓDULO CON FUNCIÓN GRANDE Y SIN TEST
        # =====================================================

        lineas_funcion = [
            "def funcion_gigante():"
        ]

        for indice in range(100):

            lineas_funcion.append(
                f"    valor_{indice} = {indice}"
            )

        lineas_funcion.append(
            "    return valor_99"
        )

        archivo = (
            src
            / "gigante.py"
        )

        archivo.write_text(
            "\n".join(
                lineas_funcion
            )
            + "\n",
            encoding="utf-8",
        )

        # =====================================================
        # COMPONENTES
        # =====================================================

        politica = (
            PoliticaDesarrollo(
                raiz_proyecto=raiz
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

        automejora = (
            AutoMejora(
                inspector=inspector,
                mapa=mapa,
                politica=politica,
                historial=None,
            )
        )

        informe = (
            automejora
            .analizar_proyecto()
        )

        print()
        print(
            "Archivos analizados:",
            informe.total_archivos
        )

        print(
            "Hallazgos:",
            len(
                informe.hallazgos
            )
        )

        print(
            "Resumen:",
            informe.resumen
        )

        tipos = {
            hallazgo.tipo
            for hallazgo
            in informe.hallazgos
        }

        assert (
            TipoHallazgo.FUNCION_GRANDE
            in tipos
        )

        assert (
            TipoHallazgo.TEST_FALTANTE
            in tipos
        )

        print()
        print("=" * 80)
        print(" HALLAZGOS")
        print("=" * 80)

        for hallazgo in (
            informe.hallazgos
        ):

            print()
            print(
                hallazgo.tipo.value,
                "->",
                hallazgo.archivo
            )

            print(
                hallazgo.descripcion
            )

            print(
                "Severidad:",
                hallazgo.severidad
            )

            print(
                "Confianza:",
                hallazgo.confianza
            )

            print(
                "Riesgo:",
                hallazgo.riesgo_estimado
            )

        print()
        print("=" * 80)
        print(" CONTEXTO PARA QWEN")
        print("=" * 80)

        print()
        print(
            automejora
            .contexto_para_llm(
                informe
            )
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()