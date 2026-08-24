from __future__ import annotations

import tempfile

from pathlib import Path

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from src.config.settings import settings

from src.atenas.cerebro.desarrollo import (
    SistemaDesarrolloAtenas,
)


def main():

    print()
    print("=" * 80)
    print(" SISTEMA DE DESARROLLO - ATENAS")
    print("=" * 80)

    llm = OllamaClient(
        config=settings.llm
    )

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        proyecto = (
            raiz
            / "proyecto"
        )

        proyecto.mkdir()

        (
            proyecto
            / "modulo.py"
        ).write_text(
            (
                "class Ejemplo:\n"
                "    def saludar(self):\n"
                "        return 'hola'\n"
            ),
            encoding="utf-8",
        )

        sistema = (
            SistemaDesarrolloAtenas(
                llm=llm,
                raiz_proyecto=proyecto,

                db_historial=(
                    raiz
                    / "historial.db"
                ),
            )
        )

        # =====================================================
        # ESTADO
        # =====================================================

        estado = (
            sistema.estado()
        )

        print()
        print(
            "Disponible:",
            estado.disponible
        )

        print(
            "Inspector:",
            estado.inspector
        )

        print(
            "Mapa:",
            estado.mapa_proyecto
        )

        print(
            "Diagnóstico:",
            estado.diagnostico
        )

        print(
            "Programador:",
            estado.programador
        )

        print(
            "Sandbox:",
            estado.sandbox
        )

        print(
            "Verificador:",
            estado.verificador
        )

        print(
            "Rollback:",
            estado.rollback
        )

        print(
            "Autorreparación:",
            estado.autorreparacion
        )

        assert estado.disponible
        assert estado.inspector
        assert estado.programador
        assert estado.sandbox
        assert estado.rollback
        assert estado.autorreparacion

        # =====================================================
        # LEER CÓDIGO
        # =====================================================

        lectura = (
            sistema.leer_codigo(
                "modulo.py"
            )
        )

        print()
        print(
            "Leer modulo.py:",
            lectura["ok"]
        )

        assert lectura["ok"]

        # =====================================================
        # SÍMBOLO
        # =====================================================

        simbolos = (
            sistema.buscar_simbolo(
                "Ejemplo"
            )
        )

        print()
        print(
            "Símbolo Ejemplo:",
            simbolos
        )

        assert simbolos

        # =====================================================
        # CONTEXTO
        # =====================================================

        print()
        print("=" * 80)
        print(" CONTEXTO PARA QWEN")
        print("=" * 80)

        print()
        print(
            sistema.contexto_para_llm()
        )

        # =====================================================
        # HISTORIAL VACÍO
        # =====================================================

        cambios = (
            sistema.ultimos_cambios()
        )

        print()
        print(
            "Cambios registrados:",
            len(cambios)
        )

        assert (
            len(cambios)
            == 0
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()