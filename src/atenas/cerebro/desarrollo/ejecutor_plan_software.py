from __future__ import annotations

import json

from dataclasses import asdict, dataclass
from pathlib import Path

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

from .validador_tarea_software import (
    ResultadoValidacionTarea,
    ValidadorTareaSoftware,
)

from .reparador_tarea_software import (
    ReparadorTareaSoftware,
    ResultadoReparacionTarea,
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

    validacion: (
        ResultadoValidacionTarea
        | None
    ) = None

    reparacion: (
        ResultadoReparacionTarea
        | None
    ) = None

    plan_completado: bool = False

    mensaje: str = ""

    error: str | None = None


class EjecutorPlanSoftware:
    """
    Ejecuta una tarea por ciclo:

      elegir
      -> programar
      -> validar
      -> si falla, reparar
      -> volver a validar
      -> completar/fallar
      -> persistir

    La reparación está limitada a un número finito de intentos.
    """

    def __init__(
        self,
        programador: ProgramadorTareaSoftware,
        validador: ValidadorTareaSoftware | None = None,
        reparador: ReparadorTareaSoftware | None = None,
    ):
        self.programador = programador

        self.validador = (
            validador
            or ValidadorTareaSoftware()
        )

        self.reparador = (
            reparador
            or ReparadorTareaSoftware(
                llm=programador.llm,
                validador=self.validador,
                max_intentos=3,
            )
        )

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
                asdict(plan),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _contexto(
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
        modelo_bd: ModeloBaseDatos | None,
        plan: PlanSistemaSoftware,
    ) -> dict:

        return {
            "analisis":
                asdict(analisis),

            "arquitectura":
                asdict(arquitectura),

            "base_datos": (
                asdict(modelo_bd)
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

    @staticmethod
    def plan_terminado(
        plan: PlanSistemaSoftware,
    ) -> bool:

        tareas = (
            PlanificadorSistemaSoftware
            .todas_las_tareas(plan)
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

    def ejecutar_siguiente(
        self,
        carpeta_proyecto: str | Path,
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
        modelo_bd: ModeloBaseDatos | None,
        plan: PlanSistemaSoftware,
    ) -> ResultadoEjecucionPlan:

        if self.plan_terminado(plan):

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
            .siguiente_tarea(plan)
        )

        if tarea is None:

            return ResultadoEjecucionPlan(
                ok=False,
                estado="sin_tarea_ejecutable",
                mensaje=(
                    "No existe una tarea desbloqueada."
                ),
                error="sin_tarea_ejecutable",
            )

        tarea.estado = (
            EstadoTarea.EN_PROGRESO
        )

        self._persistir_plan(plan)

        resultado_programacion = (
            self.programador
            .programar(
                carpeta_proyecto=(
                    carpeta_proyecto
                ),
                tarea=tarea,
                contexto_sistema=(
                    self._contexto(
                        analisis=analisis,
                        arquitectura=arquitectura,
                        modelo_bd=modelo_bd,
                        plan=plan,
                    )
                ),
            )
        )

        if (
            not resultado_programacion.ok
            or not resultado_programacion.completado
        ):

            tarea.estado = (
                EstadoTarea.FALLIDA
            )

            self._persistir_plan(plan)

            return ResultadoEjecucionPlan(
                ok=False,
                estado="tarea_fallida_programacion",
                tarea=tarea,
                resultado_tarea=(
                    resultado_programacion
                ),
                mensaje=(
                    resultado_programacion.resumen
                ),
                error=(
                    resultado_programacion.error
                ),
            )

        validacion = (
            self.validador
            .validar(
                carpeta_proyecto=(
                    carpeta_proyecto
                ),
                ejecutar_pruebas=(
                    tarea.requiere_pruebas
                ),
            )
        )

        reparacion = None

        if not validacion.ok:

            reparacion = (
                self.reparador
                .reparar(
                    carpeta_proyecto=(
                        carpeta_proyecto
                    ),
                    tarea=tarea,
                    validacion_inicial=(
                        validacion
                    ),
                    ejecutar_pruebas=(
                        tarea.requiere_pruebas
                    ),
                )
            )

            if (
                reparacion.ok
                and reparacion.validacion_final
                is not None
            ):

                validacion = (
                    reparacion
                    .validacion_final
                )

        if validacion.ok:

            tarea.estado = (
                EstadoTarea.COMPLETADA
            )

            estado = (
                "tarea_reparada_completada"
                if reparacion is not None
                else "tarea_completada"
            )

            ok = True

        else:

            tarea.estado = (
                EstadoTarea.FALLIDA
            )

            estado = (
                "tarea_fallida_validacion"
            )

            ok = False

        self._persistir_plan(plan)

        return ResultadoEjecucionPlan(
            ok=ok,
            estado=estado,
            tarea=tarea,
            resultado_tarea=(
                resultado_programacion
            ),
            validacion=validacion,
            reparacion=reparacion,
            plan_completado=(
                self.plan_terminado(plan)
            ),
            mensaje=(
                (
                    reparacion.resumen
                    if (
                        reparacion is not None
                        and reparacion.ok
                    )
                    else validacion.resumen
                )
            ),
            error=(
                None
                if validacion.ok
                else "\n".join(
                    validacion.errores
                )[:5000]
            ),
        )