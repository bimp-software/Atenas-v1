from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .capacidad_desarrollo import (
    CapacidadDesarrollo,
)
from .pendientes import (
    GestorPendientes,
)
from .registro_tareas_escritorio import (
    RegistroTareasEscritorio,
)
from .tareas_escritorio import (
    EstadoTareaEscritorio,
)


class TipoTrabajoAgente(str, Enum):
    NADA = "nada"
    PENDIENTE = "pendiente"
    PROYECTO = "proyecto"
    TAREA_ESCRITORIO = "tarea_escritorio"
    REPLANIFICAR_TAREA_ESCRITORIO = (
        "replanificar_tarea_escritorio"
    )


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

    Compara:
    - pendientes;
    - proyectos de software;
    - tareas de escritorio ejecutables;
    - tareas fallidas que pueden replanificarse.

    Una tarea que requiere confirmación humana nunca es seleccionada
    automáticamente.
    """

    MAX_REPLANIFICACIONES_AUTONOMAS = 3

    def __init__(
        self,
        registro_tareas: (
            RegistroTareasEscritorio
            | None
        ) = None,
    ):
        self.registro_tareas = (
            registro_tareas
            or RegistroTareasEscritorio()
        )

    # =========================================================
    # SCORE
    # =========================================================

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
                (
                    prioridad * 0.45
                    + confianza * 0.20
                    + urgencia * 0.15
                    + continuidad * 0.20
                ),
            ),
            4,
        )

    # =========================================================
    # PENDIENTES
    # =========================================================

    def _candidatos_pendientes(
        self,
        pendientes: GestorPendientes,
    ) -> list[TrabajoCandidato]:

        candidatos = []

        for pendiente in (
            pendientes.pendientes()
        ):

            prioridad = float(
                getattr(
                    pendiente,
                    "prioridad",
                    0.60,
                )
                or 0.60
            )

            confianza = float(
                getattr(
                    pendiente,
                    "confianza",
                    0.70,
                )
                or 0.70
            )

            urgencia = 0.55
            continuidad = 0.30

            candidatos.append(
                TrabajoCandidato(
                    tipo=(
                        TipoTrabajoAgente
                        .PENDIENTE
                    ),
                    id=pendiente.id,
                    descripcion=(
                        getattr(
                            pendiente,
                            "descripcion",
                            "",
                        )
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
                        "accion_sugerida":
                            getattr(
                                pendiente,
                                "accion_sugerida",
                                None,
                            )
                    },
                )
            )

        return candidatos

    # =========================================================
    # PROYECTOS
    # =========================================================

    def _candidatos_proyectos(
        self,
        capacidad_desarrollo: (
            CapacidadDesarrollo
            | None
        ),
    ) -> list[TrabajoCandidato]:

        if capacidad_desarrollo is None:
            return []

        try:

            proyectos = (
                capacidad_desarrollo
                .listar_proyectos(
                    solo_activos=True
                )
            )

        except Exception:

            return []

        candidatos = []

        for proyecto in (
            proyectos
            or []
        ):

            if isinstance(
                proyecto,
                dict,
            ):

                proyecto_id = (
                    proyecto.get(
                        "id"
                    )
                    or proyecto.get(
                        "proyecto_id"
                    )
                )

                prioridad = float(
                    proyecto.get(
                        "prioridad",
                        0.72,
                    )
                    or 0.72
                )

                progreso = float(
                    proyecto.get(
                        "progreso",
                        0.0,
                    )
                    or 0.0
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

                proyecto_id = getattr(
                    proyecto,
                    "id",
                    None,
                )

                prioridad = float(
                    getattr(
                        proyecto,
                        "prioridad",
                        0.72,
                    )
                    or 0.72
                )

                progreso = float(
                    getattr(
                        proyecto,
                        "progreso",
                        0.0,
                    )
                    or 0.0
                )

                descripcion = str(
                    getattr(
                        proyecto,
                        "nombre",
                        None,
                    )
                    or getattr(
                        proyecto,
                        "descripcion",
                        "Proyecto de software",
                    )
                )

            if not proyecto_id:
                continue

            continuidad = (
                0.90
                if progreso > 0.0
                else 0.55
            )

            urgencia = 0.60
            confianza = 0.92

            candidatos.append(
                TrabajoCandidato(
                    tipo=(
                        TipoTrabajoAgente
                        .PROYECTO
                    ),
                    id=str(
                        proyecto_id
                    ),
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
                    metadata={
                        "progreso":
                            progreso
                    },
                )
            )

        return candidatos

    # =========================================================
    # TAREAS DE ESCRITORIO
    # =========================================================

    def _candidatos_tareas_escritorio(
        self,
    ) -> list[TrabajoCandidato]:

        candidatos = []

        # Usamos cargar() y no pendientes() porque una tarea FALLIDA
        # puede ser candidata a replanificación.
        for tarea in (
            self.registro_tareas
            .cargar()
        ):

            if tarea.estado == (
                EstadoTareaEscritorio
                .REQUIERE_CONFIRMACION
            ):

                continue

            if tarea.estado == (
                EstadoTareaEscritorio
                .COMPLETADA
            ):

                continue

            replanificaciones = int(
                tarea.metadata.get(
                    "replanificaciones",
                    0,
                )
                or 0
            )

            sugerida = bool(
                tarea.metadata.get(
                    "replanificacion_sugerida",
                    False,
                )
            )

            # -------------------------------------------------
            # REPLANIFICAR
            # -------------------------------------------------

            if (
                tarea.estado
                == EstadoTareaEscritorio.FALLIDA
                or sugerida
            ):

                if (
                    replanificaciones
                    >= self.MAX_REPLANIFICACIONES_AUTONOMAS
                ):

                    continue

                prioridad = min(
                    1.0,
                    float(
                        tarea.prioridad
                    )
                    + 0.04,
                )

                confianza = 0.88
                urgencia = 0.82
                continuidad = 0.94

                candidatos.append(
                    TrabajoCandidato(
                        tipo=(
                            TipoTrabajoAgente
                            .REPLANIFICAR_TAREA_ESCRITORIO
                        ),
                        id=tarea.id,
                        descripcion=(
                            f"Replanificar: "
                            f"{tarea.nombre}"
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
                            "estado":
                                tarea.estado.value,

                            "progreso":
                                tarea.progreso,

                            "ultimo_error":
                                tarea.ultimo_error,

                            "replanificaciones":
                                replanificaciones,
                        },
                    )
                )

                continue

            # -------------------------------------------------
            # CONTINUAR
            # -------------------------------------------------

            if tarea.estado not in {
                EstadoTareaEscritorio.NUEVA,
                EstadoTareaEscritorio.EN_PROGRESO,
                EstadoTareaEscritorio.PAUSADA,
            }:

                continue

            progreso = (
                tarea.progreso
            )

            continuidad = (
                0.95
                if progreso > 0.0
                else 0.65
            )

            urgencia = 0.68
            confianza = 0.93
            prioridad = float(
                tarea.prioridad
            )

            candidatos.append(
                TrabajoCandidato(
                    tipo=(
                        TipoTrabajoAgente
                        .TAREA_ESCRITORIO
                    ),
                    id=tarea.id,
                    descripcion=(
                        tarea.nombre
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
                        "estado":
                            tarea.estado.value,

                        "progreso":
                            progreso,

                        "paso_actual":
                            tarea.paso_actual,
                    },
                )
            )

        return candidatos

    # =========================================================
    # ELEGIR
    # =========================================================

    def elegir(
        self,
        pendientes: GestorPendientes,
        capacidad_desarrollo: (
            CapacidadDesarrollo
            | None
        ) = None,
        permitir_proyectos: bool = True,
        permitir_tareas_escritorio: bool = True,
    ) -> TrabajoCandidato:

        candidatos = []

        candidatos.extend(
            self._candidatos_pendientes(
                pendientes
            )
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
                descripcion=(
                    "No existe trabajo ejecutable."
                ),
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