from __future__ import annotations

import json
import uuid

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class EstadoConfirmacion(str, Enum):
    PENDIENTE = "pendiente"
    APROBADA = "aprobada"
    RECHAZADA = "rechazada"
    CANCELADA = "cancelada"
    EXPIRADA = "expirada"


@dataclass
class SolicitudConfirmacion:
    id: str
    accion: str
    descripcion: str

    estado: EstadoConfirmacion = EstadoConfirmacion.PENDIENTE

    riesgo: int = 1
    motivo: str = ""

    sesion_id: str | None = None
    tarea_id: str | None = None
    proyecto_id: str | None = None

    creada_en: str = ""
    resuelta_en: str | None = None

    argumentos: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class GestorConfirmaciones:
    """
    Cola persistente de acciones que requieren aprobación humana.

    Esta capa NO ejecuta la acción aprobada. Solo registra la decisión
    humana y deja el elemento listo para que el ciclo autónomo continúe
    de forma controlada.
    """

    def __init__(
        self,
        ruta: str | Path = "data/agente/confirmaciones/confirmaciones.json",
    ):
        self.ruta = Path(ruta).expanduser().resolve()
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

        if not self.ruta.exists():
            self.ruta.write_text("[]", encoding="utf-8")

    @staticmethod
    def _ahora() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _a_dict(item: SolicitudConfirmacion) -> dict[str, Any]:
        return {
            "id": item.id,
            "accion": item.accion,
            "descripcion": item.descripcion,
            "estado": item.estado.value,
            "riesgo": item.riesgo,
            "motivo": item.motivo,
            "sesion_id": item.sesion_id,
            "tarea_id": item.tarea_id,
            "proyecto_id": item.proyecto_id,
            "creada_en": item.creada_en,
            "resuelta_en": item.resuelta_en,
            "argumentos": item.argumentos,
            "metadata": item.metadata,
        }

    @staticmethod
    def _desde_dict(datos: dict[str, Any]) -> SolicitudConfirmacion:
        return SolicitudConfirmacion(
            id=str(datos["id"]),
            accion=str(datos.get("accion", "")),
            descripcion=str(datos.get("descripcion", "")),
            estado=EstadoConfirmacion(datos.get("estado", "pendiente")),
            riesgo=int(datos.get("riesgo", 1) or 1),
            motivo=str(datos.get("motivo", "")),
            sesion_id=datos.get("sesion_id"),
            tarea_id=datos.get("tarea_id"),
            proyecto_id=datos.get("proyecto_id"),
            creada_en=str(datos.get("creada_en", "")),
            resuelta_en=datos.get("resuelta_en"),
            argumentos=datos.get("argumentos", {}) or {},
            metadata=datos.get("metadata", {}) or {},
        )

    def listar(self) -> list[SolicitudConfirmacion]:
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        except Exception:
            datos = []

        if not isinstance(datos, list):
            datos = []

        salida = []
        for item in datos:
            if not isinstance(item, dict):
                continue
            try:
                salida.append(self._desde_dict(item))
            except Exception:
                continue
        return salida

    def _guardar_todas(self, items: list[SolicitudConfirmacion]) -> None:
        temporal = self.ruta.with_suffix(".tmp")
        temporal.write_text(
            json.dumps(
                [self._a_dict(x) for x in items],
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        temporal.replace(self.ruta)

    def guardar(self, item: SolicitudConfirmacion) -> None:
        items = [x for x in self.listar() if x.id != item.id]
        items.append(item)
        self._guardar_todas(items)

    def obtener(self, confirmacion_id: str) -> SolicitudConfirmacion | None:
        for item in self.listar():
            if item.id == confirmacion_id:
                return item
        return None

    def crear(
        self,
        accion: str,
        descripcion: str,
        riesgo: int = 1,
        motivo: str = "",
        sesion_id: str | None = None,
        tarea_id: str | None = None,
        proyecto_id: str | None = None,
        argumentos: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SolicitudConfirmacion:
        # Evita duplicar la misma confirmación pendiente para la misma tarea/acción.
        for existente in self.pendientes():
            if (
                existente.accion == accion
                and existente.tarea_id == tarea_id
                and existente.proyecto_id == proyecto_id
            ):
                return existente

        item = SolicitudConfirmacion(
            id=str(uuid.uuid4()),
            accion=str(accion),
            descripcion=str(descripcion),
            riesgo=max(0, int(riesgo)),
            motivo=str(motivo),
            sesion_id=sesion_id,
            tarea_id=tarea_id,
            proyecto_id=proyecto_id,
            creada_en=self._ahora(),
            argumentos=argumentos or {},
            metadata=metadata or {},
        )
        self.guardar(item)
        return item

    def pendientes(self) -> list[SolicitudConfirmacion]:
        salida = [
            x for x in self.listar()
            if x.estado == EstadoConfirmacion.PENDIENTE
        ]
        salida.sort(key=lambda x: (x.riesgo, x.creada_en), reverse=True)
        return salida

    def resolver(
        self,
        confirmacion_id: str,
        aprobar: bool,
        motivo: str | None = None,
    ) -> SolicitudConfirmacion | None:
        item = self.obtener(confirmacion_id)
        if item is None:
            return None

        if item.estado != EstadoConfirmacion.PENDIENTE:
            return item

        item.estado = (
            EstadoConfirmacion.APROBADA
            if aprobar
            else EstadoConfirmacion.RECHAZADA
        )
        item.resuelta_en = self._ahora()

        if motivo:
            item.metadata["motivo_resolucion"] = str(motivo)

        self.guardar(item)
        return item

    def resumen(self) -> dict[str, Any]:
        items = self.listar()
        pendientes = [x for x in items if x.estado == EstadoConfirmacion.PENDIENTE]

        return {
            "total": len(items),
            "pendientes": len(pendientes),
            "aprobadas": len([
                x for x in items
                if x.estado == EstadoConfirmacion.APROBADA
            ]),
            "rechazadas": len([
                x for x in items
                if x.estado == EstadoConfirmacion.RECHAZADA
            ]),
            "siguiente": (
                self._a_dict(pendientes[0])
                if pendientes
                else None
            ),
        }