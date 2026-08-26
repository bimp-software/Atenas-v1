from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .gestor_confirmaciones import (
    GestorConfirmaciones,
)
from .gestor_contexto_operativo import (
    GestorContextoOperativo,
)
from .gestor_sesion_trabajo import (
    EstadoSesionTrabajo,
    GestorSesionTrabajo,
)
from .registro_actividad_agente import (
    RegistroActividadAgente,
)
from .registro_tareas_escritorio import (
    RegistroTareasEscritorio,
)
from .tareas_escritorio import (
    EstadoTareaEscritorio,
)


class EstadoOperativoAgente(str, Enum):
    INACTIVO = "inactivo"
    TRABAJANDO = "trabajando"
    EN_ESPERA = "en_espera"
    BLOQUEADO = "bloqueado"
    ERROR = "error"


@dataclass
class EstadoAgente:
    estado: EstadoOperativoAgente

    sesion_id: str | None = None
    sesion_nombre: str | None = None

    proyecto_id: str | None = None
    proyecto_nombre: str | None = None
    ruta_proyecto: str | None = None

    tarea_id: str | None = None
    tarea_nombre: str | None = None
    tarea_estado: str | None = None

    progreso: float = 0.0

    ultima_accion: str | None = None

    confirmaciones_pendientes: int = 0

    ultimo_error: str | None = None

    ventana_activa: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class GestorEstadoAgente:
    """
    Consolida el estado de múltiples subsistemas en una sola vista.

    Esta clase está pensada para:
    - la futura web;
    - CLI/status;
    - logs;
    - diagnósticos;
    - recuperación tras reinicio.
    """

    def __init__(
        self,
        contexto: GestorContextoOperativo,
        sesiones: GestorSesionTrabajo,
        tareas: RegistroTareasEscritorio,
        confirmaciones: GestorConfirmaciones,
        actividad: RegistroActividadAgente,
    ):
        self.contexto = contexto
        self.sesiones = sesiones
        self.tareas = tareas
        self.confirmaciones = confirmaciones
        self.actividad = actividad

    def construir(
        self,
    ) -> EstadoAgente:

        contexto = self.contexto.cargar()
        sesion = self.sesiones.activa()
        pendientes = self.confirmaciones.pendientes()
        recientes = self.actividad.recientes(1)

        tarea = None

        if (
            sesion is not None
            and sesion.tarea_actual_id
        ):
            tarea = self.tareas.obtener(
                sesion.tarea_actual_id
            )

        if (
            tarea is None
            and contexto.ultima_tarea_id
        ):
            tarea = self.tareas.obtener(
                contexto.ultima_tarea_id
            )

        ultimo_evento = (
            recientes[-1]
            if recientes
            else None
        )

        # -----------------------------------------------------
        # ESTADO GENERAL
        # -----------------------------------------------------

        if pendientes:
            estado = (
                EstadoOperativoAgente.BLOQUEADO
            )

        elif contexto.ultimo_error:
            estado = (
                EstadoOperativoAgente.ERROR
            )

        elif (
            sesion is not None
            and sesion.estado
            == EstadoSesionTrabajo.ACTIVA
        ):
            if (
                tarea is not None
                and tarea.estado
                in {
                    EstadoTareaEscritorio.NUEVA,
                    EstadoTareaEscritorio.EN_PROGRESO,
                    EstadoTareaEscritorio.PAUSADA,
                }
            ):
                estado = (
                    EstadoOperativoAgente.TRABAJANDO
                )
            else:
                estado = (
                    EstadoOperativoAgente.EN_ESPERA
                )

        else:
            estado = (
                EstadoOperativoAgente.INACTIVO
            )

        # -----------------------------------------------------
        # PROGRESO
        # -----------------------------------------------------

        progreso = 0.0

        if sesion is not None:
            progreso = float(
                sesion.progreso
            )

        elif tarea is not None:
            progreso = float(
                tarea.progreso
            )

        # -----------------------------------------------------
        # ERROR
        # -----------------------------------------------------

        ultimo_error = (
            contexto.ultimo_error
        )

        if (
            not ultimo_error
            and tarea is not None
            and tarea.ultimo_error
        ):
            ultimo_error = (
                tarea.ultimo_error
            )

        return EstadoAgente(
            estado=estado,

            sesion_id=(
                sesion.id
                if sesion
                else None
            ),

            sesion_nombre=(
                sesion.nombre
                if sesion
                else None
            ),

            proyecto_id=(
                contexto.proyecto_actual_id
                or (
                    sesion.proyecto_id
                    if sesion
                    else None
                )
            ),

            proyecto_nombre=(
                contexto.nombre_proyecto_actual
            ),

            ruta_proyecto=(
                contexto.ruta_proyecto_actual
            ),

            tarea_id=(
                tarea.id
                if tarea
                else None
            ),

            tarea_nombre=(
                tarea.nombre
                if tarea
                else None
            ),

            tarea_estado=(
                tarea.estado.value
                if tarea
                else None
            ),

            progreso=round(
                progreso,
                2,
            ),

            ultima_accion=(
                str(
                    ultimo_evento.get(
                        "accion"
                    )
                )
                if ultimo_evento
                else None
            ),

            confirmaciones_pendientes=len(
                pendientes
            ),

            ultimo_error=ultimo_error,

            ventana_activa=(
                contexto.ventana_activa
            ),

            metadata={
                "actividad_ultima":
                    ultimo_evento,

                "sesion_estado":
                    (
                        sesion.estado.value
                        if sesion
                        else None
                    ),

                "actualizado_contexto_en":
                    contexto.actualizado_en,
            },
        )

    def como_dict(
        self,
    ) -> dict[str, Any]:

        estado = self.construir()

        return {
            "estado":
                estado.estado.value,

            "sesion_id":
                estado.sesion_id,

            "sesion_nombre":
                estado.sesion_nombre,

            "proyecto_id":
                estado.proyecto_id,

            "proyecto_nombre":
                estado.proyecto_nombre,

            "ruta_proyecto":
                estado.ruta_proyecto,

            "tarea_id":
                estado.tarea_id,

            "tarea_nombre":
                estado.tarea_nombre,

            "tarea_estado":
                estado.tarea_estado,

            "progreso":
                estado.progreso,

            "ultima_accion":
                estado.ultima_accion,

            "confirmaciones_pendientes":
                estado.confirmaciones_pendientes,

            "ultimo_error":
                estado.ultimo_error,

            "ventana_activa":
                estado.ventana_activa,

            "metadata":
                estado.metadata,
        }