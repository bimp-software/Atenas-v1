from __future__ import annotations
from src.atenas.herramientas import ToolExecutor
from .gestor_tareas import GestorTareas
from .modelos import EstadoTarea, ResultadoEjecucionTarea

class EjecutorTareas:
    def __init__(self, gestor: GestorTareas, executor: ToolExecutor | None = None):
        self.gestor = gestor
        self.executor = executor or ToolExecutor()

    def ejecutar(self, tarea_id: str, confirmada: bool = False) -> ResultadoEjecucionTarea:
        tarea = self.gestor.obtener(tarea_id)
        if tarea is None:
            return ResultadoEjecucionTarea(False,tarea_id,False,error="tarea_no_encontrada")
        if tarea.estado != EstadoTarea.ACTIVA:
            return ResultadoEjecucionTarea(False,tarea.id,False,tarea.herramienta,
                error=f"tarea_no_activa:{tarea.estado.value}")
        if tarea.requiere_confirmacion and not confirmada:
            return ResultadoEjecucionTarea(True,tarea.id,False,tarea.herramienta,
                requiere_confirmacion=True)
        try:
            resultado = self.executor.ejecutar(tarea.herramienta, tarea.argumentos)
        except Exception as error:
            resultado = {"ok": False, "error": f"{type(error).__name__}: {error}"}
        self.gestor.registrar_ejecucion(tarea.id, resultado)
        ok = bool(resultado.get("ok", False))
        return ResultadoEjecucionTarea(
            ok=ok,tarea_id=tarea.id,ejecutada=True,herramienta=tarea.herramienta,
            resultado=resultado,error=None if ok else str(resultado.get("error","fallo_herramienta"))
        )
