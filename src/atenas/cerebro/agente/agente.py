from __future__ import annotations

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
)

from .planificador import (
    Planificador,
)

from .detector_necesidades import DetectorNecesidades
from src.atenas.memoria.store_manager import StorageManager
from src.atenas.herramientas import ToolExecutor
from .persistencia import PersistenciaAgente

from .planificador_inteligente import (
    PlanificadorInteligente,
)


class AgenteAtenas:

    def __init__(
        self,
        storage: StorageManager | None = None,
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

        # =====================================================
        # RECUPERAR ESTADO DEL AGENTE
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
    # REGISTRAR OBJETIVO
    # =====================================================

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

    # =====================================================
    # REGISTRAR NUEVO CONTEXTO
    # =====================================================

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
            self.detector_necesidades.detectar(
                mensaje=mensaje,
                objetivos=self.objetivos,
            )
        )

        pendientes_creados = []

        for necesidad in necesidades:

            # Evitar pendientes muy similares
            # al mismo mensaje.

            ya_existe = any(
                (
                    pendiente.objetivo_id
                    == necesidad.objetivo_id
                    and mensaje.lower()
                    in pendiente.descripcion.lower()
                )
                for pendiente
                in self.pendientes.pendientes()
            )

            if ya_existe:
                continue

            pendiente = self.pendientes.crear(
                descripcion=necesidad.descripcion,
                objetivo_id=necesidad.objetivo_id,
                prioridad=necesidad.prioridad,
                requiere_confirmacion=False,
                accion_sugerida=necesidad.accion_sugerida,
                mensaje_origen=mensaje,
            )

            self.persistencia.guardar_pendiente(pendiente)

            pendientes_creados.append(
                pendiente
            )

        return pendientes_creados

    # =====================================================
    # CREAR PENDIENTE
    # =====================================================

    def crear_pendiente(
        self,
        descripcion: str,
        objetivo_id: str | None = None,
        prioridad: float = 0.5,
        requiere_confirmacion: bool = False,
    ):

        return self.pendientes.crear(
            descripcion=descripcion,
            objetivo_id=objetivo_id,
            prioridad=prioridad,
            requiere_confirmacion=requiere_confirmacion,
        )

    # =====================================================
    # PENSAR
    # =====================================================

    def pensar(self):

        decision = self.decisiones.decidir(
            estado=self.estado,
            objetivos=self.objetivos,
            pendientes=self.pendientes,
        )

        if not decision.actuar:
            return {
                "decision": decision,
                "plan": None,
            }

        pendiente = next(
            (
                p
                for p in self.pendientes.pendientes()
                if p.id == decision.pendiente_id
            ),
            None,
        )

        if pendiente is None:
            return {
                "decision": decision,
                "plan": None,
            }

        plan = self.planificador.crear_plan(
            pendiente
        )

        return {
            "decision": decision,
            "plan": plan,
        }

    def actuar(self) -> dict:
        # =====================================================
        # 1. PENSAR
        # =====================================================

        resultado_pensamiento = self.pensar()

        decision = resultado_pensamiento["decision"]
        plan = resultado_pensamiento["plan"]

        # =====================================================
        # 2. NO HAY NADA QUE HACER
        # =====================================================

        if not decision.actuar or plan is None:

            return {
                "actuo": False,
                "exito": None,
                "decision": decision,
                "plan": plan,
                "resultados": [],
            }

        pendiente_id = decision.pendiente_id

        if pendiente_id is None:

            return {
                "actuo": False,
                "exito": None,
                "decision": decision,
                "plan": plan,
                "resultados": [],
            }

        # =====================================================
        # 3. OBTENER PENDIENTE
        # =====================================================

        pendiente = self.pendientes.obtener(
            pendiente_id
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

        # =====================================================
        # 4. MARCAR COMO EN PROCESO
        # =====================================================

        self.pendientes.iniciar(
            pendiente_id
        )

        # Guardamos inmediatamente el nuevo estado.
        pendiente = self.pendientes.obtener(
            pendiente_id
        )

        if pendiente is not None:

            self.persistencia.guardar_pendiente(
                pendiente
            )

        resultados = []

        # =====================================================
        # 5. EJECUTAR LOS PASOS DEL PLAN
        # =====================================================

        for numero_paso, paso in enumerate(
            plan.pasos,
            start=1,
        ):

            # -------------------------------------------------
            # REQUIERE CONFIRMACIÓN
            # -------------------------------------------------

            if paso.requiere_confirmacion:

                mensaje = (
                    f"El paso {numero_paso} "
                    f"'{paso.herramienta}' "
                    "requiere confirmación."
                )

                # Importante:
                # no deberíamos marcarlo como completado.
                #
                # Por ahora lo devolvemos a pendiente
                # para poder retomarlo después.

                pendiente.estado = (
                    EstadoPendiente.PENDIENTE
                )

                pendiente.resultado = mensaje

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

            # -------------------------------------------------
            # EJECUTAR HERRAMIENTA
            # -------------------------------------------------

            resultado = self.executor.ejecutar(
                paso.herramienta,
                paso.argumentos,
            )

            resultados.append(
                resultado
            )

            # -------------------------------------------------
            # REGISTRAR ACCIÓN
            # -------------------------------------------------

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
                    "No se pudo registrar la acción: "
                    f"{error}"
                )

            # -------------------------------------------------
            # LA HERRAMIENTA FALLÓ
            # -------------------------------------------------

            if not resultado.get(
                "ok",
                False,
            ):

                mensaje_error = (
                    resultado.get("mensaje")
                    or resultado.get("error")
                    or "Error desconocido."
                )

                self.pendientes.fallar(
                    pendiente_id,
                    resultado=mensaje_error,
                )

                pendiente = self.pendientes.obtener(
                    pendiente_id
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

        # =====================================================
        # 6. TODOS LOS PASOS TERMINARON CORRECTAMENTE
        # =====================================================

        self.pendientes.completar(
            pendiente_id,
            resultado=(
                "Plan ejecutado correctamente."
            ),
        )

        pendiente = self.pendientes.obtener(
            pendiente_id
        )

        if pendiente is not None:

            self.persistencia.guardar_pendiente(
                pendiente
            )

        # =====================================================
        # 7. RESULTADO FINAL
        # =====================================================

        return {
            "actuo": True,
            "exito": True,
            "decision": decision,
            "plan": plan,
            "resultados": resultados,
            "pasos_ejecutados": len(resultados),
        }