from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .gestor_contexto_operativo import (
    GestorContextoOperativo,
)
from .gestor_sesion_trabajo import (
    EstadoSesionTrabajo,
    GestorSesionTrabajo,
    SesionTrabajo,
)
from .planificador_tareas_escritorio import (
    PlanificadorTareasEscritorio,
)
from .registro_tareas_escritorio import (
    RegistroTareasEscritorio,
)
from .tareas_escritorio import (
    EstadoTareaEscritorio,
    TareaEscritorio,
)


class TipoDecisionSupervisorSesion(str, Enum):
    NADA = "nada"
    CREAR_SESION = "crear_sesion"
    REANUDAR_SESION = "reanudar_sesion"
    ASOCIAR_TAREA = "asociar_tarea"
    GENERAR_TAREA = "generar_tarea"
    CONTINUAR_TAREA = "continuar_tarea"
    COMPLETAR_SESION = "completar_sesion"
    BLOQUEAR_SESION = "bloquear_sesion"


@dataclass
class DecisionSupervisorSesion:
    tipo: TipoDecisionSupervisorSesion
    actuar: bool

    motivo: str = ""

    sesion_id: str | None = None
    tarea_id: str | None = None

    prioridad: float = 0.0
    confianza: float = 0.0

    argumentos: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ResultadoSupervisorSesion:
    ok: bool
    decision: DecisionSupervisorSesion

    sesion: SesionTrabajo | None = None
    tarea: TareaEscritorio | None = None

    mensaje: str = ""
    error: str | None = None

    datos: dict[str, Any] = field(
        default_factory=dict
    )


