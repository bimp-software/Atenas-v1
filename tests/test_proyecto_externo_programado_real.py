from __future__ import annotations

import json
from pathlib import Path

from src.atenas.cerebro.proyectos_externos.espacios_trabajo import (
    GestorEspaciosTrabajo,
)

from src.atenas.cerebro.proyectos_externos.creador_proyecto_externo import (
    CreadorProyectosExternos,
)


class LLMFalso:

    def __init__(
        self,
    ):
        self.llamadas = 0

    def chat(
        self,
        mensajes,
    ):

        self.llamadas += 1

        # Primera llamada: clasificación.
        if self.llamadas == 1:

            return json.dumps(
                {
                    "tipo":
                        "cliente",

                    "nombre":
                        "Portal Inventario ATENAS Programado",

                    "cliente":
                        "Cliente Demo",

                    "lenguaje_sugerido":
                        "python",

                    "necesita_pdf":
                        True,

                    "confianza":
                        0.99,

                    "motivo":
                        "Proyecto de cliente.",
                },
                ensure_ascii=False,
            )

        # Segunda llamada: programación de la solución.
        return json.dumps(
            {
                "lenguaje_principal":
                    "python",

                "resumen":
                    "Generé una API mínima de inventario "
                    "con modelo en memoria y pruebas.",

                "completado":
                    True,

                "archivos": [
                    {
                        "ruta":
                            "src/inventario.py",

                        "lenguaje":
                            "python",

                        "contenido":
                            (
                                "class Inventario:\n"
                                "    def __init__(self):\n"
                                "        self.productos = {}\n"
                                "\n"
                                "    def agregar(self, codigo, nombre, stock=0):\n"
                                "        self.productos[codigo] = {\n"
                                "            'nombre': nombre,\n"
                                "            'stock': int(stock),\n"
                                "        }\n"
                                "        return self.productos[codigo]\n"
                                "\n"
                                "    def obtener(self, codigo):\n"
                                "        return self.productos.get(codigo)\n"
                                "\n"
                                "    def listar(self):\n"
                                "        return dict(self.productos)\n"
                            ),
                    },
                    {
                        "ruta":
                            "tests/test_inventario.py",

                        "lenguaje":
                            "python",

                        "contenido":
                            (
                                "from src.inventario import Inventario\n"
                                "\n"
                                "\n"
                                "def test_agregar_producto():\n"
                                "    inv = Inventario()\n"
                                "    producto = inv.agregar('A1', 'Teclado', 5)\n"
                                "    assert producto['stock'] == 5\n"
                                "    assert inv.obtener('A1')['nombre'] == 'Teclado'\n"
                            ),
                    },
                    {
                        "ruta":
                            "requirements.txt",

                        "lenguaje":
                            "text",

                        "contenido":
                            "pytest\n",
                    },
                ],
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" PROYECTO EXTERNO REAL + PROGRAMACIÓN - ATENAS")
    print("=" * 80)

    raiz_atenas = Path.cwd().resolve()

    config = (
        raiz_atenas
        / "data"
        / "espacios_trabajo.json"
    )

    espacios = (
        GestorEspaciosTrabajo(
            config_path=config
        )
    )

    creador = (
        CreadorProyectosExternos(
            llm=LLMFalso(),
            espacios=espacios,
        )
    )

    resultado = (
        creador.crear(
            descripcion=(
                "Crear un portal de inventario "
                "para Cliente Demo con usuarios, "
                "productos y reportes."
            ),
            objetivos=[
                "Gestionar productos.",
                "Consultar inventario.",
                "Preparar pruebas.",
            ],
            requisitos=[
                "Código organizado.",
                "Pruebas automatizadas.",
            ],
            arquitectura=[
                "Código fuente en src.",
                "Pruebas en tests.",
            ],
            entregables=[
                "Código fuente.",
                "Documentación.",
                "PDF.",
            ],
            pruebas=[
                "Pruebas unitarias.",
            ],
            programar_solucion=True,
        )
    )

    print()
    print(
        "OK:",
        resultado.ok
    )

    print(
        "Carpeta:",
        resultado.carpeta
    )

    assert resultado.ok
    assert resultado.programacion is not None
    assert resultado.programacion.ok

    carpeta = Path(
        resultado.carpeta
    )

    esperados = [
        carpeta / "src" / "inventario.py",
        carpeta / "tests" / "test_inventario.py",
        carpeta / "requirements.txt",
        carpeta / "README.md",
        carpeta / "ESPECIFICACIONES.md",
        carpeta / "proyecto.json",
        carpeta / "ATENAS_GENERACION.json",
    ]

    if resultado.pdf_generado:

        esperados.append(
            carpeta
            / "ESPECIFICACIONES.pdf"
        )

    print()
    print("-" * 80)
    print(" SOLUCIÓN PROGRAMADA")
    print("-" * 80)

    for ruta in esperados:

        existe = ruta.exists()

        print(
            (
                "SÍ"
                if existe
                else "NO"
            ),
            "->",
            ruta,
        )

        assert existe

    print()
    print(
        "Lenguaje:",
        resultado.programacion
        .lenguaje_principal
    )

    print(
        "Completado:",
        resultado.programacion
        .completado
    )

    print(
        "Resumen:",
        resultado.programacion
        .resumen
    )

    print()
    print(
        f'explorer "{carpeta}"'
    )

    print()
    print("=" * 80)
    print(" TEST REAL CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()