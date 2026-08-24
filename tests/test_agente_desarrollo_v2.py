from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.atenas.cerebro.agente.agente import (
    AgenteAtenas,
)

from src.atenas.cerebro.agente.capacidad_desarrollo import (
    CapacidadDesarrollo,
)

from src.atenas.cerebro.agente.decision_engine import (
    TipoDecisionAgente,
)


class LLMFalsoAgente:
    """
    LLM determinista para probar el ciclo completo:

    mensaje
    -> necesidad de software
    -> pendiente
    -> decisión CREAR_PROYECTO
    -> desarrollo
    -> persistencia
    -> reinicio
    -> restauración
    -> continuación autónoma
    -> proyecto completado
    """

    def __init__(self):
        self.llamadas = 0

    def chat(self, mensajes):
        self.llamadas += 1

        # -----------------------------------------------------
        # 1. Análisis de requisitos
        # -----------------------------------------------------
        if self.llamadas == 1:
            return json.dumps({
                "nombre_proyecto": "Inventario Agente V2",
                "tipo_solucion": "web",
                "resumen": (
                    "Sistema web simple para administrar "
                    "productos de inventario."
                ),
                "actores": [
                    "Administrador"
                ],
                "requisitos_funcionales": [
                    {
                        "id": "RF-001",
                        "descripcion": "Registrar productos.",
                        "prioridad": "alta",
                        "obligatorio": True
                    }
                ],
                "requisitos_no_funcionales": [
                    {
                        "id": "RNF-001",
                        "descripcion": "Código modular.",
                        "prioridad": "media",
                        "obligatorio": True
                    }
                ],
                "entidades_negocio": [
                    "Producto"
                ],
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

        # -----------------------------------------------------
        # 2. Arquitectura
        # -----------------------------------------------------
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
                        "nombre": "productos",
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
                    "Arquitectura mínima para el alcance."
                ]
            })

        # -----------------------------------------------------
        # 3. Base de datos
        # -----------------------------------------------------
        if self.llamadas == 3:
            return json.dumps({
                "motor": "sqlite",
                "nombre": "inventario_agente",
                "tablas": [
                    {
                        "nombre": "productos",
                        "descripcion": "Productos.",
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
                        "clave_primaria": [
                            "id"
                        ],
                        "indices": [
                            [
                                "nombre"
                            ]
                        ]
                    }
                ],
                "relaciones": [],
                "decisiones": [
                    "SQLite para una prueba local."
                ],
                "estrategia_migraciones": "SQL versionado.",
                "estrategia_backup": "Copia del archivo.",
                "estrategia_integridad": [
                    "PRIMARY KEY",
                    "NOT NULL"
                ]
            })

        # -----------------------------------------------------
        # 4. Plan
        # Dos tareas para demostrar que tras reiniciar puede
        # continuar la segunda.
        # -----------------------------------------------------
        if self.llamadas == 4:
            return json.dumps({
                "fases": [
                    {
                        "id": "F1",
                        "nombre": "Implementación",
                        "objetivo": "Crear núcleo del inventario.",
                        "orden": 1,
                        "epicas": [
                            {
                                "id": "E1",
                                "nombre": "Productos",
                                "descripcion": "CRUD mínimo.",
                                "prioridad": 1.0,
                                "tareas": [
                                    {
                                        "id": "T1",
                                        "titulo": "Crear modelo de producto",
                                        "descripcion": "Crear entidad Producto.",
                                        "tipo": "backend",
                                        "prioridad": 1.0,
                                        "depende_de": [],
                                        "criterios_aceptacion": [
                                            "Producto conserva id y nombre."
                                        ],
                                        "archivos_estimados": [
                                            "src/producto.py"
                                        ],
                                        "lenguaje": "python",
                                        "tecnologia": "Python",
                                        "requiere_pruebas": True,
                                        "requiere_documentacion": True
                                    },
                                    {
                                        "id": "T2",
                                        "titulo": "Crear servicio de productos",
                                        "descripcion": (
                                            "Crear servicio para registrar "
                                            "y consultar productos."
                                        ),
                                        "tipo": "backend",
                                        "prioridad": 0.9,
                                        "depende_de": [
                                            "T1"
                                        ],
                                        "criterios_aceptacion": [
                                            "Registrar producto.",
                                            "Consultar producto."
                                        ],
                                        "archivos_estimados": [
                                            "src/servicio_productos.py"
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

        # -----------------------------------------------------
        # 5. Programación T1
        # -----------------------------------------------------
        if self.llamadas == 5:
            return json.dumps({
                "resumen": "Creé el modelo Producto.",
                "completado": True,
                "archivos": [
                    {
                        "ruta": "src/producto.py",
                        "lenguaje": "python",
                        "contenido":
                            "class Producto:\n"
                            "    def __init__(self, producto_id, nombre):\n"
                            "        self.id = producto_id\n"
                            "        self.nombre = nombre\n"
                    },
                    {
                        "ruta": "tests/test_producto.py",
                        "lenguaje": "python",
                        "contenido":
                            "from src.producto import Producto\n"
                            "\n"
                            "def test_producto():\n"
                            "    p = Producto(1, 'Mouse')\n"
                            "    assert p.id == 1\n"
                            "    assert p.nombre == 'Mouse'\n"
                    }
                ]
            })

        # -----------------------------------------------------
        # 6. Programación T2 después del reinicio
        # -----------------------------------------------------
        return json.dumps({
            "resumen": "Creé el servicio de productos.",
            "completado": True,
            "archivos": [
                {
                    "ruta": "src/servicio_productos.py",
                    "lenguaje": "python",
                    "contenido":
                        "from src.producto import Producto\n"
                        "\n"
                        "class ServicioProductos:\n"
                        "    def __init__(self):\n"
                        "        self._items = {}\n"
                        "\n"
                        "    def registrar(self, producto_id, nombre):\n"
                        "        producto = Producto(producto_id, nombre)\n"
                        "        self._items[producto_id] = producto\n"
                        "        return producto\n"
                        "\n"
                        "    def obtener(self, producto_id):\n"
                        "        return self._items.get(producto_id)\n"
                },
                {
                    "ruta": "tests/test_servicio_productos.py",
                    "lenguaje": "python",
                    "contenido":
                        "from src.servicio_productos import ServicioProductos\n"
                        "\n"
                        "def test_servicio_productos():\n"
                        "    servicio = ServicioProductos()\n"
                        "    servicio.registrar(1, 'Teclado')\n"
                        "    assert servicio.obtener(1).nombre == 'Teclado'\n"
                }
            ]
        })


class StorageFalso:
    """
    Sustituye únicamente las piezas que el agente necesita para esta
    prueba. La persistencia real del agente sigue siendo responsabilidad
    de PersistenciaAgente en producción.
    """

    class DB:
        pass

    class Vectores:
        def buscar(self, *args, **kwargs):
            return []

    class Grafo:
        def buscar_relacionado(self, *args, **kwargs):
            return []

    def __init__(self):
        self.db = self.DB()
        self.vectores = self.Vectores()
        self.grafo = self.Grafo()


class PersistenciaMemoria:
    """
    Persistencia mínima para aislar esta prueba del SQLite principal.
    """

    def __init__(self):
        self.objetivos = []
        self.pendientes = []

    def cargar_objetivos(self):
        return self.objetivos

    def cargar_pendientes(self):
        return self.pendientes

    def guardar_objetivo(self, objetivo):
        existentes = [
            item
            for item in self.objetivos
            if item.id != objetivo.id
        ]
        existentes.append(objetivo)
        self.objetivos = existentes

    def guardar_pendiente(self, pendiente):
        existentes = [
            item
            for item in self.pendientes
            if item.id != pendiente.id
        ]
        existentes.append(pendiente)
        self.pendientes = existentes

    def registrar_accion(self, **kwargs):
        return None


def construir_agente(
    llm,
    raiz_datos,
    raiz_proyectos,
    persistencia_prueba,
):
    """
    Crea AgenteAtenas y aísla objetivos/pendientes del estado productivo.

    CapacidadDesarrollo sí persiste en disco porque precisamente queremos
    comprobar restauración real después de reiniciar.
    """

    capacidad = CapacidadDesarrollo(
        llm=llm,
        raiz_datos=raiz_datos,
        raiz_proyectos=raiz_proyectos,
    )

    agente = AgenteAtenas(
        capacidad_desarrollo=capacidad
    )

    # Aislar memoria operativa de objetivos/pendientes del SQLite real.
    from src.atenas.cerebro.agente.objetivos import GestorObjetivos
    from src.atenas.cerebro.agente.pendientes import GestorPendientes

    agente.objetivos = GestorObjetivos()
    agente.pendientes = GestorPendientes()
    agente.persistencia = persistencia_prueba

    agente.objetivos.cargar(
        persistencia_prueba.cargar_objetivos()
    )

    agente.pendientes.cargar(
        persistencia_prueba.cargar_pendientes()
    )

    # Evitar que la prueba dependa de memoria vectorial/grafo productivo.
    storage_falso = StorageFalso()
    agente.detector_necesidades.storage = storage_falso

    # Forzar el mismo LLM determinista en Desarrollo.
    agente.planificador.llm = llm
    agente.capacidad_desarrollo.llm = llm
    agente.capacidad_desarrollo.orquestador.llm = llm

    return agente


def main():

    print()
    print("=" * 80)
    print(" AGENTE V2 + DESARROLLO AUTÓNOMO - ATENAS")
    print("=" * 80)

    raiz = Path.cwd().resolve()

    base = (
        raiz
        / "data"
        / "pruebas_agente"
        / "agente_desarrollo_v2"
    )

    raiz_datos = (
        base
        / "datos"
    )

    raiz_proyectos = (
        base
        / "proyectos"
    )

    if base.exists():
        shutil.rmtree(
            base
        )

    raiz_datos.mkdir(
        parents=True,
        exist_ok=True,
    )

    raiz_proyectos.mkdir(
        parents=True,
        exist_ok=True,
    )

    llm = LLMFalsoAgente()
    persistencia_prueba = PersistenciaMemoria()

    # =========================================================
    # PRIMERA EJECUCIÓN
    # =========================================================

    agente = construir_agente(
        llm=llm,
        raiz_datos=raiz_datos,
        raiz_proyectos=raiz_proyectos,
        persistencia_prueba=persistencia_prueba,
    )

    mensaje = (
        "Necesito crear un sistema web para administrar "
        "productos de inventario."
    )

    print()
    print("Usuario:", mensaje)

    pendientes = agente.observar(
        mensaje
    )

    print()
    print(
        "Pendientes creados:",
        len(
            pendientes
        )
    )

    assert pendientes

    pendiente = pendientes[0]

    print(
        "Acción sugerida:",
        pendiente.accion_sugerida
    )

    assert (
        pendiente.accion_sugerida
        == "desarrollo_software:crear_proyecto"
    )

    pensamiento = agente.pensar(
        permitir_iniciativa_desarrollo=True
    )

    decision = pensamiento[
        "decision"
    ]

    print()
    print(
        "Decisión:",
        decision.tipo
    )

    assert (
        decision.tipo
        == TipoDecisionAgente.CREAR_PROYECTO
    )

    creacion = agente.actuar(
        permitir_iniciativa_desarrollo=True
    )

    print()
    print(
        "Proyecto creado:",
        creacion.get(
            "proyecto_id"
        )
    )

    print(
        "Éxito:",
        creacion.get(
            "exito"
        )
    )

    assert creacion[
        "exito"
    ]

    proyecto_id = creacion[
        "proyecto_id"
    ]

    assert proyecto_id

    # Un ciclo explícito para completar T1 antes del reinicio.
    primer_avance = (
        agente
        .continuar_proyecto_software(
            proyecto_id=proyecto_id,
            max_ciclos=1,
        )
    )

    print()
    print(
        "Primer avance:",
        primer_avance.estado
    )

    print(
        "Progreso:",
        primer_avance.progreso
    )

    assert primer_avance.ok
    assert (
        primer_avance.progreso
        < 100.0
    )

    # =========================================================
    # SIMULAR REINICIO
    # =========================================================

    print()
    print("-" * 80)
    print(" REINICIO SIMULADO")
    print("-" * 80)

    agente = construir_agente(
        llm=llm,
        raiz_datos=raiz_datos,
        raiz_proyectos=raiz_proyectos,
        persistencia_prueba=persistencia_prueba,
    )

    listado = (
        agente
        .proyectos_software(
            solo_activos=True
        )
    )

    proyectos = listado.datos[
        "proyectos"
    ]

    print()
    print(
        "Proyectos restaurados:",
        len(
            proyectos
        )
    )

    assert proyectos

    ids = {
        item[
            "id"
        ]
        for item in proyectos
    }

    assert proyecto_id in ids

    # =========================================================
    # INICIATIVA DESPUÉS DEL REINICIO
    # =========================================================

    pensamiento_2 = (
        agente.pensar(
            permitir_iniciativa_desarrollo=True
        )
    )

    decision_2 = (
        pensamiento_2[
            "decision"
        ]
    )

    print()
    print(
        "Decisión después del reinicio:",
        decision_2.tipo
    )

    assert (
        decision_2.tipo
        == TipoDecisionAgente.CONTINUAR_PROYECTO
    )

    accion_2 = agente.actuar(
        permitir_iniciativa_desarrollo=True
    )

    print(
        "Acción autónoma:",
        accion_2.get(
            "accion_capacidad"
        )
    )

    print(
        "Éxito:",
        accion_2.get(
            "exito"
        )
    )

    print(
        "Progreso final:",
        accion_2.get(
            "progreso"
        )
    )

    assert accion_2[
        "exito"
    ]

    assert (
        accion_2[
            "progreso"
        ]
        == 100.0
    )

    # =========================================================
    # ARTEFACTOS
    # =========================================================

    estado = (
        agente.capacidad_desarrollo
        .estado_proyecto(
            proyecto_id
        )
    )

    proyecto = Path(
        estado.carpeta
    )

    esperados = [
        proyecto / "src" / "producto.py",
        proyecto / "src" / "servicio_productos.py",
        proyecto / "tests" / "test_producto.py",
        proyecto / "tests" / "test_servicio_productos.py",
        proyecto / "db" / "schema.sql",
        proyecto / ".atenas" / "estado_proyecto.json",
        proyecto / ".atenas" / "plan_software.json",
        proyecto / "docs" / "DOSSIER_PROYECTO.pdf",
    ]

    print()
    print("-" * 80)
    print(" ARTEFACTOS")
    print("-" * 80)

    for ruta in esperados:

        existe = ruta.exists()

        print(
            "SÍ" if existe else "NO",
            "->",
            ruta,
        )

        assert existe

    print()
    print(
        "Proyecto:",
        proyecto
    )

    print(
        f'explorer "{proyecto}"'
    )

    print()
    print("=" * 80)
    print(" AGENTE V2 + DESARROLLO: TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()