class SupervisorSesionAutonoma:
    """
    Supervisa continuidad de trabajo de nivel superior.

    Responsabilidades:
    - detectar si falta una sesión activa;
    - reanudar una sesión pausada cuando procede;
    - asociar una tarea existente a la sesión;
    - pedir la generación de una nueva tarea si el objetivo sigue abierto;
    - cerrar una sesión cuando todas sus tareas terminaron y no quedan bloqueos;
    - bloquear una sesión si solo quedan tareas que requieren confirmación.

    No ejecuta mouse, teclado ni código. Solo gobierna continuidad.
    """

    def __init__(
        self,
        gestor_sesiones: GestorSesionTrabajo,
        registro_tareas: RegistroTareasEscritorio,
        contexto_operativo: GestorContextoOperativo,
        planificador_tareas: PlanificadorTareasEscritorio,
    ):
        self.gestor_sesiones = gestor_sesiones
        self.registro_tareas = registro_tareas
        self.contexto_operativo = contexto_operativo
        self.planificador_tareas = planificador_tareas

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _tarea_terminal(
        tarea: TareaEscritorio,
    ) -> bool:
        return tarea.estado in {
            EstadoTareaEscritorio.COMPLETADA,
            EstadoTareaEscritorio.FALLIDA,
        }

    @staticmethod
    def _tarea_ejecutable(
        tarea: TareaEscritorio,
    ) -> bool:
        return tarea.estado in {
            EstadoTareaEscritorio.NUEVA,
            EstadoTareaEscritorio.EN_PROGRESO,
            EstadoTareaEscritorio.PAUSADA,
        }

    @staticmethod
    def _tarea_bloqueada(
        tarea: TareaEscritorio,
    ) -> bool:
        return (
            tarea.estado
            == EstadoTareaEscritorio.REQUIERE_CONFIRMACION
        )

    def _tareas_de_sesion(
        self,
        sesion: SesionTrabajo,
    ) -> list[TareaEscritorio]:
        ids = set(
            sesion.tareas_relacionadas
            or []
        )

        return [
            tarea
            for tarea in self.registro_tareas.cargar()
            if tarea.id in ids
        ]

    def _tareas_no_asociadas(
        self,
        proyecto_id: str | None,
    ) -> list[TareaEscritorio]:
        asociadas = set()

        for sesion in self.gestor_sesiones.listar():
            asociadas.update(
                sesion.tareas_relacionadas
                or []
            )

        salida = []

        for tarea in self.registro_tareas.cargar():
            if tarea.id in asociadas:
                continue

            if self._tarea_terminal(tarea):
                continue

            if (
                proyecto_id
                and tarea.proyecto_id
                and tarea.proyecto_id != proyecto_id
            ):
                continue

            salida.append(tarea)

        salida.sort(
            key=lambda t: (
                t.prioridad,
                t.progreso,
            ),
            reverse=True,
        )

        return salida

    # =========================================================
    # DECIDIR
    # =========================================================

    def decidir(
        self,
    ) -> DecisionSupervisorSesion:
        contexto = self.contexto_operativo.cargar()
        sesion = self.gestor_sesiones.activa()

        # -----------------------------------------------------
        # NO HAY SESIÓN
        # -----------------------------------------------------

        if sesion is None:
            sesiones = self.gestor_sesiones.listar()

            pausadas = [
                s for s in sesiones
                if s.estado == EstadoSesionTrabajo.PAUSADA
            ]

            if pausadas:
                pausadas.sort(
                    key=lambda s: s.actualizada_en or s.creada_en,
                    reverse=True,
                )

                elegida = pausadas[0]

                return DecisionSupervisorSesion(
                    tipo=TipoDecisionSupervisorSesion.REANUDAR_SESION,
                    actuar=True,
                    motivo=(
                        "No existe una sesión activa y hay una sesión "
                        "pausada que puede continuar."
                    ),
                    sesion_id=elegida.id,
                    prioridad=0.82,
                    confianza=0.96,
                )

            if (
                contexto.proyecto_actual_id
                or contexto.ruta_proyecto_actual
                or contexto.ultima_tarea_id
            ):
                nombre = (
                    contexto.nombre_proyecto_actual
                    or "Sesión autónoma de trabajo"
                )

                objetivo = (
                    contexto.metadata.get("objetivo_superior")
                    or (
                        f"Continuar el trabajo pendiente de "
                        f"{nombre} hasta alcanzar un estado estable."
                    )
                )

                return DecisionSupervisorSesion(
                    tipo=TipoDecisionSupervisorSesion.CREAR_SESION,
                    actuar=True,
                    motivo=(
                        "Existe contexto operativo de trabajo, "
                        "pero no hay una sesión activa."
                    ),
                    prioridad=0.80,
                    confianza=0.88,
                    argumentos={
                        "nombre": nombre,
                        "objetivo_superior": objetivo,
                        "proyecto_id": contexto.proyecto_actual_id,
                        "resultado_esperado": (
                            contexto.metadata.get(
                                "resultado_esperado"
                            )
                        ),
                    },
                )

            return DecisionSupervisorSesion(
                tipo=TipoDecisionSupervisorSesion.NADA,
                actuar=False,
                motivo=(
                    "No existe una sesión activa ni contexto "
                    "suficiente para crear una automáticamente."
                ),
            )

        # -----------------------------------------------------
        # SESIÓN BLOQUEADA
        # -----------------------------------------------------

        if sesion.estado == EstadoSesionTrabajo.BLOQUEADA:
            return DecisionSupervisorSesion(
                tipo=TipoDecisionSupervisorSesion.NADA,
                actuar=False,
                motivo=(
                    "La sesión está bloqueada y requiere resolver "
                    "sus bloqueos antes de continuar."
                ),
                sesion_id=sesion.id,
            )

        # -----------------------------------------------------
        # TAREAS DE SESIÓN
        # -----------------------------------------------------

        tareas = self._tareas_de_sesion(sesion)

        if sesion.tarea_actual_id:
            actual = self.registro_tareas.obtener(
                sesion.tarea_actual_id
            )

            if actual is not None:
                if self._tarea_ejecutable(actual):
                    return DecisionSupervisorSesion(
                        tipo=TipoDecisionSupervisorSesion.CONTINUAR_TAREA,
                        actuar=True,
                        motivo=(
                            "La sesión ya tiene una tarea actual ejecutable."
                        ),
                        sesion_id=sesion.id,
                        tarea_id=actual.id,
                        prioridad=max(
                            0.70,
                            actual.prioridad,
                        ),
                        confianza=0.98,
                    )

                if self._tarea_bloqueada(actual):
                    otras = [
                        t for t in tareas
                        if (
                            t.id != actual.id
                            and self._tarea_ejecutable(t)
                        )
                    ]

                    if otras:
                        otras.sort(
                            key=lambda t: (
                                t.prioridad,
                                t.progreso,
                            ),
                            reverse=True,
                        )

                        return DecisionSupervisorSesion(
                            tipo=TipoDecisionSupervisorSesion.ASOCIAR_TAREA,
                            actuar=True,
                            motivo=(
                                "La tarea actual requiere confirmación, "
                                "pero la sesión tiene otra tarea ejecutable."
                            ),
                            sesion_id=sesion.id,
                            tarea_id=otras[0].id,
                            prioridad=otras[0].prioridad,
                            confianza=0.94,
                        )

                    return DecisionSupervisorSesion(
                        tipo=TipoDecisionSupervisorSesion.BLOQUEAR_SESION,
                        actuar=True,
                        motivo=(
                            "La única tarea disponible requiere "
                            "confirmación humana."
                        ),
                        sesion_id=sesion.id,
                        tarea_id=actual.id,
                        prioridad=0.90,
                        confianza=0.98,
                        argumentos={
                            "bloqueo": (
                                "Tarea pendiente de confirmación: "
                                + actual.nombre
                            )
                        },
                    )

        ejecutables = [
            tarea
            for tarea in tareas
            if self._tarea_ejecutable(tarea)
        ]

        if ejecutables:
            ejecutables.sort(
                key=lambda t: (
                    t.prioridad,
                    t.progreso,
                ),
                reverse=True,
            )

            return DecisionSupervisorSesion(
                tipo=TipoDecisionSupervisorSesion.ASOCIAR_TAREA,
                actuar=True,
                motivo=(
                    "La sesión no tiene tarea actual, pero existe "
                    "una tarea relacionada ejecutable."
                ),
                sesion_id=sesion.id,
                tarea_id=ejecutables[0].id,
                prioridad=ejecutables[0].prioridad,
                confianza=0.96,
            )

        # -----------------------------------------------------
        # BUSCAR TAREA PENDIENTE NO ASOCIADA
        # -----------------------------------------------------

        externas = self._tareas_no_asociadas(
            sesion.proyecto_id
        )

        if externas:
            return DecisionSupervisorSesion(
                tipo=TipoDecisionSupervisorSesion.ASOCIAR_TAREA,
                actuar=True,
                motivo=(
                    "Existe una tarea pendiente compatible con "
                    "la sesión actual."
                ),
                sesion_id=sesion.id,
                tarea_id=externas[0].id,
                prioridad=externas[0].prioridad,
                confianza=0.86,
            )

        # -----------------------------------------------------
        # TERMINAR O GENERAR MÁS TRABAJO
        # -----------------------------------------------------

        if tareas:
            terminales = [
                tarea
                for tarea in tareas
                if self._tarea_terminal(tarea)
            ]

            fallidas = [
                tarea
                for tarea in terminales
                if tarea.estado == EstadoTareaEscritorio.FALLIDA
            ]

            if (
                len(terminales) == len(tareas)
                and not fallidas
            ):
                return DecisionSupervisorSesion(
                    tipo=TipoDecisionSupervisorSesion.COMPLETAR_SESION,
                    actuar=True,
                    motivo=(
                        "Todas las tareas relacionadas terminaron "
                        "correctamente."
                    ),
                    sesion_id=sesion.id,
                    prioridad=0.92,
                    confianza=0.92,
                )

        # Si el objetivo no está demostrado como completado,
        # generar siguiente tarea en lugar de cerrar a ciegas.
        return DecisionSupervisorSesion(
            tipo=TipoDecisionSupervisorSesion.GENERAR_TAREA,
            actuar=True,
            motivo=(
                "La sesión sigue activa, no hay una tarea ejecutable "
                "y el objetivo superior aún no está cerrado."
            ),
            sesion_id=sesion.id,
            prioridad=0.78,
            confianza=0.82,
            argumentos={
                "objetivo": sesion.objetivo_superior,
            },
        )

    # =========================================================
    # EJECUTAR DECISIÓN DEL SUPERVISOR
    # =========================================================

    def aplicar(
        self,
        decision: DecisionSupervisorSesion,
        crear_tarea_desde_objetivo,
    ) -> ResultadoSupervisorSesion:
        if not decision.actuar:
            return ResultadoSupervisorSesion(
                ok=True,
                decision=decision,
                mensaje=decision.motivo,
            )

        # -----------------------------------------------------
        # CREAR SESIÓN
        # -----------------------------------------------------

        if decision.tipo == TipoDecisionSupervisorSesion.CREAR_SESION:
            sesion = self.gestor_sesiones.crear(
                nombre=str(
                    decision.argumentos.get(
                        "nombre",
                        "Sesión autónoma",
                    )
                ),
                objetivo_superior=str(
                    decision.argumentos.get(
                        "objetivo_superior",
                        "",
                    )
                ),
                proyecto_id=(
                    decision.argumentos.get(
                        "proyecto_id"
                    )
                ),
                resultado_esperado=(
                    decision.argumentos.get(
                        "resultado_esperado"
                    )
                ),
                metadata={
                    "creada_por_supervisor": True,
                },
                activar=True,
            )

            self.contexto_operativo.actualizar(
                metadata={
                    "sesion_trabajo_id": sesion.id,
                    "sesion_trabajo_nombre": sesion.nombre,
                    "objetivo_superior": sesion.objetivo_superior,
                }
            )

            return ResultadoSupervisorSesion(
                ok=True,
                decision=decision,
                sesion=sesion,
                mensaje="Sesión de trabajo autónoma creada.",
            )

        # -----------------------------------------------------
        # REANUDAR
        # -----------------------------------------------------

        if decision.tipo == TipoDecisionSupervisorSesion.REANUDAR_SESION:
            sesion = self.gestor_sesiones.reanudar(
                str(decision.sesion_id)
            )

            return ResultadoSupervisorSesion(
                ok=(sesion is not None),
                decision=decision,
                sesion=sesion,
                mensaje=(
                    "Sesión reanudada."
                    if sesion is not None
                    else "No se pudo reanudar la sesión."
                ),
                error=(
                    None
                    if sesion is not None
                    else "sesion_no_encontrada"
                ),
            )

        # -----------------------------------------------------
        # ASOCIAR TAREA
        # -----------------------------------------------------

        if decision.tipo == TipoDecisionSupervisorSesion.ASOCIAR_TAREA:
            sesion = self.gestor_sesiones.asociar_tarea(
                sesion_id=str(decision.sesion_id),
                tarea_id=str(decision.tarea_id),
                hacer_actual=True,
            )

            tarea = self.registro_tareas.obtener(
                str(decision.tarea_id)
            )

            return ResultadoSupervisorSesion(
                ok=(sesion is not None and tarea is not None),
                decision=decision,
                sesion=sesion,
                tarea=tarea,
                mensaje="Tarea asociada a la sesión.",
                error=(
                    None
                    if sesion is not None and tarea is not None
                    else "asociacion_tarea_fallida"
                ),
            )

        # -----------------------------------------------------
        # GENERAR TAREA
        # -----------------------------------------------------

        if decision.tipo == TipoDecisionSupervisorSesion.GENERAR_TAREA:
            sesion = self.gestor_sesiones.obtener(
                str(decision.sesion_id)
            )

            if sesion is None:
                return ResultadoSupervisorSesion(
                    ok=False,
                    decision=decision,
                    error="sesion_no_encontrada",
                )

            contexto = self.contexto_operativo.para_planificacion()
            contexto["sesion_id"] = sesion.id
            contexto["objetivo_superior"] = sesion.objetivo_superior

            tarea = crear_tarea_desde_objetivo(
                objetivo=str(
                    decision.argumentos.get(
                        "objetivo",
                        sesion.objetivo_superior,
                    )
                ),
                contexto=contexto,
                prioridad=max(
                    0.70,
                    decision.prioridad,
                ),
                creada_por="supervisor_sesion",
                proyecto_id=sesion.proyecto_id,
            )

            self.gestor_sesiones.asociar_tarea(
                sesion_id=sesion.id,
                tarea_id=tarea.id,
                hacer_actual=True,
            )

            return ResultadoSupervisorSesion(
                ok=True,
                decision=decision,
                sesion=self.gestor_sesiones.obtener(sesion.id),
                tarea=tarea,
                mensaje="El supervisor generó la siguiente tarea.",
            )

        # -----------------------------------------------------
        # CONTINUAR TAREA
        # -----------------------------------------------------

        if decision.tipo == TipoDecisionSupervisorSesion.CONTINUAR_TAREA:
            sesion = self.gestor_sesiones.obtener(
                str(decision.sesion_id)
            )

            tarea = self.registro_tareas.obtener(
                str(decision.tarea_id)
            )

            return ResultadoSupervisorSesion(
                ok=(sesion is not None and tarea is not None),
                decision=decision,
                sesion=sesion,
                tarea=tarea,
                mensaje=(
                    "La tarea actual está lista para continuar "
                    "en el ciclo autónomo."
                ),
                error=(
                    None
                    if sesion is not None and tarea is not None
                    else "tarea_actual_no_disponible"
                ),
            )

        # -----------------------------------------------------
        # COMPLETAR
        # -----------------------------------------------------

        if decision.tipo == TipoDecisionSupervisorSesion.COMPLETAR_SESION:
            sesion = self.gestor_sesiones.completar(
                sesion_id=str(decision.sesion_id),
                resultado=(
                    "Objetivo superior cerrado por el supervisor "
                    "tras completar sus tareas relacionadas."
                ),
            )

            return ResultadoSupervisorSesion(
                ok=(sesion is not None),
                decision=decision,
                sesion=sesion,
                mensaje="Sesión de trabajo completada.",
                error=(
                    None
                    if sesion is not None
                    else "sesion_no_encontrada"
                ),
            )

        # -----------------------------------------------------
        # BLOQUEAR
        # -----------------------------------------------------

        if decision.tipo == TipoDecisionSupervisorSesion.BLOQUEAR_SESION:
            sesion = self.gestor_sesiones.bloquear(
                sesion_id=str(decision.sesion_id),
                motivo=str(
                    decision.argumentos.get(
                        "bloqueo",
                        decision.motivo,
                    )
                ),
            )

            return ResultadoSupervisorSesion(
                ok=(sesion is not None),
                decision=decision,
                sesion=sesion,
                mensaje="Sesión bloqueada de forma controlada.",
                error=(
                    None
                    if sesion is not None
                    else "sesion_no_encontrada"
                ),
            )

        return ResultadoSupervisorSesion(
            ok=False,
            decision=decision,
            error="decision_supervisor_no_soportada",
        )