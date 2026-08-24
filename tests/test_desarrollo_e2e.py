from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.atenas.cerebro.desarrollo.orquestador_desarrollo import (
    OrquestadorDesarrollo,
)


class LLMFalsoE2E:
    def __init__(self):
        self.llamadas = 0

    def chat(self, mensajes):
        self.llamadas += 1

        # 1. Análisis
        if self.llamadas == 1:
            return json.dumps({
                "nombre_proyecto": "Sistema Inventario E2E",
                "tipo_solucion": "web",
                "resumen": "Sistema web pequeño de inventario.",
                "actores": ["Administrador"],
                "requisitos_funcionales": [
                    {
                        "id": "RF-001",
                        "descripcion": "Gestionar productos.",
                        "prioridad": "alta",
                        "obligatorio": True
                    }
                ],
                "requisitos_no_funcionales": [
                    {
                        "id": "RNF-001",
                        "descripcion": "Mantener código modular.",
                        "prioridad": "media",
                        "obligatorio": True
                    }
                ],
                "entidades_negocio": ["Producto"],
                "integraciones": [],
                "restricciones": [],
                "necesita_base_datos": True,
                "necesita_autenticacion": False,
                "necesita_roles": False,
                "necesita_api": False,
                "necesita_archivos": False,
                "necesita_tiempo_real": False,
                "necesita_offline": False,
                "complejidad": "baja",
                "riesgos_iniciales": [],
                "preguntas_abiertas": []
            })

        # 2. Arquitectura
        if self.llamadas == 2:
            return json.dumps({
                "estilo": "monolito_modular",
                "tipo_solucion": "web",
                "frontend": None,
                "backend": {
                    "tecnologia": "Python",
                    "lenguaje": "Python"
                },
                "desktop": None,
                "movil": None,
                "embebido": None,
                "api": None,
                "base_datos": {
                    "motor": "SQLite"
                },
                "cache": None,
                "colas": None,
                "autenticacion": None,
                "componentes": [
                    {
                        "nombre": "inventario",
                        "responsabilidad": "Gestionar productos.",
                        "tecnologia": "Python",
                        "lenguaje": "Python",
                        "depende_de": []
                    }
                ],
                "despliegue": {
                    "tipo": "local"
                },
                "pruebas": {
                    "backend": "pytest"
                },
                "seguridad": [],
                "decisiones": [
                    "Arquitectura simple para alcance reducido."
                ]
            })

        # 3. Base de datos
        if self.llamadas == 3:
            return json.dumps({
                "motor": "sqlite",
                "nombre": "inventario",
                "tablas": [
                    {
                        "nombre": "productos",
                        "descripcion": "Productos del inventario.",
                        "campos": [
                            {
                                "nombre": "id",
                                "tipo": "integer",
                                "nullable": False,
                                "unique": True,
                                "default": None,
                                "descripcion": "Identificador."
                            },
                            {
                                "nombre": "nombre",
                                "tipo": "text",
                                "nullable": False,
                                "unique": False,
                                "default": None,
                                "descripcion": "Nombre."
                            }
                        ],
                        "clave_primaria": ["id"],
                        "indices": [["nombre"]]
                    }
                ],
                "relaciones": [],
                "decisiones": [
                    "SQLite por alcance pequeño."
                ],
                "estrategia_migraciones": "SQL versionado.",
                "estrategia_backup": "Copia del archivo de base de datos.",
                "estrategia_integridad": [
                    "PRIMARY KEY",
                    "NOT NULL"
                ]
            })

        # 4. Plan
        if self.llamadas == 4:
            return json.dumps({
                "fases": [
                    {
                        "id": "F1",
                        "nombre": "Implementación",
                        "objetivo": "Crear el módulo de productos.",
                        "orden": 1,
                        "epicas": [
                            {
                                "id": "E1",
                                "nombre": "Productos",
                                "descripcion": "Gestión básica.",
                                "prioridad": 1.0,
                                "tareas": [
                                    {
                                        "id": "T1",
                                        "titulo": "Crear servicio de productos",
                                        "descripcion": "Implementar alta y consulta.",
                                        "tipo": "backend",
                                        "prioridad": 1.0,
                                        "depende_de": [],
                                        "criterios_aceptacion": [
                                            "Agregar un producto.",
                                            "Consultar un producto."
                                        ],
                                        "archivos_estimados": [
                                            "src/productos.py"
                                        ],
                                        "lenguaje": "python",
                                        "tecnologia": "Python",
                                        "requiere_pruebas": True,
                                        "requiere_documentacion": True
                                    }
                                ]
                            }
                        ]
                    }
                ]
            })

        # 5. Programación de tarea
        return json.dumps({
            "resumen": "Implementé servicio y prueba.",
            "completado": True,
            "archivos": [
                {
                    "ruta": "src/productos.py",
                    "lenguaje": "python",
                    "contenido":
                        "class ProductosService:\n"
                        "    def __init__(self):\n"
                        "        self._items = {}\n"
                        "\n"
                        "    def agregar(self, producto_id, nombre):\n"
                        "        self._items[producto_id] = nombre\n"
                        "        return nombre\n"
                        "\n"
                        "    def obtener(self, producto_id):\n"
                        "        return self._items.get(producto_id)\n"
                },
                {
                    "ruta": "tests/test_productos.py",
                    "lenguaje": "python",
                    "contenido":
                        "from src.productos import ProductosService\n"
                        "\n"
                        "def test_productos():\n"
                        "    servicio = ProductosService()\n"
                        "    servicio.agregar(1, 'Teclado')\n"
                        "    assert servicio.obtener(1) == 'Teclado'\n"
                }
            ]
        })


