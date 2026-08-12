from __future__ import annotations

from dataclasses import dataclass

from .objetivos import GestorObjetivos
from .pendientes import GestorPendientes
from .estado_mundo import EstadoMundo


@dataclass
class Decision:
    actuar: bool

    motivo: str

    objetivo_id: str | None = None
    pendiente_id: str | None = None

    confianza: float = 0.0


class DecisionEngine:

    def decidir(
        self,
        estado: EstadoMundo,
        objetivos: GestorObjetivos,
        pendientes: GestorPendientes,
    ) -> Decision:

        lista_pendientes = (
            pendientes.pendientes()
        )

        # =====================================================
        # PRIORIDAD 1: PENDIENTES YA EXISTENTES
        # =====================================================

        if lista_pendientes:

            pendiente = lista_pendientes[0]

            return Decision(
                actuar=True,
                motivo=(
                    "Existe un pendiente activo "
                    "que todavía no ha sido resuelto."
                ),
                objetivo_id=pendiente.objetivo_id,
                pendiente_id=pendiente.id,
                confianza=0.90,
            )

        # =====================================================
        # PRIORIDAD 2: OBJETIVOS ACTIVOS
        # =====================================================

        objetivos_activos = (
            objetivos.activos()
        )

        if not objetivos_activos:

            return Decision(
                actuar=False,
                motivo="No existen objetivos activos.",
                confianza=1.0,
            )

        objetivo = objetivos_activos[0]

        # En esta primera versión,
        # tener un objetivo no significa actuar
        # inmediatamente.

        return Decision(
            actuar=False,
            motivo=(
                f"El objetivo '{objetivo.nombre}' "
                "está activo, pero no hay una acción "
                "pendiente concreta."
            ),
            objetivo_id=objetivo.id,
            confianza=0.75,
        )