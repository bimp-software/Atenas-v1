from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .gestor_entornos_proyecto import (
    DependenciaProyecto,
    GestorEntornosProyecto,
    PlanEntornoProyecto,
)
from .gestor_seguro_dependencias import (
    EvaluacionDependencia,
    GestorSeguroDependencias,
)


class EstadoDependenciasTarea(str, Enum):
    LISTA = "lista"
    BLOQUEADA = "bloqueada_dependencias"
    REQUIERE_CONFIRMACION = "requiere_confirmacion_dependencias"
    ERROR = "error_dependencias"


@dataclass
class DependenciaPendiente:
    dependencia: DependenciaProyecto
    evaluacion: EvaluacionDependencia | None = None
    motivo: str = ""


@dataclass
class ResultadoPreparacionTarea:
    ok: bool
    estado: EstadoDependenciasTarea
    plan_entorno: PlanEntornoProyecto | None = None
    pendientes: list[DependenciaPendiente] = field(default_factory=list)
    mensajes: list[str] = field(default_factory=list)


class CoordinadorDependenciasTarea:
    """
    Puente entre el ejecutor de planes de software y los gestores
    de entorno/dependencias.

    Su responsabilidad NO es programar la tarea. Antes de programarla:
      1. prepara/detecta el entorno;
      2. comprueba dependencias declaradas;
      3. clasifica las faltantes;
      4. devuelve un estado estructurado;
      5. permite reanudar después sin perder el plan.

    Esto evita que EjecutorPlanSoftware tenga que conocer detalles
    de pip/npm/venv.
    """

    def __init__(
        self,
        gestor_entornos: GestorEntornosProyecto | None = None,
        gestor_dependencias: GestorSeguroDependencias | None = None,
    ):
        self.gestor_entornos = (
            gestor_entornos or GestorEntornosProyecto()
        )
        self.gestor_dependencias = (
            gestor_dependencias or GestorSeguroDependencias()
        )

    def preparar(
        self,
        carpeta_proyecto: str | Path,
    ) -> ResultadoPreparacionTarea:

        resultado_entorno = self.gestor_entornos.preparar(
            carpeta_proyecto=carpeta_proyecto,
            crear_venv_python=True,
        )

        if not resultado_entorno.ok or resultado_entorno.plan is None:
            return ResultadoPreparacionTarea(
                ok=False,
                estado=EstadoDependenciasTarea.ERROR,
                mensajes=[
                    resultado_entorno.error
                    or "No fue posible preparar el entorno."
                ],
            )

        plan = resultado_entorno.plan
        pendientes: list[DependenciaPendiente] = []

        for dependencia in plan.dependencias:
            if dependencia.instalada is not False:
                continue

            evaluacion = self.gestor_dependencias.evaluar(
                plan=plan,
                dependencia=dependencia,
            )

            pendientes.append(
                DependenciaPendiente(
                    dependencia=dependencia,
                    evaluacion=evaluacion,
                    motivo=evaluacion.motivo,
                )
            )

        if not pendientes:
            return ResultadoPreparacionTarea(
                ok=True,
                estado=EstadoDependenciasTarea.LISTA,
                plan_entorno=plan,
                mensajes=[
                    "El entorno está listo para ejecutar la tarea."
                ],
            )

        if any(
            p.evaluacion is not None
            and p.evaluacion.requiere_confirmacion
            for p in pendientes
        ):
            return ResultadoPreparacionTarea(
                ok=False,
                estado=EstadoDependenciasTarea.REQUIERE_CONFIRMACION,
                plan_entorno=plan,
                pendientes=pendientes,
                mensajes=[
                    "La tarea quedó pausada hasta resolver "
                    "dependencias que requieren confirmación."
                ],
            )

        return ResultadoPreparacionTarea(
            ok=False,
            estado=EstadoDependenciasTarea.BLOQUEADA,
            plan_entorno=plan,
            pendientes=pendientes,
            mensajes=[
                "La tarea quedó bloqueada por dependencias faltantes."
            ],
        )

    def resolver_confirmadas(
        self,
        carpeta_proyecto: str | Path,
        preparacion: ResultadoPreparacionTarea,
    ) -> ResultadoPreparacionTarea:

        if preparacion.plan_entorno is None:
            return ResultadoPreparacionTarea(
                ok=False,
                estado=EstadoDependenciasTarea.ERROR,
                mensajes=["No existe un plan de entorno para reanudar."],
            )

        errores: list[str] = []

        for pendiente in preparacion.pendientes:
            resultado = self.gestor_dependencias.instalar(
                carpeta_proyecto=carpeta_proyecto,
                plan=preparacion.plan_entorno,
                dependencia=pendiente.dependencia,
                confirmado=True,
            )

            if not resultado.ok:
                errores.append(
                    f"{pendiente.dependencia.nombre}: "
                    f"{resultado.error or 'instalación fallida'}"
                )

        if errores:
            return ResultadoPreparacionTarea(
                ok=False,
                estado=EstadoDependenciasTarea.ERROR,
                plan_entorno=preparacion.plan_entorno,
                pendientes=preparacion.pendientes,
                mensajes=errores,
            )

        # Volvemos a inspeccionar el proyecto; no asumimos que instalar
        # equivale a estar listo.
        return self.preparar(carpeta_proyecto)


def estado_para_ejecutor(
    resultado: ResultadoPreparacionTarea,
) -> str:
    """
    Traduce el estado del coordinador a una cadena simple que puede usar
    EjecutorPlanSoftware sin acoplarse a este módulo.
    """
    return resultado.estado.value