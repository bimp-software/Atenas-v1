from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .planificador_tareas_escritorio import (
    PlanificadorTareasEscritorio,
    PlanTareaEscritorio,
)
from .tareas_escritorio import (
    EstadoPasoEscritorio,
    EstadoTareaEscritorio,
    PasoTareaEscritorio,
    TareaEscritorio,
)


@dataclass
class ResultadoReplanificacion:
    ok: bool
    tarea: TareaEscritorio | None = None
    pasos_conservados: int = 0
    pasos_reemplazados: int = 0
    pasos_nuevos: int = 0
    motivo: str = ""
    advertencias: list[str] = field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ReplanificadorTareasEscritorio:
    """
    Reemplaza únicamente los pasos futuros de una tarea.

    Conserva COMPLETADO/OMITIDO, mantiene el mismo ID de tarea y
    genera un nuevo tramo usando PlanificadorTareasEscritorio.
    """

    def __init__(
        self,
        planificador: PlanificadorTareasEscritorio | None = None,
    ):
        self.planificador = planificador or PlanificadorTareasEscritorio()

    @staticmethod
    def _copiar(paso: PasoTareaEscritorio) -> PasoTareaEscritorio:
        return PasoTareaEscritorio(
            id=paso.id,
            tipo=paso.tipo,
            descripcion=paso.descripcion,
            argumentos=dict(paso.argumentos or {}),
            estado=paso.estado,
            intentos=paso.intentos,
            max_intentos=paso.max_intentos,
            requiere_confirmacion=paso.requiere_confirmacion,
            resultado=dict(paso.resultado or {}),
            error=paso.error,
        )

    @classmethod
    def _conservados(
        cls,
        tarea: TareaEscritorio,
    ) -> list[PasoTareaEscritorio]:
        return [
            cls._copiar(p)
            for p in tarea.pasos
            if p.estado in {
                EstadoPasoEscritorio.COMPLETADO,
                EstadoPasoEscritorio.OMITIDO,
            }
        ]

    @classmethod
    def _normalizar_nuevos(
        cls,
        pasos: list[PasoTareaEscritorio],
        usados: set[str],
    ) -> list[PasoTareaEscritorio]:
        salida = []

        for paso in pasos:
            nuevo = cls._copiar(paso)

            if not nuevo.id or nuevo.id in usados:
                nuevo.id = "replan_" + uuid.uuid4().hex[:10]

            usados.add(nuevo.id)

            nuevo.estado = EstadoPasoEscritorio.PENDIENTE
            nuevo.intentos = 0
            nuevo.requiere_confirmacion = False
            nuevo.resultado = {}
            nuevo.error = None

            salida.append(nuevo)

        return salida

    def conviene_replanificar(
        self,
        tarea: TareaEscritorio,
    ) -> tuple[bool, str]:
        if tarea.estado == EstadoTareaEscritorio.COMPLETADA:
            return False, "La tarea ya está completada."

        cantidad = int(tarea.metadata.get("replanificaciones", 0) or 0)
        if cantidad >= 3:
            return (
                False,
                "Se alcanzó el límite conservador de replanificaciones.",
            )

        if tarea.estado == EstadoTareaEscritorio.FALLIDA:
            return (
                True,
                "La tarea falló y conviene reconstruir los pasos futuros.",
            )

        if tarea.metadata.get("replanificacion_sugerida"):
            return (
                True,
                "El orquestador marcó la tarea para replanificación.",
            )

        return False, "No existe un motivo suficiente para replanificar."

    def replanificar(
        self,
        tarea: TareaEscritorio,
        motivo: str,
        contexto_nuevo: dict[str, Any] | None = None,
        objetivo_actualizado: str | None = None,
    ) -> ResultadoReplanificacion:
        if tarea.estado == EstadoTareaEscritorio.COMPLETADA:
            return ResultadoReplanificacion(
                ok=False,
                tarea=tarea,
                motivo=motivo,
                error="tarea_ya_completada",
            )

        conservados = self._conservados(tarea)
        reemplazables = [
            p for p in tarea.pasos
            if p.estado not in {
                EstadoPasoEscritorio.COMPLETADO,
                EstadoPasoEscritorio.OMITIDO,
            }
        ]

        contexto = dict(tarea.metadata.get("contexto", {}) or {})
        contexto.update(contexto_nuevo or {})
        contexto["replanificando_tarea_id"] = tarea.id
        contexto["motivo_replanificacion"] = motivo
        contexto["progreso_previo"] = tarea.progreso

        if tarea.ultimo_error:
            contexto["ultimo_error"] = tarea.ultimo_error

        objetivo = (
            objetivo_actualizado
            or tarea.descripcion
            or tarea.nombre
        )

        try:
            plan: PlanTareaEscritorio = self.planificador.planificar(
                objetivo=objetivo,
                contexto=contexto,
            )
        except Exception as error:
            return ResultadoReplanificacion(
                ok=False,
                tarea=tarea,
                pasos_conservados=len(conservados),
                pasos_reemplazados=len(reemplazables),
                motivo=motivo,
                error=f"{type(error).__name__}: {error}",
            )

        nuevos = self._normalizar_nuevos(
            plan.pasos,
            {p.id for p in conservados},
        )

        if not nuevos:
            return ResultadoReplanificacion(
                ok=False,
                tarea=tarea,
                pasos_conservados=len(conservados),
                pasos_reemplazados=len(reemplazables),
                motivo=motivo,
                error="replanificacion_sin_pasos",
            )

        tarea.pasos = conservados + nuevos
        tarea.paso_actual = len(conservados)
        tarea.estado = EstadoTareaEscritorio.EN_PROGRESO
        tarea.ultimo_error = None

        tarea.metadata["contexto"] = plan.contexto
        tarea.metadata["replanificacion_sugerida"] = False
        tarea.metadata["replanificaciones"] = (
            int(tarea.metadata.get("replanificaciones", 0) or 0) + 1
        )
        tarea.metadata["ultima_replanificacion"] = {
            "motivo": motivo,
            "pasos_conservados": len(conservados),
            "pasos_reemplazados": len(reemplazables),
            "pasos_nuevos": len(nuevos),
            "confianza_plan": plan.confianza,
            "advertencias": list(plan.advertencias),
        }

        return ResultadoReplanificacion(
            ok=True,
            tarea=tarea,
            pasos_conservados=len(conservados),
            pasos_reemplazados=len(reemplazables),
            pasos_nuevos=len(nuevos),
            motivo=motivo,
            advertencias=list(plan.advertencias),
            metadata={
                "confianza_plan": plan.confianza,
                "contexto": plan.contexto,
            },
        )