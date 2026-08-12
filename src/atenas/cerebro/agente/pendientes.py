from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class EstadoPendiente(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"
    FALLIDO = "fallido"


@dataclass
class Pendiente:
    id: str
    descripcion: str
    objetivo_id: str | None = None
    prioridad: float = 0.5
    estado: EstadoPendiente = EstadoPendiente.PENDIENTE
    requiere_confirmacion: bool = False
    resultado: str | None = None
    accion_sugerida: str | None = None
    mensaje_origen: str | None = None


class GestorPendientes:

    def __init__(self):
        self._pendientes: dict[str, Pendiente] = {}

    def cargar(
        self,
        pendientes: list[Pendiente],
    ) -> None:

        for pendiente in pendientes:
            self._pendientes[
                pendiente.id
            ] = pendiente

    # =====================================================
    # CREAR
    # =====================================================

    def crear(
        self,
        descripcion: str,
        objetivo_id: str | None = None,
        prioridad: float = 0.5,
        requiere_confirmacion: bool = False,
        accion_sugerida: str | None = None,
        mensaje_origen: str | None = None,
    ) -> Pendiente:

        pendiente = Pendiente(
            id=str(uuid4()),
            descripcion=descripcion,
            objetivo_id=objetivo_id,
            prioridad=prioridad,
            requiere_confirmacion=requiere_confirmacion,
            accion_sugerida=accion_sugerida,
            mensaje_origen=mensaje_origen,
        )

        self._pendientes[
            pendiente.id
        ] = pendiente

        return pendiente

    # =====================================================
    # OBTENER
    # =====================================================

    def obtener(
        self,
        pendiente_id: str,
    ) -> Pendiente | None:

        return self._pendientes.get(
            pendiente_id
        )

    # =====================================================
    # PENDIENTES ACTIVOS
    # =====================================================

    def pendientes(
        self,
    ) -> list[Pendiente]:

        return sorted(
            [
                pendiente
                for pendiente
                in self._pendientes.values()
                if pendiente.estado
                == EstadoPendiente.PENDIENTE
            ],
            key=lambda item: (
                item.prioridad
            ),
            reverse=True,
        )

    # =====================================================
    # EN PROCESO
    # =====================================================

    def iniciar(
        self,
        pendiente_id: str,
    ) -> bool:

        pendiente = self.obtener(
            pendiente_id
        )

        if pendiente is None:
            return False

        pendiente.estado = (
            EstadoPendiente.EN_PROCESO
        )

        return True

    # =====================================================
    # COMPLETAR
    # =====================================================

    def completar(
        self,
        pendiente_id: str,
        resultado: str | None = None,
    ) -> bool:

        pendiente = self.obtener(
            pendiente_id
        )

        if pendiente is None:
            return False

        pendiente.estado = (
            EstadoPendiente.COMPLETADO
        )

        pendiente.resultado = resultado

        return True

    # =====================================================
    # FALLAR
    # =====================================================

    def fallar(
        self,
        pendiente_id: str,
        resultado: str | None = None,
    ) -> bool:

        pendiente = self.obtener(
            pendiente_id
        )

        if pendiente is None:
            return False

        pendiente.estado = (
            EstadoPendiente.FALLIDO
        )

        pendiente.resultado = resultado

        return True

    # =====================================================
    # CANCELAR
    # =====================================================

    def cancelar(
        self,
        pendiente_id: str,
    ) -> bool:

        pendiente = self.obtener(
            pendiente_id
        )

        if pendiente is None:
            return False

        pendiente.estado = (
            EstadoPendiente.CANCELADO
        )

        return True