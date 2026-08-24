from __future__ import annotations
from pathlib import Path
from typing import Any
from .ejecutor_tareas import EjecutorTareas
from .gestor_tareas import GestorTareas
from .modelos import TipoDisparo

class ServicioTareas:
    def __init__(self, db_path: str | Path = "data/tareas.db"):
        self.gestor = GestorTareas(db_path=db_path)
        self.ejecutor = EjecutorTareas(gestor=self.gestor)

    def crear_tarea(self, nombre: str, descripcion: str, herramienta: str,
                    argumentos: dict[str, Any] | None = None,
                    tipo_disparo: str = "manual",
                    configuracion_disparo: dict[str, Any] | None = None,
                    requiere_confirmacion: bool = False,
                    origen: str = "usuario") -> dict:
        tarea = self.gestor.crear(
            nombre=nombre,descripcion=descripcion,herramienta=herramienta,
            argumentos=argumentos,tipo_disparo=TipoDisparo(tipo_disparo),
            configuracion_disparo=configuracion_disparo,
            requiere_confirmacion=requiere_confirmacion,origen=origen)
        return {"ok": True, "tarea": tarea.a_dict()}

    def listar_tareas(self) -> dict:
        tareas = self.gestor.listar()
        return {"ok": True,"total": len(tareas),"tareas": [t.a_dict() for t in tareas]}

    def obtener_tarea(self, tarea_id: str) -> dict:
        tarea = self.gestor.obtener(tarea_id)
        return {"ok": False,"error": "tarea_no_encontrada"} if tarea is None else {
            "ok": True,"tarea": tarea.a_dict()}

    def ejecutar_tarea(self, tarea_id: str, confirmada: bool = False) -> dict:
        r = self.ejecutor.ejecutar(tarea_id, confirmada=confirmada)
        return {"ok": r.ok,"tarea_id": r.tarea_id,"ejecutada": r.ejecutada,
                "herramienta": r.herramienta,"resultado": r.resultado,
                "requiere_confirmacion": r.requiere_confirmacion,"error": r.error}

    def pausar_tarea(self, tarea_id: str) -> dict:
        return {"ok": True,"tarea": self.gestor.pausar(tarea_id).a_dict()}

    def reanudar_tarea(self, tarea_id: str) -> dict:
        return {"ok": True,"tarea": self.gestor.reanudar(tarea_id).a_dict()}

    def eliminar_tarea(self, tarea_id: str) -> dict:
        return {"ok": True,"tarea": self.gestor.eliminar(tarea_id).a_dict()}
