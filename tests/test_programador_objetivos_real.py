from __future__ import annotations

import json

from pathlib import Path

from src.atenas.cerebro.desarrollo.proyectos_internos import (
    GestorProyectosInternos,
)

from src.atenas.cerebro.desarrollo.programador_objetivos import (
    ProgramadorObjetivosAutonomo,
)


class LLMFalso:

    def chat(
        self,
        mensajes,
    ):

        return json.dumps(
            {
                "lenguaje_principal": "python",

                "resumen": (
                    "Creé una solución real de prueba "
                    "dentro de Atenas-v1/data."
                ),

                "completado": True,

                "archivos": [
                    {
                        "ruta": "validador.py",
                        "lenguaje": "python",
                        "contenido": (
                            "def validar_comando(comando):\n"
                            "    if not isinstance(comando, str):\n"
                            "        return False\n"
                            "    return bool(comando.strip())\n"
                        ),
                    },
                    {
                        "ruta": "README.md",
                        "lenguaje": "markdown",
                        "contenido": (
                            "# Solución real de prueba\n\n"
                            "Este archivo fue creado por el "
                            "ProgramadorObjetivosAutonomo de ATENAS.\n"
                        ),
                    },
                    {
                        "ruta": "config.json",
                        "lenguaje": "json",
                        "contenido": (
                            '{\n'
                            '  "creado_por": "ATENAS",\n'
                            '  "tipo": "prueba_real"\n'
                            '}\n'
                        ),
                    },
                ],
            },
            ensure_ascii=False,
        )


class MapaFalso:

    def contexto_para_llm(
        self,
    ) -> str:

        return (
            "Proyecto ATENAS real. "
            "Prueba controlada de creación de archivos."
        )


class DesarrolloFalso:

    def __init__(
        self,
    ):
        self.mapa = MapaFalso()


def main():

    print()
    print("=" * 80)
    print(" PROGRAMADOR DE OBJETIVOS - PRUEBA REAL EN ATENAS-v1")
    print("=" * 80)

    # =========================================================
    # RAÍZ REAL DEL REPOSITORIO
    # =========================================================

    raiz = Path.cwd().resolve()

    if not (
        raiz / "src" / "atenas"
    ).exists():

        raise RuntimeError(
            "Ejecuta este test desde la raíz de Atenas-v1."
        )

    data_dir = (
        raiz
        / "data"
    )

    data_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Esta base queda realmente dentro de Atenas-v1/data.
    db_path = (
        data_dir
        / "test_programador_objetivos_real.db"
    )

    # Los archivos generados también quedan realmente en data.
    raiz_soluciones = (
        data_dir
        / "soluciones_objetivos_real"
    )

    gestor = (
        GestorProyectosInternos(
            db_path=db_path
        )
    )

    proyecto = (
        gestor.crear_proyecto(
            nombre=(
                "Prueba real de creación de archivos"
            ),
            descripcion=(
                "Comprobar que ATENAS puede crear "
                "una solución persistente dentro "
                "del repositorio real."
            ),
            origen="test_real",
            prioridad=1.0,
            autonomia=True,
            activar=True,
        )
    )

    objetivo = (
        gestor.agregar_objetivo(
            proyecto_id=proyecto.id,
            descripcion=(
                "Implementar un pequeño módulo "
                "Python para validar comandos."
            ),
            prioridad=1.0,
            orden=0,
        )
    )

    programador = (
        ProgramadorObjetivosAutonomo(
            llm=LLMFalso(),
            gestor=gestor,
            desarrollo=DesarrolloFalso(),
            raiz_soluciones=(
                raiz_soluciones
            ),
        )
    )

    resultado = (
        programador.programar_objetivo(
            proyecto=proyecto,
            objetivo=objetivo,
        )
    )

    print()
    print(
        "OK:",
        resultado.ok
    )

    print(
        "Completado:",
        resultado.completado
    )

    print(
        "Carpeta real:",
        resultado.carpeta_solucion
    )

    assert resultado.ok
    assert resultado.completado
    assert resultado.carpeta_solucion

    carpeta = Path(
        resultado.carpeta_solucion
    )

    archivos_esperados = [
        carpeta / "validador.py",
        carpeta / "README.md",
        carpeta / "config.json",
        carpeta / "manifest.json",
    ]

    print()
    print("-" * 80)
    print(" ARCHIVOS CREADOS REALMENTE")
    print("-" * 80)

    for archivo in archivos_esperados:

        existe = archivo.exists()

        print(
            f"{'SÍ' if existe else 'NO'} -> "
            f"{archivo}"
        )

        assert existe

    print()
    print("-" * 80)
    print(" VERIFICACIÓN CON PATH")
    print("-" * 80)

    print(
        "Directorio existe:",
        carpeta.exists()
    )

    print(
        "validador.py existe:",
        (
            carpeta
            / "validador.py"
        ).exists()
    )

    print()
    print("-" * 80)
    print(" COMANDOS POWERSHELL PARA VERLO")
    print("-" * 80)

    print()
    print(
        f'explorer "{carpeta}"'
    )

    print()
    print(
        f'Get-ChildItem -Recurse "{raiz_soluciones}"'
    )

    print()
    print("=" * 80)
    print(" TEST REAL CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()