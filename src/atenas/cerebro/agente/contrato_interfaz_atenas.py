from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PaginaAtenas(str, Enum):
    CHAT = "chat"
    ESTADO = "estado"
    PROYECTOS = "proyectos"
    TAREAS = "tareas"
    SESIONES = "sesiones"
    DOCUMENTOS = "documentos"
    CONFIRMACIONES = "confirmaciones"
    ACTIVIDAD = "actividad"
    EMPRESA = "empresa"
    CONFIGURACION = "configuracion"


@dataclass
class ModuloPagina:
    pagina: PaginaAtenas
    titulo: str
    descripcion: str
    recursos: list[str] = field(default_factory=list)


class ContratoInterfazAtenas:
    """
    Define las páginas base de la futura interfaz.

    No contiene HTML ni depende de React/Vue/FastAPI.
    Es un contrato estable entre el agente y la futura web.
    """

    @staticmethod
    def paginas() -> list[ModuloPagina]:
        return [
            ModuloPagina(
                PaginaAtenas.CHAT,
                "Chat",
                "Conversación principal con ATENAS.",
                [
                    "mensajes",
                    "archivos_adjuntos",
                    "estado_resumido",
                ],
            ),
            ModuloPagina(
                PaginaAtenas.ESTADO,
                "Estado",
                "Estado operativo en tiempo real.",
                [
                    "estado_agente",
                    "sesion_actual",
                    "tarea_actual",
                    "progreso",
                    "ultimo_error",
                ],
            ),
            ModuloPagina(
                PaginaAtenas.PROYECTOS,
                "Proyectos",
                "Proyectos internos, personales y de clientes.",
                [
                    "proyectos",
                    "planes",
                    "artefactos",
                ],
            ),
            ModuloPagina(
                PaginaAtenas.TAREAS,
                "Tareas",
                "Trabajo planificado y autónomo.",
                [
                    "pendientes",
                    "en_progreso",
                    "bloqueadas",
                    "completadas",
                ],
            ),
            ModuloPagina(
                PaginaAtenas.SESIONES,
                "Sesiones",
                "Objetivos superiores y continuidad de trabajo.",
                [
                    "sesion_activa",
                    "historial_sesiones",
                ],
            ),
            ModuloPagina(
                PaginaAtenas.DOCUMENTOS,
                "Documentos",
                "PDF, texto, documentación y conocimiento importado.",
                [
                    "documentos",
                    "buscar_documentos",
                    "fragmentos",
                ],
            ),
            ModuloPagina(
                PaginaAtenas.CONFIRMACIONES,
                "Confirmaciones",
                "Acciones que requieren aprobación humana.",
                [
                    "pendientes",
                    "aprobar",
                    "rechazar",
                ],
            ),
            ModuloPagina(
                PaginaAtenas.ACTIVIDAD,
                "Actividad",
                "Historial estructurado de acciones y decisiones.",
                [
                    "eventos",
                    "errores",
                    "decisiones",
                ],
            ),
            ModuloPagina(
                PaginaAtenas.EMPRESA,
                "Empresa",
                "Puente futuro con BIMP Software.",
                [
                    "clientes",
                    "contratos",
                    "proyectos_cliente",
                    "entregas",
                    "facturacion_futura",
                ],
            ),
            ModuloPagina(
                PaginaAtenas.CONFIGURACION,
                "Configuración",
                "Modelos, autonomía, rutas y conexiones.",
                [
                    "ollama",
                    "vision",
                    "autonomia",
                    "directorios",
                    "integraciones",
                ],
            ),
        ]

    @classmethod
    def como_dict(
        cls,
    ) -> list[dict[str, Any]]:
        return [
            {
                "pagina":
                    modulo.pagina.value,

                "titulo":
                    modulo.titulo,

                "descripcion":
                    modulo.descripcion,

                "recursos":
                    modulo.recursos,
            }
            for modulo in cls.paginas()
        ]