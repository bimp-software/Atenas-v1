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


_CAPACIDADES: tuple[
    CapacidadAgente,
    ...
] = (
    CapacidadAgente(
        nombre="desarrollo_software",
        tipo=(
            TipoCapacidadAgente
            .DESARROLLO
        ),
        descripcion=(
            "Diseña, crea, continúa, valida, repara y documenta "
            "proyectos de software completos."
        ),
        acciones=(
            "crear_proyecto",
            "continuar_proyecto",
            "consultar_estado",
            "listar_proyectos",
        ),
        argumentos={
            "crear_proyecto": {
                "descripcion":
                    "str",

                "nombre_sugerido":
                    "str | None",

                "carpeta":
                    "str | None",
            },

            "continuar_proyecto": {
                "proyecto_id":
                    "str",

                "max_ciclos":
                    "int",
            },

            "consultar_estado": {
                "proyecto_id":
                    "str",
            },

            "listar_proyectos": {
                "solo_activos":
                    "bool",
            },
        },
        persistente=True,
        autonoma=True,
    ),

    CapacidadAgente(
        nombre="sistema_computador",
        tipo=(
            TipoCapacidadAgente
            .SISTEMA
        ),
        descripcion=(
            "Interactúa con el computador mediante acciones "
            "estructuradas y verificables, sin comandos shell libres."
        ),
        acciones=(
            "leer_texto",
            "listar_directorio",
            "crear_carpeta",
            "escribir_texto",
            "abrir_ruta",
            "abrir_aplicacion",
            "listar_procesos",
        ),
        argumentos={
            "leer_texto": {
                "ruta":
                    "str",
            },

            "listar_directorio": {
                "ruta":
                    "str",
            },

            "crear_carpeta": {
                "ruta":
                    "str",
            },

            "escribir_texto": {
                "ruta":
                    "str",

                "contenido":
                    "str",

                "sobrescribir":
                    "bool",
            },

            "abrir_ruta": {
                "ruta":
                    "str",
            },

            "abrir_aplicacion": {
                "alias":
                    "str",

                "argumentos":
                    "list[str]",
            },

            "listar_procesos": {},
        },
        persistente=False,
        autonoma=False,
        requiere_confirmacion_por_defecto=False,
    ),
)


def capacidades_disponibles(
    self=None,
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
    ).strip().lower()

    for capacidad in _CAPACIDADES:

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
    self=None,
) -> list[dict[str, Any]]:

    resultado = []

    for capacidad in _CAPACIDADES:

        datos = asdict(
            capacidad
        )

        datos[
            "tipo"
        ] = capacidad.tipo.value

        datos[
            "acciones"
        ] = list(
            capacidad.acciones
        )

        resultado.append(
            datos
        )

    return resultado