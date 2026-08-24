from __future__ import annotations

import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    SistemaDesarrolloAtenas,
    TipoHallazgo,
)


class LLMFalso:
    pass


def main():

    print()
    print("=" * 80)
    print(" SISTEMA DESARROLLO + AUTOMEJORA - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        proyecto = (
            raiz
            / "proyecto"
        )

        modulo_dir = (
            proyecto
            / "src"
            / "atenas"
            / "ejemplo"
        )

        modulo_dir.mkdir(
            parents=True
        )

        for carpeta in (
            proyecto / "src",
            proyecto / "src" / "atenas",
            modulo_dir,
        ):

            (
                carpeta
                / "__init__.py"
            ).write_text(
                "",
                encoding="utf-8",
            )

        lineas = [
            "def proceso_largo():"
        ]

        for indice in range(95):

            lineas.append(
                f"    valor_{indice} = {indice}"
            )

        lineas.append(
            "    return valor_94"
        )

        (
            modulo_dir
            / "proceso.py"
        ).write_text(
            "\n".join(
                lineas
            )
            + "\n",
            encoding="utf-8",
        )

        sistema = (
            SistemaDesarrolloAtenas(
                llm=LLMFalso(),
                raiz_proyecto=proyecto,
                db_historial=(
                    raiz
                    / "historial.db"
                ),
            )
        )

        informe = (
            sistema.analizar_mejoras()
        )

        print()
        print(
            "Archivos:",
            informe.total_archivos
        )

        print(
            "Hallazgos:",
            len(
                informe.hallazgos
            )
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

        estado = (
            sistema.estado()
        )

        assert estado.automejora
        assert (
            estado.hallazgos_automejora
            == len(
                informe.hallazgos
            )
        )

        prioritarias = (
            sistema
            .mejoras_prioritarias(
                limite=5,
                severidad_minima=0.50,
            )
        )

        print()
        print(
            "Prioritarias:",
            len(prioritarias)
        )

        assert prioritarias

        print()
        print("=" * 80)
        print(" CONTEXTO AUTOMEJORA")
        print("=" * 80)

        print()
        print(
            sistema
            .contexto_mejoras_para_llm()
        )

        print()
        print("=" * 80)
        print(" CONTEXTO DESARROLLO COMPLETO")
        print("=" * 80)

        print()
        print(
            sistema.contexto_para_llm(
                incluir_automejora=True
            )
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()