from __future__ import annotations

import json

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .analista_requisitos import (
    AnalisisRequisitos,
)

from .arquitecto_software import (
    ArquitecturaSoftware,
)

from .disenador_base_datos import (
    ModeloBaseDatos,
)

from .planificador_sistema_software import (
    EstadoTarea,
    PlanSistemaSoftware,
    PlanificadorSistemaSoftware,
    TareaSoftware,
)

from .programador_tarea_software import (
    ProgramadorTareaSoftware,
    ResultadoProgramacionTarea,
)


@dataclass
class ResultadoEjecucionPlan:
    ok: bool

    estado: str

    tarea: TareaSoftware | None = None

    resultado_tarea: (
        ResultadoProgramacionTarea
        | None
    ) = None

    plan_completado: bool = False

    mensaje: str = ""

    error: str | None = None


class EjecutorPlanSoftware:
    """
    Motor que permite a ATENAS desarrollar un sistema completo
    de forma progresiva.

    En cada iteración:
    1. encuentra la siguiente tarea desbloqueada;
    2. la marca EN_PROGRESO;
    3. llama al programador incremental;
    4. persiste el estado;
    5. la completa o marca FALLIDA;
    6. deja que el siguiente ciclo continúe con otra tarea.

    No ejecuta todas las tareas en un solo ciclo.
    """

    def __init__(
        self,
        programador: ProgramadorTareaSoftware,
    ):
        self.programador = (
            programador
        )

    # =========================================================
    # PERSISTENCIA
    # =========================================================

    @staticmethod
    def _persistir_plan(
        plan: PlanSistemaSoftware,
    ) -> None:

        if not plan.ruta_persistencia:
            return

        ruta = Path(
            plan.ruta_persistencia
        )

        ruta.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        ruta.write_text(
            json.dumps(
                asdict(
                    plan
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    # =========================================================
    # CONTEXTO
    # =========================================================

    @staticmethod
    def _contexto(
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
        modelo_bd: ModeloBaseDatos | None,
        plan: PlanSistemaSoftware,
    ) -> dict:

        return {
            "analisis":
                asdict(
                    analisis
                ),

            "arquitectura":
                asdict(
                    arquitectura
                ),

            "base_datos": (
                asdict(
                    modelo_bd
                )
                if modelo_bd is not None
                else None
            ),

            "plan": {
                "id":
                    plan.id,

                "nombre_proyecto":
                    plan.nombre_proyecto,

                "tipo_solucion":
                    plan.tipo_solucion,

                "arquitectura":
                    plan.arquitectura,

                "complejidad":
                    plan.complejidad,
            },
        }

    # =========================================================
    # ESTADO GLOBAL
    # =========================================================

    @staticmethod
    def plan_terminado(
        plan: PlanSistemaSoftware,
    ) -> bool:

        tareas = (
            PlanificadorSistemaSoftware
            .todas_las_tareas(
                plan
            )
        )

        return bool(
            tareas
            and all(
                tarea.estado
                == EstadoTarea.COMPLETADA
                for tarea
                in tareas
            )
        )

    # =========================================================
    # EJECUTAR UNA SOLA TAREA
    # =========================================================

    def ejecutar_siguiente(
        self,
        carpeta_proyecto: str | Path,
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
        modelo_bd: ModeloBaseDatos | None,
        plan: PlanSistemaSoftware,
    ) -> ResultadoEjecucionPlan:

        if self.plan_terminado(
            plan
        ):

            return ResultadoEjecucionPlan(
                ok=True,
                estado="plan_completado",
                plan_completado=True,
                mensaje=(
                    "Todas las tareas del plan "
                    "están completadas."
                ),
            )

        tarea = (
            PlanificadorSistemaSoftware
            .siguiente_tarea(
                plan
            )
        )

        if tarea is None:

            return ResultadoEjecucionPlan(
                ok=False,
                estado="sin_tarea_ejecutable",
                mensaje=(
                    "No existe una tarea desbloqueada. "
                    "Puede haber dependencias pendientes "
                    "o tareas fallidas."
                ),
                error="sin_tarea_ejecutable",
            )

        tarea.estado = (
            EstadoTarea.EN_PROGRESO
        )

        self._persistir_plan(
            plan
        )

        contexto = (
            self._contexto(
                analisis=analisis,
                arquitectura=arquitectura,
                modelo_bd=modelo_bd,
                plan=plan,
            )
        )

        resultado = (
            self.programador
            .programar(
                carpeta_proyecto=(
                    carpeta_proyecto
                ),
                tarea=tarea,
                contexto_sistema=(
                    contexto
                ),
            )
        )

        if (
            resultado.ok
            and resultado.completado
        ):

            tarea.estado = (
                EstadoTarea.COMPLETADA
            )

            estado = (
                "tarea_completada"
            )

        else:

            tarea.estado = (
                EstadoTarea.FALLIDA
            )

            estado = (
                "tarea_fallida"
            )

        self._persistir_plan(
            plan
        )

        terminado = (
            self.plan_terminado(
                plan
            )
        )

        return ResultadoEjecucionPlan(
            ok=bool(
                resultado.ok
                and resultado.completado
            ),
            estado=estado,
            tarea=tarea,
            resultado_tarea=resultado,
            plan_completado=terminado,
            mensaje=(
                resultado.resumen
            ),
            error=(
                resultado.error
            ),
        )