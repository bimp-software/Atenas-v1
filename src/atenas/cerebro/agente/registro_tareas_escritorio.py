from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .tareas_escritorio import (
    EstadoPasoEscritorio,
    EstadoTareaEscritorio,
    PasoTareaEscritorio,
    TareaEscritorio,
    TipoPasoEscritorio,
)


class RegistroTareasEscritorio:
    def __init__(
        self,
        ruta: str | Path = "data/agente/tareas_escritorio/tareas.json",
    ):
        self.ruta = Path(ruta).resolve()
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        if not self.ruta.exists():
            self.ruta.write_text("[]", encoding="utf-8")

    @staticmethod
    def _paso_a_dict(paso: PasoTareaEscritorio) -> dict[str, Any]:
        return {
            "id": paso.id,
            "tipo": paso.tipo.value,
            "descripcion": paso.descripcion,
            "argumentos": paso.argumentos,
            "estado": paso.estado.value,
            "intentos": paso.intentos,
            "max_intentos": paso.max_intentos,
            "requiere_confirmacion": paso.requiere_confirmacion,
            "resultado": paso.resultado,
            "error": paso.error,
        }

    @classmethod
    def _tarea_a_dict(cls, tarea: TareaEscritorio) -> dict[str, Any]:
        return {
            "id": tarea.id,
            "nombre": tarea.nombre,
            "descripcion": tarea.descripcion,
            "pasos": [cls._paso_a_dict(p) for p in tarea.pasos],
            "estado": tarea.estado.value,
            "prioridad": tarea.prioridad,
            "creada_por": tarea.creada_por,
            "proyecto_id": tarea.proyecto_id,
            "paso_actual": tarea.paso_actual,
            "metadata": tarea.metadata,
            "ultimo_error": tarea.ultimo_error,
        }

    @staticmethod
    def _paso_desde_dict(datos: dict[str, Any]) -> PasoTareaEscritorio:
        return PasoTareaEscritorio(
            id=str(datos["id"]),
            tipo=TipoPasoEscritorio(datos["tipo"]),
            descripcion=str(datos.get("descripcion", "")),
            argumentos=datos.get("argumentos", {}) or {},
            estado=EstadoPasoEscritorio(datos.get("estado", "pendiente")),
            intentos=int(datos.get("intentos", 0)),
            max_intentos=int(datos.get("max_intentos", 2)),
            requiere_confirmacion=bool(datos.get("requiere_confirmacion", False)),
            resultado=datos.get("resultado", {}) or {},
            error=str(datos["error"]) if datos.get("error") else None,
        )

    @classmethod
    def _tarea_desde_dict(cls, datos: dict[str, Any]) -> TareaEscritorio:
        return TareaEscritorio(
            id=str(datos["id"]),
            nombre=str(datos.get("nombre", "Tarea de escritorio")),
            descripcion=str(datos.get("descripcion", "")),
            pasos=[
                cls._paso_desde_dict(p)
                for p in (datos.get("pasos", []) or [])
                if isinstance(p, dict)
            ],
            estado=EstadoTareaEscritorio(datos.get("estado", "nueva")),
            prioridad=float(datos.get("prioridad", 0.70) or 0.70),
            creada_por=str(datos.get("creada_por", "agente")),
            proyecto_id=(
                str(datos["proyecto_id"]) if datos.get("proyecto_id") else None
            ),
            paso_actual=int(datos.get("paso_actual", 0)),
            metadata=datos.get("metadata", {}) or {},
            ultimo_error=(
                str(datos["ultimo_error"]) if datos.get("ultimo_error") else None
            ),
        )

    def cargar(self) -> list[TareaEscritorio]:
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
                salida.append(self._tarea_desde_dict(item))
            except Exception:
                continue
        return salida

    def guardar_todas(self, tareas: list[TareaEscritorio]) -> None:
        temporal = self.ruta.with_suffix(".tmp")
        temporal.write_text(
            json.dumps(
                [self._tarea_a_dict(t) for t in tareas],
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        temporal.replace(self.ruta)

    def guardar(self, tarea: TareaEscritorio) -> None:
        tareas = [t for t in self.cargar() if t.id != tarea.id]
        tareas.append(tarea)
        self.guardar_todas(tareas)

    def obtener(self, tarea_id: str) -> TareaEscritorio | None:
        for tarea in self.cargar():
            if tarea.id == tarea_id:
                return tarea
        return None

    def pendientes(self) -> list[TareaEscritorio]:
        return [
            tarea for tarea in self.cargar()
            if tarea.estado in {
                EstadoTareaEscritorio.NUEVA,
                EstadoTareaEscritorio.EN_PROGRESO,
                EstadoTareaEscritorio.PAUSADA,
                EstadoTareaEscritorio.REQUIERE_CONFIRMACION,
            }
        ]