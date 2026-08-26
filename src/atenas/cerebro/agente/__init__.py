from __future__ import annotations

from .catalogo_herramientas import (
    catalogo_para_llm,
)

from .catalogo_capacidades import (
    TipoCapacidadAgente,
    CapacidadAgente,
    capacidades_disponibles,
    capacidad_por_nombre,
    catalogo_capacidades_para_llm,
    es_capacidad,
)

from .gestor_ventanas import (
    VentanaSistema,
    ResultadoVentanas,
    GestorVentanas,
)

from .controlador_mouse import (
    BotonMouse,
    PosicionMouse,
    ResultadoMouse,
    ControladorMouse,
)

from .controlador_teclado import (
    TeclaEspecial,
    ResultadoTeclado,
    ControladorTeclado,
)

from .capturador_pantalla import (
    CapturaPantalla,
    ResultadoCapturaPantalla,
    CapturadorPantalla,
)

from .percepcion_visual import (
    EstadoVisual,
    ResultadoPercepcionVisual,
    PercepcionVisual,
)

from .interpretador_visual import (
    ElementoVisual,
    InterpretacionVisual,
    ResultadoInterpretacionVisual,
    InterpretadorVisual,
)

from .adaptador_vision_ollama import (
    EstadoVisionOllama,
    AdaptadorVisionOllama,
)

from .objetivo_visual import (
    TipoObjetivoVisual,
    ObjetivoVisual,
    ResultadoObjetivoVisual,
    ResolutorObjetivoVisual,
)

from .accion_gui import (
    TipoAccionGUI,
    AccionGUIPlanificada,
    ResultadoPlanGUI,
    PlanificadorGUI,
)

from .ejecutor_gui import (
    ResultadoEjecucionGUI,
    EjecutorGUI,
)

from .verificador_visual import (
    CriterioVerificacionVisual,
    ResultadoVerificacionVisual,
    VerificadorVisual,
)

from .ciclo_accion_gui import (
    ResultadoCicloGUI,
    CicloAccionGUI,
)

from .tareas_escritorio import (
    EstadoTareaEscritorio,
    EstadoPasoEscritorio,
    TipoPasoEscritorio,
    PasoTareaEscritorio,
    TareaEscritorio,
)

from .registro_tareas_escritorio import (
    RegistroTareasEscritorio,
)

from .orquestador_tareas_escritorio import (
    ResultadoPasoTarea,
    OrquestadorTareasEscritorio,
)

from .planificador_tareas_escritorio import (
    PlanTareaEscritorio,
    PlanificadorTareasEscritorio,
)

from .replanificador_tareas_escritorio import (
    ResultadoReplanificacion,
    ReplanificadorTareasEscritorio,
)

from .gestor_contexto_operativo import (
    ContextoOperativo,
    GestorContextoOperativo,
)

from .gestor_sesion_trabajo import (
    EstadoSesionTrabajo,
    SesionTrabajo,
    GestorSesionTrabajo,
)


from .gestor_confirmaciones import (
    EstadoConfirmacion,
    SolicitudConfirmacion,
    GestorConfirmaciones,
)

from .registro_actividad_agente import (
    EventoActividad,
    RegistroActividadAgente,
)

from .runtime_agente import (
    RuntimeAtenas,
)

from .estado_agente import (
    EstadoOperativoAgente,
    EstadoAgente,
    GestorEstadoAgente,
)

from .motor_heartbeat_agente import (
    EstadoHeartbeat,
    ResultadoHeartbeat,
    MotorHeartbeatAgente,
)

from .supervisor_sesion_autonoma import (
    TipoDecisionSupervisorSesion,
    DecisionSupervisorSesion,
    ResultadoSupervisorSesion,
    SupervisorSesionAutonoma,
)

from .ejecutor_sistema import (
    TipoAccionSistema,
    AccionSistema,
    ResultadoAccionSistema,
    EjecutorSistema,
)

from .capacidad_sistema import (
    ResultadoCapacidadSistema,
    CapacidadSistema,
)

from .gestor_presupuesto_autonomia import (
    NivelAutonomia,
    PoliticaAutonomia,
    EvaluacionAutonomia,
    GestorPresupuestoAutonomia,
)

from .director_iniciativa import (
    TipoTrabajoAgente,
    TrabajoCandidato,
    DirectorIniciativaAgente,
)

from .ciclo_autonomo import (
    EstadoCicloAutonomo,
    PasoCicloAutonomo,
    ResultadoCicloAutonomo,
    CicloAutonomoAgente,
)

from .decision_engine import (
    TipoDecisionAgente,
    Decision,
    DecisionEngine,
)

from .detector_necesidades import (
    NecesidadDetectada,
    DetectorNecesidades,
)

from .estado_mundo import (
    EstadoMundo,
)

from .generador_acciones import (
    GeneradorAcciones,
)

from .objetivos import (
    EstadoObjetivo,
    Objetivo,
    GestorObjetivos,
)

