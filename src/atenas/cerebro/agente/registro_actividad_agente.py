from __future__ import annotations

import json
import uuid

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class EventoActividad:
    id: str
    fecha: str
    categoria: str
    accion: str
    mensaje: str

    ok: bool = True

    sesion_id: str | None = None
    tarea_id: str | None = None
    proyecto_id: str | None = None

    duracion_ms: float | None = None

    datos: dict[str, Any] = field(default_factory=dict)


class RegistroActividadAgente:
    """
    Log estructurado JSONL para observabilidad y futura interfaz web.
    """

    def __init__(
        self,
        ruta: str | Path = "data/agente/actividad/actividad.jsonl",
        max_eventos_resumen: int = 200,
    ):
        self.ruta = Path(ruta).expanduser().resolve()
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.max_eventos_resumen = max(10, int(max_eventos_resumen))

        if not self.ruta.exists():
            self.ruta.touch()

    @staticmethod
    def _ahora() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _a_dict(evento: EventoActividad) -> dict[str, Any]:
        return {
            "id": evento.id,
            "fecha": evento.fecha,
            "categoria": evento.categoria,
            "accion": evento.accion,
            "mensaje": evento.mensaje,
            "ok": evento.ok,
            "sesion_id": evento.sesion_id,
            "tarea_id": evento.tarea_id,
            "proyecto_id": evento.proyecto_id,
            "duracion_ms": evento.duracion_ms,
            "datos": evento.datos,
        }

    def registrar(
        self,
        categoria: str,
        accion: str,
        mensaje: str,
        ok: bool = True,
        sesion_id: str | None = None,
        tarea_id: str | None = None,
        proyecto_id: str | None = None,
        duracion_ms: float | None = None,
        datos: dict[str, Any] | None = None,
    ) -> EventoActividad:
        evento = EventoActividad(
            id=str(uuid.uuid4()),
            fecha=self._ahora(),
            categoria=str(categoria),
            accion=str(accion),
            mensaje=str(mensaje),
            ok=bool(ok),
            sesion_id=sesion_id,
            tarea_id=tarea_id,
            proyecto_id=proyecto_id,
            duracion_ms=duracion_ms,
            datos=datos or {},
        )

        with self.ruta.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    self._a_dict(evento),
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )

        return evento

    def recientes(self, limite: int = 50) -> list[dict[str, Any]]:
        limite = max(1, min(int(limite), self.max_eventos_resumen))

        try:
            lineas = self.ruta.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []

        salida = []

        for linea in lineas[-limite:]:
            try:
                item = json.loads(linea)
                if isinstance(item, dict):
                    salida.append(item)
            except Exception:
                continue

        return salida

    def resumen(self) -> dict[str, Any]:
        recientes = self.recientes(self.max_eventos_resumen)

        return {
            "eventos_considerados": len(recientes),
            "correctos": sum(1 for x in recientes if x.get("ok") is True),
            "fallidos": sum(1 for x in recientes if x.get("ok") is False),
            "ultimo_evento": (
                recientes[-1]
                if recientes
                else None
            ),
        }