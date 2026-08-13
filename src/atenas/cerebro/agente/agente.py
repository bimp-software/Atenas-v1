from __future__ import annotations

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from src.atenas.memoria.store_manager import (
    StorageManager,
)

from src.atenas.herramientas import (
    ToolExecutor,
)

from .objetivos import (
    GestorObjetivos,
    Objetivo,
)

from .pendientes import (
    GestorPendientes,
    EstadoPendiente,
)

from .estado_mundo import EstadoMundo

from .decision_engine import (
    DecisionEngine,
    Decision,
)

from .detector_necesidades import (
    DetectorNecesidades,
)

from .planificador_inteligente import (
    PlanificadorInteligente,
)

from .persistencia import (
    PersistenciaAgente,
)


class AgenteAtenas:

    def __init__(
        self,
        storage: StorageManager | None = None,
        llm: OllamaClient | None = None,
    ):

        # =====================================================
        # RECURSOS COMPARTIDOS
        # =====================================================

        self.storage = (
            storage
            or StorageManager()
        )

        self.llm = llm

        # =====================================================
        # ESTADO DEL AGENTE
        # =====================================================

        self.estado = EstadoMundo()

        self.objetivos = (
            GestorObjetivos()
        )

        self.pendientes = (
            GestorPendientes()
        )

        self.decisiones = (
            DecisionEngine()
        )

        # =====================================================
        # COMPONENTES
        # =====================================================

        self.detector_necesidades = (
            DetectorNecesidades(
                storage=self.storage
            )
        )

        self.planificador = (
            PlanificadorInteligente(
                llm=self.llm
            )
        )

        self.executor = (
            ToolExecutor()
        )

        self.persistencia = (
            PersistenciaAgente(
                self.storage.db
            )
        )

        # =====================================================
        # RECUPERAR ESTADO PERSISTENTE
        # =====================================================

        self.objetivos.cargar(
            self.persistencia
            .cargar_objetivos()
        )

        self.pendientes.cargar(
            self.persistencia
            .cargar_pendientes()
        )

        # =====================================================
        # OBJETIVOS BASE
        # =====================================================

        self._asegurar_objetivos_base()

    # =========================================================
    # OBJETIVOS BASE
    # =========================================================

    def _asegurar_objetivos_base(
        self,
    ) -> None:

        if (
            self.objetivos.obtener(
                "documentar_atenas"
            )
            is None
        ):

            self.agregar_objetivo(
                Objetivo(
                    id="documentar_atenas",
                    nombre=(
                        "Documentar desarrollo "
                        "de Atenas"
                    ),
                    descripcion=(
                        "Mantener un registro útil "
                        "de decisiones y cambios "
                        "importantes relacionados "
                        "con el desarrollo de Atenas, "
                        "incluyendo software, robótica, "
                        "hardware, visión, voz y memoria."
                    ),
                    prioridad=0.8,
                    autonomia=True,
                )
            )

    # =========================================================
    # AGREGAR OBJETIVO
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

        mensaje = mensaje.strip()

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

        creados = []

        for necesidad in necesidades:

            # =================================================
            # EVITAR DUPLICADOS DEL MISMO MENSAJE
            # =================================================

            ya_existe = any(
                (
                    pendiente.objetivo_id
                    == necesidad.objetivo_id
                    and (
                        pendiente.mensaje_origen
                        or ""
                    ).lower()
                    == mensaje.lower()
                )
                for pendiente
                in self.pendientes.pendientes()
            )

            if ya_existe:
                continue

            pendiente = (
                self.pendientes.crear(
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

            creados.append(
                pendiente
            )

        return creados

    # =========================================================
    # CREAR PENDIENTE MANUAL
    # =========================================================

    def crear_pendiente(
        self,
        descripcion: str,
        objetivo_id: str | None = None,
        prioridad: float = 0.5,
        requiere_confirmacion: bool = False,
        accion_sugerida: str | None = None,
        mensaje_origen: str | None = None,
    ):

        pendiente = (
            self.pendientes.crear(
                descripcion=descripcion,
                objetivo_id=objetivo_id,
                prioridad=prioridad,
                requiere_confirmacion=(
                    requiere_confirmacion
                ),
                accion_sugerida=(
                    accion_sugerida
                ),
                mensaje_origen=(
                    mensaje_origen
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
        pendiente_id: str | None = None,
    ) -> dict:

        # =====================================================
        # PENDIENTE ESPECÍFICO DEL TURNO ACTUAL
        # =====================================================

        if pendiente_id is not None:

            pendiente = (
                self.pendientes.obtener(
                    pendiente_id
                )
            )

            if pendiente is None:

                return {
                    "decision": None,
                    "plan": None,
                    "error": (
                        "El pendiente solicitado "
                        "no existe."
                    ),
                }

            decision = Decision(
                actuar=True,
                motivo=(
                    "Se está evaluando una necesidad "
                    "detectada en el turno actual."
                ),
                objetivo_id=(
                    pendiente.objetivo_id
                ),
                pendiente_id=(
                    pendiente.id
                ),
                confianza=0.95,
            )

        # =====================================================
        # MODO GENERAL
        # =====================================================

        else:

            decision = (
                self.decisiones.decidir(
                    estado=self.estado,
                    objetivos=self.objetivos,
                    pendientes=self.pendientes,
                )
            )

            if not decision.actuar:

                return {
                    "decision": decision,
                    "plan": None,
                }

            pendiente = (
                self.pendientes.obtener(
                    decision.pendiente_id
                )
                if decision.pendiente_id
                else None
            )

        # =====================================================
        # SIN PENDIENTE
        # =====================================================

        if pendiente is None:

            return {
                "decision": decision,
                "plan": None,
            }

        # =====================================================
        # PLANIFICAR
        # =====================================================

        try:

            plan = (
                self.planificador.crear_plan(
                    pendiente
                )
            )

        except Exception as error:

            print(
                "[ATENAS][PLANIFICADOR] "
                f"No pudo crear un plan: {error}"
            )

            return {
                "decision": decision,
                "plan": None,
                "error": str(error),
            }

        return {
            "decision": decision,
            "plan": plan,
        }

    # =========================================================
    # ACTUAR
    # =========================================================

    def actuar(
        self,
        pendiente_id: str | None = None,
    ) -> dict:

        pensamiento = self.pensar(
            pendiente_id=pendiente_id
        )

        decision = pensamiento.get(
            "decision"
        )

        plan = pensamiento.get(
            "plan"
        )

        # =====================================================
        # NO HUBO DECISIÓN
        # =====================================================

        if decision is None:

            return {
                "actuo": False,
                "exito": False,
                "decision": None,
                "plan": plan,
                "resultados": [],
                "error": pensamiento.get(
                    "error",
                    (
                        "ATENAS no pudo tomar "
                        "una decisión."
                    ),
                ),
            }

        # =====================================================
        # NO HAY NADA QUE HACER
        # =====================================================

        if (
            not decision.actuar
            or plan is None
        ):

            return {
                "actuo": False,
                "exito": None,
                "decision": decision,
                "plan": plan,
                "resultados": [],
            }

        pendiente_id = (
            decision.pendiente_id
        )

        if pendiente_id is None:

            return {
                "actuo": False,
                "exito": False,
                "decision": decision,
                "plan": plan,
                "resultados": [],
                "error": (
                    "La decisión no contiene "
                    "un pendiente."
                ),
            }

        pendiente = (
            self.pendientes.obtener(
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
                    "no existe."
                ),
            }

        # =====================================================
        # PLAN VACÍO
        # =====================================================

        if not plan.pasos:

            self.pendientes.completar(
                pendiente_id,
                resultado=(
                    "ATENAS determinó que "
                    "no era necesario ejecutar "
                    "ninguna herramienta."
                ),
            )

            self.persistencia.guardar_pendiente(
                pendiente
            )

            return {
                "actuo": False,
                "exito": True,
                "decision": decision,
                "plan": plan,
                "resultados": [],
                "pasos_ejecutados": 0,
            }

        # =====================================================
        # MARCAR EN PROCESO
        # =====================================================

        self.pendientes.iniciar(
            pendiente_id
        )

        self.persistencia.guardar_pendiente(
            pendiente
        )

        resultados = []

        # =====================================================
        # EJECUTAR PLAN
        # =====================================================

        for numero_paso, paso in enumerate(
            plan.pasos,
            start=1,
        ):

            # =================================================
            # CONFIRMACIÓN
            # =================================================

            if paso.requiere_confirmacion:

                pendiente.estado = (
                    EstadoPendiente.PENDIENTE
                )

                pendiente.resultado = (
                    f"El paso {numero_paso} "
                    f"'{paso.herramienta}' "
                    "requiere confirmación."
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
                }

            # =================================================
            # EJECUTAR HERRAMIENTA
            # =================================================

            resultado = (
                self.executor.ejecutar(
                    paso.herramienta,
                    paso.argumentos,
                )
            )

            resultados.append(
                resultado
            )

            # =================================================
            # REGISTRAR ACCIÓN
            # =================================================

            try:

                self.persistencia.registrar_accion(
                    pendiente_id=pendiente_id,
                    herramienta=(
                        paso.herramienta
                    ),
                    argumentos=(
                        paso.argumentos
                    ),
                    resultado=resultado,
                )

            except Exception as error:

                print(
                    "[ATENAS][AGENTE][HISTORIAL] "
                    f"{error}"
                )

            # =================================================
            # ERROR DE HERRAMIENTA
            # =================================================

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

        # =====================================================
        # COMPLETADO
        # =====================================================

        self.pendientes.completar(
            pendiente_id,
            resultado=(
                "Plan ejecutado correctamente."
            ),
        )

        self.persistencia.guardar_pendiente(
            pendiente
        )

        return {
            "actuo": True,
            "exito": True,
            "decision": decision,
            "plan": plan,
            "resultados": resultados,
            "pasos_ejecutados": (
                len(resultados)
            ),
        }