from .pendientes import (
    EstadoPendiente,
    Pendiente,
    GestorPendientes,
)

from .persistencia import (
    PersistenciaAgente,
)

from .planificador import (
    PasoPlan,
    Plan,
    Planificador,
)

from .planificador_inteligente import (
    PlanificadorInteligente,
)

from .validador_plan import (
    ValidadorPlan,
)

from .restaurador_contexto_desarrollo import (
    ResultadoRestauracionDesarrollo,
    RestauradorContextoDesarrollo,
)

from .capacidad_desarrollo import (
    AccionDesarrollo,
    ProyectoSoftwareAgente,
    ResultadoCapacidadDesarrollo,
    CapacidadDesarrollo,
)

from .agente import (
    AgenteAtenas,
)


__all__ = [
    "catalogo_para_llm",

    "TipoCapacidadAgente",
    "CapacidadAgente",
    "capacidades_disponibles",
    "capacidad_por_nombre",
    "catalogo_capacidades_para_llm",
    "es_capacidad",

    "VentanaSistema",
    "ResultadoVentanas",
    "GestorVentanas",

    "BotonMouse",
    "PosicionMouse",
    "ResultadoMouse",
    "ControladorMouse",

    "TeclaEspecial",
    "ResultadoTeclado",
    "ControladorTeclado",

    "CapturaPantalla",
    "ResultadoCapturaPantalla",
    "CapturadorPantalla",

    "EstadoVisual",
    "ResultadoPercepcionVisual",
    "PercepcionVisual",

    "ElementoVisual",
    "InterpretacionVisual",
    "ResultadoInterpretacionVisual",
    "InterpretadorVisual",

    "EstadoVisionOllama",
    "AdaptadorVisionOllama",

    "TipoObjetivoVisual",
    "ObjetivoVisual",
    "ResultadoObjetivoVisual",
    "ResolutorObjetivoVisual",

    "TipoAccionGUI",
    "AccionGUIPlanificada",
    "ResultadoPlanGUI",
    "PlanificadorGUI",

    "ResultadoEjecucionGUI",
    "EjecutorGUI",

    "CriterioVerificacionVisual",
    "ResultadoVerificacionVisual",
    "VerificadorVisual",

    "ResultadoCicloGUI",
    "CicloAccionGUI",

    "EstadoTareaEscritorio",
    "EstadoPasoEscritorio",
    "TipoPasoEscritorio",
    "PasoTareaEscritorio",
    "TareaEscritorio",
    "RegistroTareasEscritorio",
    "ResultadoPasoTarea",
    "OrquestadorTareasEscritorio",
    "PlanTareaEscritorio",
    "PlanificadorTareasEscritorio",
    "ResultadoReplanificacion",
    "ReplanificadorTareasEscritorio",
    "ContextoOperativo",
    "GestorContextoOperativo",

    "EstadoSesionTrabajo",
    "SesionTrabajo",
    "GestorSesionTrabajo",

    "TipoDecisionSupervisorSesion",
    "DecisionSupervisorSesion",
    "ResultadoSupervisorSesion",
    "SupervisorSesionAutonoma",
    "EstadoConfirmacion",
    "SolicitudConfirmacion",
    "GestorConfirmaciones",
    "EventoActividad",
    "RegistroActividadAgente",
    "EstadoHeartbeat",
    "ResultadoHeartbeat",
    "MotorHeartbeatAgente",
    "EstadoOperativoAgente",
    "EstadoAgente",
    "GestorEstadoAgente",
    "RuntimeAtenas",

    "TipoAccionSistema",
    "AccionSistema",
    "ResultadoAccionSistema",
    "EjecutorSistema",

    "ResultadoCapacidadSistema",
    "CapacidadSistema",

    "NivelAutonomia",
    "PoliticaAutonomia",
    "EvaluacionAutonomia",
    "GestorPresupuestoAutonomia",

    "TipoTrabajoAgente",
    "TrabajoCandidato",
    "DirectorIniciativaAgente",

    "EstadoCicloAutonomo",
    "PasoCicloAutonomo",
    "ResultadoCicloAutonomo",
    "CicloAutonomoAgente",

    "TipoDecisionAgente",
    "Decision",
    "DecisionEngine",

    "NecesidadDetectada",
    "DetectorNecesidades",

    "EstadoMundo",
    "GeneradorAcciones",

    "EstadoObjetivo",
    "Objetivo",
    "GestorObjetivos",

    "EstadoPendiente",
    "Pendiente",
    "GestorPendientes",

    "PersistenciaAgente",

    "PasoPlan",
    "Plan",
    "Planificador",

    "PlanificadorInteligente",
    "ValidadorPlan",

    "ResultadoRestauracionDesarrollo",
    "RestauradorContextoDesarrollo",

    "AccionDesarrollo",
    "ProyectoSoftwareAgente",
    "ResultadoCapacidadDesarrollo",
    "CapacidadDesarrollo",

    "AgenteAtenas",
]