from __future__ import annotations

import json
import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    SistemaDesarrolloAtenas,
    TipoIniciativaDesarrollo,
)


class LLMFalso:

    def chat(
        self,
        mensajes,
    ):

        ultimo = (
            mensajes[-1][
                "content"
            ]
        )

        if (
            "Divide este proyecto"
            in ultimo
        ):

            return json.dumps(
                {
                    "objetivos": [
                        {
                            "descripcion":
                                "Implementar un pequeño módulo "
                                "Python para validar comandos.",

                            "prioridad":
                                0.95,

                            "depende_de_indices":
                                [],
                        },
                    ]
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "lenguaje_principal":
                    "python",

                "resumen":
                    "Creé un módulo pequeño para validar comandos.",

                "completado":
                    True,

                "archivos": [
                    {
                        "ruta":
                            "validador.py",

                        "lenguaje":
                            "python",

                        "contenido":
                            (
                                "def validar_comando(comando):\n"
                                "    if not isinstance(comando, str):\n"
                                "        return False\n"
                                "    return bool(comando.strip())\n"
                            ),
                    },
                    {
                        "ruta":
                            "README.md",

                        "lenguaje":
                            "markdown",

                        "contenido":
                            (
                                "# Validador\n\n"
                                "Solución pequeña generada por ATENAS.\n"
                            ),
                    },
                ],
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" PROGRAMADOR AUTÓNOMO DE OBJETIVOS - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        repo = (
            raiz
            / "proyecto"
        )

        (
            repo
            / "src"
            / "atenas"
        ).mkdir(
            parents=True
        )

        (
            repo
            / "src"
            / "__init__.py"
        ).write_text(
            "",
            encoding="utf-8",
        )

        (
            repo
            / "src"
            / "atenas"
            / "__init__.py"
        ).write_text(
            "",
            encoding="utf-8",
        )

        sistema = (
            SistemaDesarrolloAtenas(
                llm=LLMFalso(),
                raiz_proyecto=repo,
                db_historial=(
                    raiz
                    / "historial.db"
                ),
            )
        )

        creado = (
            sistema
            .crear_proyecto_interno(
                nombre=(
                    "Crear validador de comandos"
                ),
                descripcion=(
                    "Preparar una solución pequeña "
                    "para validar comandos de texto."
                ),
                prioridad=0.97,
                autonomia=True,
            )
        )

        assert creado.ok
        assert (
            creado.proyecto
            is not None
        )

        informe_vacio = type(
            "Informe",
            (),
            {
                "hallazgos": [],
            },
        )()

        sistema.analizar_mejoras = (
            lambda: informe_vacio
        )

        decision = (
            sistema
            .decidir_siguiente_trabajo_desarrollo()
        )

        assert (
            decision.tipo
            == TipoIniciativaDesarrollo
            .CONTINUAR_PROYECTO
        )

        print()
        print(
            "ATENAS decidió:",
            decision.tipo
        )

        print(
            "Objetivo:",
            decision.datos[
                "objetivo"
            ]
        )

        resultado = (
            sistema
            .ejecutar_siguiente_trabajo_desarrollo(
                permitir_aplicacion=False
            )
        )

        assert resultado.ok
        assert resultado.ejecutada

        solucion = (
            resultado.resultado
        )

        print()
        print(
            "Resumen:",
            solucion.resumen
        )

        print(
            "Lenguaje:",
            solucion.lenguaje_principal
        )

        print(
            "Carpeta:",
            solucion.carpeta_solucion
        )

        print(
            "Archivos:",
            len(
                solucion.archivos
            )
        )

        assert solucion.completado
        assert (
            solucion.lenguaje_principal
            == "python"
        )

        carpeta = Path(
            solucion.carpeta_solucion
        )

        assert (
            carpeta
            / "validador.py"
        ).exists()

        assert (
            carpeta
            / "README.md"
        ).exists()

        print()
        print(
            "Solución persistida: SÍ"
        )

        print(
            "Código productivo modificado: NO"
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()