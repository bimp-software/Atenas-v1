from __future__ import annotations

from typing import Any

from .objetivos import (
    GestorObjetivos,
    Objetivo,
)

from .pendientes import (
    EstadoPendiente,
    GestorPendientes,
)

from .estado_mundo import EstadoMundo

from .decision_engine import (
    Decision,
    DecisionEngine,
    TipoDecisionAgente,
)

from .detector_necesidades import (
    DetectorNecesidades,
)

from .persistencia import (
    PersistenciaAgente,
)

from .planificador_inteligente import (
    PlanificadorInteligente,
)

from .capacidad_desarrollo import (
    CapacidadDesarrollo,
    ResultadoCapacidadDesarrollo,
)

from .capacidad_sistema import (
    CapacidadSistema,
    ResultadoCapacidadSistema,
)

from src.atenas.memoria.store_manager import (
    StorageManager,
)

from src.atenas.herramientas import (
    ToolExecutor,
)


class AgenteAtenas:
    """
    Agente principal de ATENAS V2.

    Integra:
    - observación;
    - detección de necesidades;
    - objetivos y pendientes persistentes;
    - herramientas simples;
    - capacidades complejas;
    - creación de proyectos de software;
    - continuación autónoma de proyectos.
    """

    def __init__(
        self,
        storage: StorageManager | None = None,
        capacidad_desarrollo: (
            CapacidadDesarrollo
            | None
        ) = None,
        capacidad_sistema: (
            CapacidadSistema
            | None
        ) = None,
    ):

        self.storage = (
            storage
            or StorageManager()
        )

        self.estado = EstadoMundo()
        self.objetivos = GestorObjetivos()
        self.pendientes = GestorPendientes()
        self.decisiones = DecisionEngine()

        self.planificador = (
            PlanificadorInteligente()
        )

        self.detector_necesidades = (
            DetectorNecesidades(
                storage=self.storage
            )
        )

        self.executor = ToolExecutor()

        self.persistencia = (
            PersistenciaAgente(
                self.storage.db
            )
        )

        self.capacidad_desarrollo = (
            capacidad_desarrollo
            or CapacidadDesarrollo(
                llm=self.planificador.llm
            )
        )

        self.capacidad_sistema = (
            capacidad_sistema
            or CapacidadSistema()
        )

        self.objetivos.cargar(
            self.persistencia
            .cargar_objetivos()
        )

        self.pendientes.cargar(
            self.persistencia
            .cargar_pendientes()
        )

    # =========================================================
    # OBJETIVOS
    # =========================================================

    def agregar_objetivo(
        self,
        objetivo: Objetivo,
    ) -> None:

        self.objetivos.agregar(
            objetivo
        )

        self.persistencia.guardar_objetivo(
            objetivo
        )

    # =========================================================
    # OBSERVAR
    # =========================================================

    def observar(
        self,
        mensaje: str,
    ) -> list:

        mensaje = (
            mensaje
            or ""
        ).strip()

        if not mensaje:
            return []

        self.estado.actualizar_mensaje(
            mensaje
        )

        necesidades = (
            self.detector_necesidades
            .detectar(
                mensaje=mensaje,
                objetivos=self.objetivos,
            )
        )

        pendientes_creados = []

        for necesidad in necesidades:

            ya_existe = any(
                (
                    (
                        pendiente.accion_sugerida
                        == necesidad.accion_sugerida
                    )
                    and (
                        pendiente.mensaje_origen
                        or ""
                    ).strip().lower()
                    == mensaje.lower()
                )
                for pendiente
                in self.pendientes.pendientes()
            )

            if ya_existe:
                continue

            pendiente = (
                self.pendientes
                .crear(
                    descripcion=(
                        necesidad.descripcion
                    ),
                    objetivo_id=(
                        necesidad.objetivo_id
                    ),
                    prioridad=(
                        necesidad.prioridad
                    ),
                    requiere_confirmacion=False,
                    accion_sugerida=(
                        necesidad.accion_sugerida
                    ),
                    mensaje_origen=mensaje,
                )
            )

            self.persistencia.guardar_pendiente(
                pendiente
            )

            pendientes_creados.append(
                pendiente
            )

        return pendientes_creados

    # =========================================================
    # CREAR PENDIENTE
    # =========================================================

    def crear_pendiente(
        self,
        descripcion: str,
        objetivo_id: str | None = None,
        prioridad: float = 0.5,
        requiere_confirmacion: bool = False,
    ):

        pendiente = (
            self.pendientes
            .crear(
                descripcion=descripcion,
                objetivo_id=objetivo_id,
                prioridad=prioridad,
                requiere_confirmacion=(
                    requiere_confirmacion
                ),
            )
        )

        self.persistencia.guardar_pendiente(
            pendiente
        )

        return pendiente

    # =========================================================
    # PENSAR
    # =========================================================

    def pensar(
        self,
        permitir_iniciativa_desarrollo: bool = True,
    ) -> dict:

        decision = (
            self.decisiones
            .decidir_ampliado(
                estado=self.estado,
                objetivos=self.objetivos,
                pendientes=self.pendientes,
                capacidad_desarrollo=(
                    self.capacidad_desarrollo
                ),
                permitir_iniciativa_desarrollo=(
                    permitir_iniciativa_desarrollo
                ),
            )
        )

        if not decision.actuar:

            return {
                "decision": decision,
                "plan": None,
                "tipo": decision.tipo.value,
            }

        if (
            decision.capacidad
            in {
                "desarrollo_software",
                "sistema_computador",
            }
        ):

            return {
                "decision": decision,
                "plan": None,
                "tipo": decision.tipo.value,
            }

        pendiente = next(
            (
                p
                for p
                in self.pendientes
                .pendientes()
                if (
                    p.id
                    == decision.pendiente_id
                )
            ),
            None,
        )

        if pendiente is None:

            return {
                "decision": decision,
                "plan": None,
                "tipo": decision.tipo.value,
            }

        plan = (
            self.planificador
            .crear_plan(
                pendiente
            )
        )

        return {
            "decision": decision,
            "plan": plan,
            "tipo": decision.tipo.value,
        }

    # =========================================================
    # COMPLETAR PENDIENTE ASOCIADO A CAPACIDAD
    # =========================================================

    def _cerrar_pendiente_capacidad(
        self,
        decision: Decision,
        resultado: ResultadoCapacidadDesarrollo,
    ) -> None:

        if not decision.pendiente_id:
            return

        pendiente = (
            self.pendientes
            .obtener(
                decision.pendiente_id
            )
        )

        if pendiente is None:
            return

        if resultado.ok:

            self.pendientes.completar(
                decision.pendiente_id,
                resultado=(
                    resultado.mensaje
                    or "Capacidad ejecutada correctamente."
                ),
            )

        else:

            self.pendientes.fallar(
                decision.pendiente_id,
                resultado=(
                    resultado.error
                    or resultado.mensaje
                    or "La capacidad falló."
                ),
            )

        actualizado = (
            self.pendientes
            .obtener(
                decision.pendiente_id
            )
        )

        if actualizado is not None:

            self.persistencia.guardar_pendiente(
                actualizado
            )

    # =========================================================
    # CAPACIDAD DESARROLLO
    # =========================================================

    def _actuar_desarrollo(
        self,
        decision: Decision,
    ) -> dict:

        accion = (
            decision.accion_capacidad
            or ""
        )

        argumentos = (
            decision.argumentos
            or {}
        )

        try:

            if accion == "crear_proyecto":

                resultado = (
                    self.capacidad_desarrollo
                    .crear_proyecto(
                        descripcion=str(
                            argumentos.get(
                                "descripcion",
                                "",
                            )
                            or ""
                        ),
                        carpeta=(
                            argumentos.get(
                                "carpeta"
                            )
                        ),
                        nombre_sugerido=(
                            argumentos.get(
                                "nombre_sugerido"
                            )
                        ),
                        creado_por="agente",
                        prioridad=float(
                            argumentos.get(
                                "prioridad",
                                0.70,
                            )
                            or 0.70
                        ),
                        urgencia=float(
                            argumentos.get(
                                "urgencia",
                                0.0,
                            )
                            or 0.0
                        ),
                    )
                )

            elif accion == "continuar_proyecto":

                proyecto_id = (
                    argumentos.get(
                        "proyecto_id"
                    )
                    or decision.proyecto_id
                )

                if not proyecto_id:

                    return {
                        "actuo": False,
                        "exito": False,
                        "decision": decision,
                        "plan": None,
                        "resultados": [],
                        "error": (
                            "No se indicó proyecto_id."
                        ),
                    }

                resultado = (
                    self.capacidad_desarrollo
                    .continuar_proyecto(
                        proyecto_id=proyecto_id,
                        max_ciclos=int(
                            argumentos.get(
                                "max_ciclos",
                                1,
                            )
                            or 1
                        ),
                    )
                )

            elif accion == "consultar_estado":

                proyecto_id = (
                    argumentos.get(
                        "proyecto_id"
                    )
                    or decision.proyecto_id
                )

                if not proyecto_id:

                    return {
                        "actuo": False,
                        "exito": False,
                        "decision": decision,
                        "plan": None,
                        "resultados": [],
                        "error": (
                            "No se indicó proyecto_id."
                        ),
                    }

                resultado = (
                    self.capacidad_desarrollo
                    .estado_proyecto(
                        proyecto_id
                    )
                )

            elif accion == "listar_proyectos":

                resultado = (
                    self.capacidad_desarrollo
                    .listar_proyectos(
                        solo_activos=bool(
                            argumentos.get(
                                "solo_activos",
                                False,
                            )
                        )
                    )
                )

            else:

                return {
                    "actuo": False,
                    "exito": False,
                    "decision": decision,
                    "plan": None,
                    "resultados": [],
                    "error": (
                        f"Acción no soportada: {accion}"
                    ),
                }

        except Exception as error:

            return {
                "actuo": True,
                "exito": False,
                "decision": decision,
                "plan": None,
                "resultados": [],
                "capacidad": "desarrollo_software",
                "accion_capacidad": accion,
                "error": (
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            }

        self._cerrar_pendiente_capacidad(
            decision=decision,
            resultado=resultado,
        )

        return {
            "actuo": True,
            "exito": resultado.ok,
            "decision": decision,
            "plan": None,
            "resultados": [resultado],
            "capacidad": "desarrollo_software",
            "accion_capacidad": accion,
            "proyecto_id": resultado.proyecto_id,
            "estado_proyecto": resultado.estado,
            "progreso": resultado.progreso,
            "requiere_confirmacion": (
                resultado.requiere_confirmacion
            ),
            "dependencias_pendientes": (
                resultado.dependencias_pendientes
            ),
            "mensaje": resultado.mensaje,
            "error": resultado.error,
        }

    # =========================================================
    # PENDIENTE TRADICIONAL
    # =========================================================

    def _actuar_pendiente(
        self,
        decision: Decision,
        plan: Any,
    ) -> dict:

        if plan is None:

            return {
                "actuo": False,
                "exito": None,
                "decision": decision,
                "plan": None,
                "resultados": [],
            }

        pendiente_id = (
            decision.pendiente_id
        )

        if pendiente_id is None:

            return {
                "actuo": False,
                "exito": None,
                "decision": decision,
                "plan": plan,
                "resultados": [],
            }

        pendiente = (
            self.pendientes
            .obtener(
                pendiente_id
            )
        )

        if pendiente is None:

            return {
                "actuo": False,
                "exito": False,
                "decision": decision,
                "plan": plan,
                "resultados": [],
                "error": (
                    "El pendiente seleccionado "
                    "ya no existe."
                ),
            }

        self.pendientes.iniciar(
            pendiente_id
        )

        pendiente = (
            self.pendientes
            .obtener(
                pendiente_id
            )
        )

        if pendiente is not None:

            self.persistencia.guardar_pendiente(
                pendiente
            )

        resultados = []

        for numero_paso, paso in enumerate(
            plan.pasos,
            start=1,
        ):

            if paso.requiere_confirmacion:

                mensaje = (
                    f"El paso {numero_paso} "
                    f"'{paso.herramienta}' "
                    "requiere confirmación."
                )

                pendiente.estado = (
                    EstadoPendiente.PENDIENTE
                )

                pendiente.resultado = (
                    mensaje
                )

                self.persistencia.guardar_pendiente(
                    pendiente
                )

                return {
                    "actuo": False,
                    "exito": None,
                    "decision": decision,
                    "plan": plan,
                    "resultados": resultados,
                    "requiere_confirmacion": True,
                    "paso_pendiente": numero_paso,
                    "mensaje": mensaje,
                }

            resultado = (
                self.executor
                .ejecutar(
                    paso.herramienta,
                    paso.argumentos,
                )
            )

            resultados.append(
                resultado
            )

            try:

                self.persistencia.registrar_accion(
                    pendiente_id=pendiente_id,
                    herramienta=paso.herramienta,
                    argumentos=paso.argumentos,
                    resultado=resultado,
                )

            except Exception as error:

                print(
                    "[ATENAS][AGENTE][HISTORIAL] "
                    f"{error}"
                )

            if not resultado.get(
                "ok",
                False,
            ):

                mensaje_error = (
                    resultado.get(
                        "mensaje"
                    )
                    or resultado.get(
                        "error"
                    )
                    or "Error desconocido."
                )

                self.pendientes.fallar(
                    pendiente_id,
                    resultado=(
                        mensaje_error
                    ),
                )

                pendiente = (
                    self.pendientes
                    .obtener(
                        pendiente_id
                    )
                )

                if pendiente is not None:

                    self.persistencia.guardar_pendiente(
                        pendiente
                    )

                return {
                    "actuo": True,
                    "exito": False,
                    "decision": decision,
                    "plan": plan,
                    "resultados": resultados,
                    "paso_fallido": numero_paso,
                    "herramienta_fallida": (
                        paso.herramienta
                    ),
                    "error": mensaje_error,
                }

        self.pendientes.completar(
            pendiente_id,
            resultado=(
                "Plan ejecutado correctamente."
            ),
        )

        pendiente = (
            self.pendientes
            .obtener(
                pendiente_id
            )
        )

        if pendiente is not None:

            self.persistencia.guardar_pendiente(
                pendiente
            )

        return {
            "actuo": True,
            "exito": True,
            "decision": decision,
            "plan": plan,
            "resultados": resultados,
            "pasos_ejecutados": len(
                resultados
            ),
        }

    # =========================================================
    # REGISTRAR RESULTADO EN ESTADO MUNDO
    # =========================================================

    def _registrar_resultado_estado(
        self,
        resultado: dict,
    ) -> dict:

        decision = (
            resultado.get(
                "decision"
            )
        )

        accion = (
            resultado.get(
                "accion_capacidad"
            )
            or getattr(
                getattr(
                    decision,
                    "tipo",
                    None,
                ),
                "value",
                "sin_accion",
            )
        )

        try:

            self.estado.registrar_accion(
                accion=str(
                    accion
                ),
                ok=(
                    resultado.get(
                        "exito"
                    )
                ),
                datos={
                    "proyecto_id":
                        resultado.get(
                            "proyecto_id"
                        ),

                    "capacidad":
                        resultado.get(
                            "capacidad"
                        ),
                },
            )

        except Exception:
            pass

        return resultado

    # =========================================================
    # ACTUAR
    # =========================================================

    def actuar(
        self,
        permitir_iniciativa_desarrollo: bool = True,
    ) -> dict:

        pensamiento = (
            self.pensar(
                permitir_iniciativa_desarrollo=(
                    permitir_iniciativa_desarrollo
                )
            )
        )

        decision: Decision = (
            pensamiento[
                "decision"
            ]
        )

        plan = pensamiento[
            "plan"
        ]

        if not decision.actuar:

            return {
                "actuo": False,
                "exito": None,
                "decision": decision,
                "plan": plan,
                "resultados": [],
            }

        if (
            decision.capacidad
            == "desarrollo_software"
        ):

            return (
                self._actuar_desarrollo(
                    decision
                )
            )

        if (
            decision.capacidad
            == "sistema_computador"
        ):

            return (
                self._actuar_sistema(
                    decision
                )
            )

        return (
            self._actuar_pendiente(
                decision=decision,
                plan=plan,
            )
        )

    # =========================================================
    # API EXPLÍCITA
    # =========================================================

    def crear_proyecto_software(
        self,
        descripcion: str,
        nombre_sugerido: str | None = None,
        carpeta: str | None = None,
    ) -> ResultadoCapacidadDesarrollo:

        return (
            self.capacidad_desarrollo
            .crear_proyecto(
                descripcion=descripcion,
                nombre_sugerido=(
                    nombre_sugerido
                ),
                carpeta=carpeta,
                creado_por="usuario",
                prioridad=0.75,
                urgencia=0.0,
            )
        )

    def continuar_proyecto_software(
        self,
        proyecto_id: str,
        max_ciclos: int = 1,
    ) -> ResultadoCapacidadDesarrollo:

        return (
            self.capacidad_desarrollo
            .continuar_proyecto(
                proyecto_id=proyecto_id,
                max_ciclos=max_ciclos,
            )
        )

    def proyectos_software(
        self,
        solo_activos: bool = False,
    ) -> ResultadoCapacidadDesarrollo:

        return (
            self.capacidad_desarrollo
            .listar_proyectos(
                solo_activos=solo_activos
            )
        )


    def ejecutar_accion_sistema(
        self,
        texto: str,
        confirmada: bool = False,
    ) -> ResultadoCapacidadSistema:
        """
        API explícita para UI/usuario.
        """

        return (
            self.capacidad_sistema
            .ejecutar_desde_texto(
                texto=texto,
                es_autonoma=False,
                confirmada=confirmada,
            )
        )