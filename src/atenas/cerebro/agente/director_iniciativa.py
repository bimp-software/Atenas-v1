from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .capacidad_desarrollo import CapacidadDesarrollo
from .pendientes import GestorPendientes
from .registro_tareas_escritorio import RegistroTareasEscritorio
from .tareas_escritorio import EstadoTareaEscritorio


class TipoTrabajoAgente(str, Enum):
    NADA = "nada"
    PENDIENTE = "pendiente"
    PROYECTO = "proyecto"
    TAREA_ESCRITORIO = "tarea_escritorio"


@dataclass
class TrabajoCandidato:
    tipo: TipoTrabajoAgente
    id: str | None
    descripcion: str = ""
    prioridad: float = 0.0
    confianza: float = 0.0
    urgencia: float = 0.0
    continuidad: float = 0.0
    bloqueado: bool = False
    score: float = 0.0
    metadata: dict[str, Any] | None = None


class DirectorIniciativaAgente:
    """
    Director general de trabajo autónomo.

    Compara pendientes, proyectos y tareas de escritorio y devuelve
    el trabajo ejecutable con mayor score.
    """

    def __init__(
        self,
        registro_tareas: RegistroTareasEscritorio | None = None,
    ):
        self.registro_tareas = (
            registro_tareas
            or RegistroTareasEscritorio()
        )

    @staticmethod
    def _score(
        prioridad: float,
        confianza: float,
        urgencia: float,
        continuidad: float,
    ) -> float:
        return round(
            min(
                1.0,
                prioridad * 0.45
                + confianza * 0.20
                + urgencia * 0.15
                + continuidad * 0.20,
            ),
            4,
        )

    def _candidatos_pendientes(
        self,
        pendientes: GestorPendientes,
    ) -> list[TrabajoCandidato]:
        salida = []

        for pendiente in pendientes.pendientes():
            prioridad = float(
                getattr(pendiente, "prioridad", 0.60) or 0.60
            )
            confianza = float(
                getattr(pendiente, "confianza", 0.70) or 0.70
            )
            urgencia = 0.55
            continuidad = 0.30

            salida.append(
                TrabajoCandidato(
                    tipo=TipoTrabajoAgente.PENDIENTE,
                    id=pendiente.id,
                    descripcion=(
                        getattr(pendiente, "descripcion", "")
                        or ""
                    ),
                    prioridad=prioridad,
                    confianza=confianza,
                    urgencia=urgencia,
                    continuidad=continuidad,
                    score=self._score(
                        prioridad,
                        confianza,
                        urgencia,
                        continuidad,
                    ),
                    metadata={
                        "accion_sugerida": getattr(
                            pendiente,
                            "accion_sugerida",
                            None,
                        )
                    },
                )
            )

        return salida

    def _candidatos_proyectos(
        self,
        capacidad_desarrollo: CapacidadDesarrollo | None,
    ) -> list[TrabajoCandidato]:
        if capacidad_desarrollo is None:
            return []

        try:
            proyectos = capacidad_desarrollo.listar_proyectos(
                solo_activos=True
            )
        except Exception:
            return []

        salida = []

        for proyecto in proyectos or []:
            if isinstance(proyecto, dict):
                proyecto_id = (
                    proyecto.get("id")
                    or proyecto.get("proyecto_id")
                )
                prioridad = float(
                    proyecto.get("prioridad", 0.72) or 0.72
                )
                progreso = float(
                    proyecto.get("progreso", 0.0) or 0.0
                )
                descripcion = str(
                    proyecto.get(
                        "nombre",
                        proyecto.get(
                            "descripcion",
                            "Proyecto de software",
                        ),
                    )
                )
            else:
                proyecto_id = getattr(proyecto, "id", None)
                prioridad = float(
                    getattr(proyecto, "prioridad", 0.72)
                    or 0.72
                )
                progreso = float(
                    getattr(proyecto, "progreso", 0.0)
                    or 0.0
                )
                descripcion = str(
                    getattr(proyecto, "nombre", None)
                    or getattr(
                        proyecto,
                        "descripcion",
                        "Proyecto de software",
                    )
                )

            if not proyecto_id:
                continue

            continuidad = 0.90 if progreso > 0.0 else 0.55
            urgencia = 0.60
            confianza = 0.92

            salida.append(
                TrabajoCandidato(
                    tipo=TipoTrabajoAgente.PROYECTO,
                    id=str(proyecto_id),
                    descripcion=descripcion,
                    prioridad=prioridad,
                    confianza=confianza,
                    urgencia=urgencia,
                    continuidad=continuidad,
                    score=self._score(
                        prioridad,
                        confianza,
                        urgencia,
                        continuidad,
                    ),
                    metadata={"progreso": progreso},
                )
            )

        return salida

    def _candidatos_tareas_escritorio(
        self,
    ) -> list[TrabajoCandidato]:
        salida = []

        for tarea in self.registro_tareas.pendientes():
            if tarea.estado == EstadoTareaEscritorio.REQUIERE_CONFIRMACION:
                continue

            if tarea.estado in {
                EstadoTareaEscritorio.COMPLETADA,
                EstadoTareaEscritorio.FALLIDA,
            }:
                continue

            progreso = tarea.progreso
            prioridad = float(tarea.prioridad)
            confianza = 0.93
            urgencia = 0.68
            continuidad = 0.95 if progreso > 0.0 else 0.65

            salida.append(
                TrabajoCandidato(
                    tipo=TipoTrabajoAgente.TAREA_ESCRITORIO,
                    id=tarea.id,
                    descripcion=tarea.nombre,
                    prioridad=prioridad,
                    confianza=confianza,
                    urgencia=urgencia,
                    continuidad=continuidad,
                    score=self._score(
                        prioridad,
                        confianza,
                        urgencia,
                        continuidad,
                    ),
                    metadata={
                        "estado": tarea.estado.value,
                        "progreso": progreso,
                        "paso_actual": tarea.paso_actual,
                    },
                )
            )

        return salida

    def elegir(
        self,
        pendientes: GestorPendientes,
        capacidad_desarrollo: CapacidadDesarrollo | None = None,
        permitir_proyectos: bool = True,
        permitir_tareas_escritorio: bool = True,
    ) -> TrabajoCandidato:
        candidatos = []
        candidatos.extend(
            self._candidatos_pendientes(pendientes)
        )

        if permitir_proyectos:
            candidatos.extend(
                self._candidatos_proyectos(
                    capacidad_desarrollo
                )
            )

        if permitir_tareas_escritorio:
            candidatos.extend(
                self._candidatos_tareas_escritorio()
            )

        if not candidatos:
            return TrabajoCandidato(
                tipo=TipoTrabajoAgente.NADA,
                id=None,
                descripcion="No existe trabajo ejecutable.",
            )

        candidatos.sort(
            key=lambda item: (
                item.score,
                item.prioridad,
                item.continuidad,
                item.confianza,
            ),
            reverse=True,
        )

        return candidatos[0]