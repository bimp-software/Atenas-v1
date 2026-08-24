from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EstadoMundo:
    """
    Estado observable mínimo del Agente.

    V2 añade información de ciclo e iniciativa para que ATENAS pueda
    saber si está trabajando, cuándo fue su última acción y qué ocurrió.
    """

    ultimo_mensaje: str | None = None

    ultimo_evento: str | None = None

    ultima_accion: str | None = None
    ultima_accion_ok: bool | None = None

    ciclo_autonomo_activo: bool = False

    actualizado_en: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def _ahora(
        self,
    ) -> str:

        return (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

    def actualizar_mensaje(
        self,
        mensaje: str,
    ) -> None:

        self.ultimo_mensaje = (
            mensaje
        )

        self.ultimo_evento = (
            "mensaje_usuario"
        )

        self.actualizado_en = (
            self._ahora()
        )

    def registrar_accion(
        self,
        accion: str,
        ok: bool | None,
        datos: dict[str, Any] | None = None,
    ) -> None:

        self.ultima_accion = (
            accion
        )

        self.ultima_accion_ok = (
            ok
        )

        self.ultimo_evento = (
            "accion_agente"
        )

        if datos:

            self.metadata.update(
                datos
            )

        self.actualizado_en = (
            self._ahora()
        )

    def iniciar_ciclo_autonomo(
        self,
    ) -> None:

        self.ciclo_autonomo_activo = (
            True
        )

        self.ultimo_evento = (
            "ciclo_autonomo_iniciado"
        )

        self.actualizado_en = (
            self._ahora()
        )

    def finalizar_ciclo_autonomo(
        self,
        estado: str,
    ) -> None:

        self.ciclo_autonomo_activo = (
            False
        )

        self.ultimo_evento = (
            "ciclo_autonomo_finalizado"
        )

        self.metadata[
            "ultimo_estado_ciclo_autonomo"
        ] = estado

        self.actualizado_en = (
            self._ahora()
        )