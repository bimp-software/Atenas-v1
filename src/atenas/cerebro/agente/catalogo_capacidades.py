from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TipoCapacidadAgente(str, Enum):
    DESARROLLO = "desarrollo"
    SISTEMA = "sistema"
    HERRAMIENTA = "herramienta"
    MEMORIA = "memoria"
    INVESTIGACION = "investigacion"


@dataclass(frozen=True)
class CapacidadAgente:
    nombre: str
    tipo: TipoCapacidadAgente
    descripcion: str

    acciones: tuple[str, ...] = ()

    argumentos: dict[str, Any] = field(
        default_factory=dict
    )

    persistente: bool = False
    autonoma: bool = False
    requiere_confirmacion_por_defecto: bool = False


_CAPACIDADES = (
    CapacidadAgente(
        nombre="desarrollo_software",
        tipo=TipoCapacidadAgente.DESARROLLO,
        descripcion=(
            "Diseña, crea, continúa, valida, repara "
            "y documenta proyectos de software."
        ),
        acciones=(
            "crear_proyecto",
            "continuar_proyecto",
            "consultar_estado",
            "listar_proyectos",
        ),
        persistente=True,
        autonoma=True,
    ),

    CapacidadAgente(
        nombre="sistema_computador",
        tipo=TipoCapacidadAgente.SISTEMA,
        descripcion=(
            "Interactúa con archivos, carpetas, aplicaciones, "
            "procesos y ventanas mediante acciones estructuradas."
        ),
        acciones=(
            "leer_texto",
            "listar_directorio",
            "crear_carpeta",
            "escribir_texto",
            "abrir_ruta",
            "abrir_aplicacion",
            "listar_procesos",
            "listar_ventanas",
            "ventana_activa",
            "activar_ventana",
            "minimizar_ventana",
            "maximizar_ventana",
            "restaurar_ventana",
            "posicion_mouse",
            "mover_mouse",
            "mover_mouse_ventana",
            "click_mouse",
            "doble_click_mouse",
            "click_mouse_ventana",
            "scroll_mouse",
            "escribir_teclado",
            "pulsar_tecla",
            "combinacion_teclas",
            "escribir_en_ventana",
            "combinacion_teclas_ventana",
            "capturar_pantalla",
            "capturar_ventana",
            "listar_capturas",
            "construir_estado_visual",
            "interpretar_escena",
            "estado_vision",
            "planificar_accion_gui",
            "ejecutar_accion_gui",
            "verificar_resultado_visual",
            "planificar_tarea_escritorio",
            "crear_tarea_escritorio",
            "crear_tarea_desde_objetivo",
            "replanificar_tarea_escritorio",
            "solicitar_confirmacion",
            "resolver_confirmacion",
            "consultar_confirmaciones",
            "consultar_actividad_agente",
            "consultar_estado_agente",
            "heartbeat_agente",
            "supervisar_sesion_autonoma",
            "crear_sesion_trabajo",
            "consultar_sesion_trabajo",
            "actualizar_sesion_trabajo",
            "consultar_contexto_operativo",
            "actualizar_contexto_operativo",
            "evaluar_replanificacion_tarea",
            "continuar_tarea_escritorio",
            "confirmar_paso_tarea_escritorio",
            "listar_tareas_escritorio",
        ),
        persistente=False,
        autonoma=False,
    ),
)


def capacidades_disponibles(
) -> list[CapacidadAgente]:

    return list(
        _CAPACIDADES
    )


def capacidad_por_nombre(
    nombre: str,
) -> CapacidadAgente | None:

    clave = (
        nombre
        or ""
    ).lower().strip()

    for capacidad in (
        _CAPACIDADES
    ):

        if (
            capacidad.nombre.lower()
            == clave
        ):
            return capacidad

    return None


def es_capacidad(
    nombre: str,
) -> bool:

    return (
        capacidad_por_nombre(
            nombre
        )
        is not None
    )


def catalogo_capacidades_para_llm(
) -> list[dict[str, Any]]:

    resultado = []

    for capacidad in (
        _CAPACIDADES
    ):

        datos = asdict(
            capacidad
        )

        datos["tipo"] = (
            capacidad.tipo.value
        )

        datos["acciones"] = list(
            capacidad.acciones
        )

        resultado.append(
            datos
        )

    return resultado