def main():
    print()
    print("=" * 80)
    print(" DESARROLLO E2E - ATENAS")
    print("=" * 80)

    raiz = Path.cwd().resolve()

    proyecto = (
        raiz
        / "data"
        / "pruebas_desarrollo"
        / "e2e_desarrollo"
        / "proyecto"
    )

    planes = (
        raiz
        / "data"
        / "pruebas_desarrollo"
        / "e2e_desarrollo"
        / "planes"
    )

    if proyecto.exists():
        shutil.rmtree(proyecto)

    if planes.exists():
        shutil.rmtree(planes)

    proyecto.mkdir(parents=True, exist_ok=True)
    planes.mkdir(parents=True, exist_ok=True)

    llm = LLMFalsoE2E()

    orquestador = OrquestadorDesarrollo(
        llm=llm,
        raiz_planes=planes,
    )

    inicio = orquestador.iniciar(
        descripcion="Crear un sistema pequeño de inventario.",
        carpeta_proyecto=proyecto,
    )

    assert inicio.ok
    assert inicio.analisis is not None
    assert inicio.arquitectura is not None
    assert inicio.plan is not None

    resultados = orquestador.ejecutar_hasta_pausa(
        carpeta_proyecto=proyecto,
        proyecto_id=inicio.proyecto_id,
        analisis=inicio.analisis,
        arquitectura=inicio.arquitectura,
        modelo_bd=inicio.modelo_bd,
        plan=inicio.plan,
        max_ciclos=5,
    )

    ultimo = resultados[-1]

    print()
    print("Estado final:", ultimo.estado)
    print("Progreso:", ultimo.progreso)
    print("Plan completado:", ultimo.plan_completado)

    assert ultimo.ok
    assert ultimo.plan_completado
    assert ultimo.progreso == 100.0

    esperados = [
        proyecto / "src" / "productos.py",
        proyecto / "tests" / "test_productos.py",
        proyecto / "db" / "schema.sql",
        proyecto / "db" / "migrations" / "0001_initial.sql",
        proyecto / ".atenas" / "estado_proyecto.json",
        proyecto / ".atenas" / "analisis_requisitos.json",
        proyecto / ".atenas" / "arquitectura.json",
        proyecto / ".atenas" / "modelo_datos.json",
        proyecto / ".atenas" / "plan_software.json",
        proyecto / "docs" / "DOSSIER_PROYECTO.pdf",
    ]

    print()
    print("-" * 80)
    print(" ARTEFACTOS")
    print("-" * 80)

    for ruta in esperados:
        print(
            "SÍ" if ruta.exists() else "NO",
            "->",
            ruta,
        )
        assert ruta.exists()

    print()
    print("Proyecto persistente:", proyecto)
    print(f'explorer "{proyecto}"')

    print()
    print("=" * 80)
    print(" DESARROLLO V1 E2E CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()