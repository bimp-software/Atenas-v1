from __future__ import annotations

import json

from pathlib import Path

from src.atenas.cerebro.desarrollo.analista_requisitos import (
    AnalisisRequisitos,
    TipoSolucion,
)

from src.atenas.cerebro.desarrollo.arquitecto_software import (
    ArquitecturaSoftware,
)

from src.atenas.cerebro.desarrollo.disenador_base_datos import (
    ModeloBaseDatos,
)

from src.atenas.cerebro.desarrollo.planificador_sistema_software import (
    EpicaSoftware,
    FaseSoftware,
    PlanSistemaSoftware,
    TareaSoftware,
)

from src.atenas.cerebro.desarrollo.programador_tarea_software import (
    ProgramadorTareaSoftware,
)

from src.atenas.cerebro.desarrollo.ejecutor_plan_software import (
    EjecutorPlanSoftware,
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

        if self.llamadas == 1:

            return json.dumps(
                {
                    "resumen":
                        "Creé el modelo de productos.",

                    "completado":
                        True,

                    "archivos": [
                        {
                            "ruta":
                                "src/models/product.py",

                            "lenguaje":
                                "python",

                            "contenido":
                                (
                                    "from dataclasses import dataclass\n"
                                    "\n"
                                    "@dataclass\n"
                                    "class Producto:\n"
                                    "    id: str\n"
                                    "    nombre: str\n"
                                    "    stock: int = 0\n"
                                ),
                        },
                        {
                            "ruta":
                                "tests/test_product.py",

                            "lenguaje":
                                "python",

                            "contenido":
                                (
                                    "from src.models.product import Producto\n"
                                    "\n"
                                    "\n"
                                    "def test_producto():\n"
                                    "    p = Producto('1', 'Teclado', 5)\n"
                                    "    assert p.stock == 5\n"
                                ),
                        },
                    ],
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "resumen":
                    "Creé el repositorio de productos.",

                "completado":
                    True,

                "archivos": [
                    {
                        "ruta":
                            "src/repositories/product_repository.py",

                        "lenguaje":
                            "python",

                        "contenido":
                            (
                                "class ProductRepository:\n"
                                "    def __init__(self):\n"
                                "        self._items = {}\n"
                                "\n"
                                "    def save(self, producto):\n"
                                "        self._items[producto.id] = producto\n"
                                "        return producto\n"
                                "\n"
                                "    def get(self, producto_id):\n"
                                "        return self._items.get(producto_id)\n"
                            ),
                    }
                ],
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" EJECUTOR INCREMENTAL DEL PLAN - ATENAS (PERSISTENTE)")
    print("=" * 80)

    # =========================================================
    # RAÍZ REAL DEL REPOSITORIO
    # =========================================================

    raiz_atenas = (
        Path.cwd()
        .resolve()
    )

    if not (
        raiz_atenas
        / "src"
        / "atenas"
    ).exists():

        raise RuntimeError(
            "Ejecuta este test desde la raíz "
            "del repositorio Atenas-v1."
        )

    # =========================================================
    # CARPETA PERSISTENTE
    # =========================================================

    carpeta_prueba = (
        raiz_atenas
        / "data"
        / "pruebas_desarrollo"
        / "ejecutor_plan_software"
    )

    proyecto = (
        carpeta_prueba
        / "proyecto"
    )

    proyecto.mkdir(
        parents=True,
        exist_ok=True,
    )

    # El plan se conserva físicamente dentro de Atenas-v1.
    ruta_plan = (
        carpeta_prueba
        / "plan.json"
    )

    # =========================================================
    # CONTEXTO DEL SISTEMA
    # =========================================================

    analisis = AnalisisRequisitos(
        nombre_proyecto="Sistema Comercial",
        tipo_solucion=TipoSolucion.WEB,
        resumen="Ventas e inventario.",
        necesita_base_datos=True,
        complejidad="alta",
    )

    arquitectura = ArquitecturaSoftware(
        estilo="monolito_modular",
        tipo_solucion="web",
        backend={
            "tecnologia":
                "FastAPI",

            "lenguaje":
                "Python",
        },
        base_datos={
            "motor":
                "PostgreSQL",
        },
    )

    modelo = ModeloBaseDatos(
        motor="postgresql",
        nombre="sistema_comercial",
    )

    # =========================================================
    # PLAN DE PRUEBA
    # =========================================================

    tarea_1 = TareaSoftware(
        id="T1",
        titulo="Crear modelo Producto",
        descripcion="Crear entidad Producto.",
        tipo="base_datos",
        prioridad=1.0,
        archivos_estimados=[
            "src/models/product.py"
        ],
        lenguaje="python",
        tecnologia="dataclasses",
        requiere_pruebas=True,
    )

    tarea_2 = TareaSoftware(
        id="T2",
        titulo="Crear repositorio Producto",
        descripcion="Crear repositorio.",
        tipo="backend",
        prioridad=0.9,
        depende_de=[
            "T1"
        ],
        archivos_estimados=[
            "src/repositories/product_repository.py"
        ],
        lenguaje="python",
        requiere_pruebas=False,
    )

    plan = PlanSistemaSoftware(
        id="PLAN-1",
        nombre_proyecto="Sistema Comercial",
        tipo_solucion="web",
        arquitectura="monolito_modular",
        complejidad="alta",
        fases=[
            FaseSoftware(
                id="F1",
                nombre="Base",
                objetivo="Persistencia",
                orden=1,
                epicas=[
                    EpicaSoftware(
                        id="E1",
                        nombre="Datos",
                        descripcion="Persistencia",
                        prioridad=1.0,
                        tareas=[
                            tarea_1,
                            tarea_2,
                        ],
                    )
                ],
            )
        ],
    )

    plan.ruta_persistencia = str(
        ruta_plan
    )

    # =========================================================
    # EJECUTOR
    # =========================================================

    programador = (
        ProgramadorTareaSoftware(
            llm=LLMFalso()
        )
    )

    ejecutor = (
        EjecutorPlanSoftware(
            programador=programador
        )
    )

    # =========================================================
    # PRIMERA TAREA
    # =========================================================

    resultado_1 = (
        ejecutor
        .ejecutar_siguiente(
            carpeta_proyecto=proyecto,
            analisis=analisis,
            arquitectura=arquitectura,
            modelo_bd=modelo,
            plan=plan,
        )
    )

    print()
    print(
        "Primera:",
        resultado_1.tarea.titulo
    )

    print(
        "Estado:",
        resultado_1.estado
    )

    assert resultado_1.ok

    archivo_modelo = (
        proyecto
        / "src"
        / "models"
        / "product.py"
    )

    archivo_test = (
        proyecto
        / "tests"
        / "test_product.py"
    )

    assert archivo_modelo.exists()
    assert archivo_test.exists()

    # =========================================================
    # SEGUNDA TAREA
    # =========================================================

    resultado_2 = (
        ejecutor
        .ejecutar_siguiente(
            carpeta_proyecto=proyecto,
            analisis=analisis,
            arquitectura=arquitectura,
            modelo_bd=modelo,
            plan=plan,
        )
    )

    print()
    print(
        "Segunda:",
        resultado_2.tarea.titulo
    )

    print(
        "Estado:",
        resultado_2.estado
    )

    assert resultado_2.ok

    archivo_repo = (
        proyecto
        / "src"
        / "repositories"
        / "product_repository.py"
    )

    assert archivo_repo.exists()
    assert resultado_2.plan_completado
    assert ruta_plan.exists()

    # =========================================================
    # VERIFICACIÓN PERSISTENTE
    # =========================================================

    print()
    print("-" * 80)
    print(" ARCHIVOS PERSISTENTES")
    print("-" * 80)

    archivos = [
        ruta_plan,
        archivo_modelo,
        archivo_test,
        archivo_repo,
    ]

    for archivo in archivos:

        print(
            (
                "SÍ"
                if archivo.exists()
                else "NO"
            ),
            "->",
            archivo,
        )

        assert archivo.exists()

    print()
    print(
        "Plan completado:",
        resultado_2.plan_completado
    )

    print(
        "Plan persistido:",
        ruta_plan
    )

    print(
        "Proyecto persistido:",
        proyecto
    )

    print()
    print("-" * 80)
    print(" ABRIR CARPETA EN WINDOWS")
    print("-" * 80)

    print()
    print(
        f'explorer "{carpeta_prueba}"'
    )

    print()
    print("=" * 80)
    print(" TEST CORRECTO Y PERSISTENTE")
    print("=" * 80)


if __name__ == "__main__":
    main()