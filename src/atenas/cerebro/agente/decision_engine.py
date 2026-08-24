from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .estado_mundo import EstadoMundo
from .objetivos import GestorObjetivos
from .pendientes import GestorPendientes

from .capacidad_desarrollo import (
    CapacidadDesarrollo,
)

from .director_iniciativa import (
    DirectorIniciativaAgente,
    TipoTrabajoAgente,
)


class TipoDecisionAgente(str, Enum):
    NADA = "nada"
    PENDIENTE = "pendiente"

    CREAR_PROYECTO = "crear_proyecto"
    CONTINUAR_PROYECTO = "continuar_proyecto"
    CONSULTAR_PROYECTO = "consultar_proyecto"

    ACCION_SISTEMA = "accion_sistema"


@dataclass
class Decision:
    actuar: bool

    pendiente_id: str | None = None
    motivo: str = ""
    prioridad: float = 0.0

    tipo: TipoDecisionAgente = (
        TipoDecisionAgente.NADA
    )

    capacidad: str | None = None
    accion_capacidad: str | None = None

    proyecto_id: str | None = None

    argumentos: dict[str, Any] | None = None

    autonomo: bool = False


class DecisionEngine:
    """
    DecisionEngine V4.

    Puede seleccionar:
    - pendiente tradicional;
    - creación de software;
    - continuación autónoma;
    - acción estructurada del computador.
    """

    ACCION_CREAR_PROYECTO = (
        "desarrollo_software:"
        "crear_proyecto"
    )

    PREFIJO_SISTEMA = (
        "sistema_computador:"
    )

    def __init__(
        self,
        director: (
            DirectorIniciativaAgente
            | None
        ) = None,
    ):

        self.director = (
            director
            or DirectorIniciativaAgente()
        )

    def decidir(
        self,
        estado: EstadoMundo,
        objetivos: GestorObjetivos,
        pendientes: GestorPendientes,
    ) -> Decision:

        candidato = (
            self.director.elegir(
                pendientes=pendientes,
                capacidad_desarrollo=None,
                permitir_proyectos=False,
            )
        )

        if (
            candidato.tipo
            == TipoTrabajoAgente.NADA
        ):

            return Decision(
                actuar=False,
                motivo=(
                    "No existen pendientes ejecutables."
                ),
            )

        return Decision(
            actuar=True,
            pendiente_id=(
                candidato.id
            ),
            motivo=(
                "El Director de Iniciativa "
                "seleccionó trabajo."
            ),
            prioridad=(
                candidato.score
            ),
            tipo=(
                TipoDecisionAgente
                .PENDIENTE
            ),
            autonomo=True,
        )

    def decidir_ampliado(
        self,
        estado: EstadoMundo,
        objetivos: GestorObjetivos,
        pendientes: GestorPendientes,
        capacidad_desarrollo: (
            CapacidadDesarrollo
            | None
        ) = None,
        permitir_iniciativa_desarrollo: bool = True,
    ) -> Decision:

        candidato = (
            self.director.elegir(
                pendientes=pendientes,
                capacidad_desarrollo=(
                    capacidad_desarrollo
                ),
                permitir_proyectos=(
                    permitir_iniciativa_desarrollo
                ),
            )
        )

        if (
            candidato.tipo
            == TipoTrabajoAgente.NADA
        ):

            return Decision(
                actuar=False,
                motivo=(
                    "No existe trabajo ejecutable."
                ),
                tipo=(
                    TipoDecisionAgente.NADA
                ),
            )

        if (
            candidato.tipo
            == TipoTrabajoAgente.PROYECTO
        ):

            return Decision(
                actuar=True,
                motivo=(
                    "El Director seleccionó "
                    "un proyecto activo."
                ),
                prioridad=(
                    candidato.score
                ),
                tipo=(
                    TipoDecisionAgente
                    .CONTINUAR_PROYECTO
                ),
                capacidad=(
                    "desarrollo_software"
                ),
                accion_capacidad=(
                    "continuar_proyecto"
                ),
                proyecto_id=(
                    candidato.id
                ),
                argumentos={
                    "proyecto_id":
                        candidato.id,

                    "max_ciclos":
                        1,
                },
                autonomo=True,
            )

        pendiente = (
            pendientes.obtener(
                candidato.id
            )
        )

        if pendiente is None:

            return Decision(
                actuar=False,
                motivo=(
                    "El pendiente ya no existe."
                ),
            )

        accion = (
            pendiente.accion_sugerida
            or ""
        ).strip().lower()

        if (
            accion
            == self.ACCION_CREAR_PROYECTO
        ):

            return Decision(
                actuar=True,
                pendiente_id=(
                    pendiente.id
                ),
                motivo=(
                    "Solicitud de software priorizada."
                ),
                prioridad=(
                    candidato.score
                ),
                tipo=(
                    TipoDecisionAgente
                    .CREAR_PROYECTO
                ),
                capacidad=(
                    "desarrollo_software"
                ),
                accion_capacidad=(
                    "crear_proyecto"
                ),
                argumentos={
                    "descripcion":
                        (
                            pendiente
                            .mensaje_origen
                            or pendiente
                            .descripcion
                        ),

                    "nombre_sugerido":
                        None,

                    "carpeta":
                        None,

                    "prioridad":
                        getattr(
                            pendiente,
                            "prioridad",
                            0.70,
                        ),
                },
                autonomo=False,
            )

        if accion.startswith(
            self.PREFIJO_SISTEMA
        ):

            accion_sistema = (
                accion.split(
                    ":",
                    1,
                )[1]
            )

            return Decision(
                actuar=True,
                pendiente_id=(
                    pendiente.id
                ),
                motivo=(
                    "Solicitud estructurada "
                    "del sistema priorizada."
                ),
                prioridad=(
                    candidato.score
                ),
                tipo=(
                    TipoDecisionAgente
                    .ACCION_SISTEMA
                ),
                capacidad=(
                    "sistema_computador"
                ),
                accion_capacidad=(
                    accion_sistema
                ),
                argumentos={
                    "texto":
                        (
                            pendiente
                            .mensaje_origen
                            or pendiente
                            .descripcion
                        )
                },
                autonomo=False,
            )

        return Decision(
            actuar=True,
            pendiente_id=(
                pendiente.id
            ),
            motivo=(
                "Pendiente tradicional seleccionado."
            ),
            prioridad=(
                candidato.score
            ),
            tipo=(
                TipoDecisionAgente.PENDIENTE
            ),
            autonomo=True,
        )