from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NivelAutonomia(str, Enum):
    LIBRE = "libre"
    CONTROLADA = "controlada"
    CONFIRMACION = "confirmacion"
    BLOQUEADA = "bloqueada"


@dataclass(frozen=True)
class PoliticaAutonomia:
    accion: str
    nivel: NivelAutonomia
    costo: int
    descripcion: str


@dataclass
class EvaluacionAutonomia:
    permitida: bool
    requiere_confirmacion: bool
    bloqueada: bool

    accion: str
    nivel: NivelAutonomia

    costo: int
    presupuesto_restante: int

    motivo: str


class GestorPresupuestoAutonomia:
    """
    Política común para Agente, Desarrollo, Sistema y GUI.
    """

    POLITICAS = {
        # Lecturas
        "pensar":
            PoliticaAutonomia(
                "pensar",
                NivelAutonomia.LIBRE,
                0,
                "Evaluar estado.",
            ),

        "consultar_estado":
            PoliticaAutonomia(
                "consultar_estado",
                NivelAutonomia.LIBRE,
                0,
                "Consultar estado.",
            ),

        "listar_proyectos":
            PoliticaAutonomia(
                "listar_proyectos",
                NivelAutonomia.LIBRE,
                0,
                "Listar proyectos.",
            ),

        "buscar_memoria":
            PoliticaAutonomia(
                "buscar_memoria",
                NivelAutonomia.LIBRE,
                0,
                "Consultar memoria.",
            ),

        "leer_texto":
            PoliticaAutonomia(
                "leer_texto",
                NivelAutonomia.LIBRE,
                0,
                "Leer texto.",
            ),

        "listar_directorio":
            PoliticaAutonomia(
                "listar_directorio",
                NivelAutonomia.LIBRE,
                0,
                "Listar carpeta.",
            ),

        "listar_procesos":
            PoliticaAutonomia(
                "listar_procesos",
                NivelAutonomia.LIBRE,
                0,
                "Listar procesos.",
            ),

        "listar_ventanas":
            PoliticaAutonomia(
                "listar_ventanas",
                NivelAutonomia.LIBRE,
                0,
                "Observar ventanas.",
            ),

        "ventana_activa":
            PoliticaAutonomia(
                "ventana_activa",
                NivelAutonomia.LIBRE,
                0,
                "Consultar ventana activa.",
            ),

        # Controladas
        "continuar_proyecto":
            PoliticaAutonomia(
                "continuar_proyecto",
                NivelAutonomia.CONTROLADA,
                2,
                "Continuar proyecto.",
            ),

        "crear_proyecto":
            PoliticaAutonomia(
                "crear_proyecto",
                NivelAutonomia.CONTROLADA,
                3,
                "Crear proyecto solicitado.",
            ),

        "crear_nota":
            PoliticaAutonomia(
                "crear_nota",
                NivelAutonomia.CONTROLADA,
                1,
                "Crear nota.",
            ),

        "investigar":
            PoliticaAutonomia(
                "investigar",
                NivelAutonomia.CONTROLADA,
                1,
                "Investigar.",
            ),

        "crear_carpeta":
            PoliticaAutonomia(
                "crear_carpeta",
                NivelAutonomia.CONTROLADA,
                1,
                "Crear carpeta autorizada.",
            ),

        "escribir_texto":
            PoliticaAutonomia(
                "escribir_texto",
                NivelAutonomia.CONTROLADA,
                1,
                "Crear archivo de texto.",
            ),

        "abrir_ruta":
            PoliticaAutonomia(
                "abrir_ruta",
                NivelAutonomia.CONTROLADA,
                1,
                "Abrir ruta.",
            ),

        "abrir_aplicacion":
            PoliticaAutonomia(
                "abrir_aplicacion",
                NivelAutonomia.CONTROLADA,
                1,
                "Abrir aplicación registrada.",
            ),

        "activar_ventana":
            PoliticaAutonomia(
                "activar_ventana",
                NivelAutonomia.CONTROLADA,
                1,
                "Traer una ventana al frente.",
            ),

        "minimizar_ventana":
            PoliticaAutonomia(
                "minimizar_ventana",
                NivelAutonomia.CONTROLADA,
                1,
                "Minimizar ventana.",
            ),

        "maximizar_ventana":
            PoliticaAutonomia(
                "maximizar_ventana",
                NivelAutonomia.CONTROLADA,
                1,
                "Maximizar ventana.",
            ),

        "restaurar_ventana":
            PoliticaAutonomia(
                "restaurar_ventana",
                NivelAutonomia.CONTROLADA,
                1,
                "Restaurar ventana.",
            ),


        "capturar_pantalla":
            PoliticaAutonomia(
                "capturar_pantalla",
                NivelAutonomia.CONTROLADA,
                1,
                "Capturar pantalla para percepción visual local.",
            ),

        "capturar_ventana":
            PoliticaAutonomia(
                "capturar_ventana",
                NivelAutonomia.CONTROLADA,
                1,
                "Capturar una ventana conocida para percepción local.",
            ),

        "listar_capturas":
            PoliticaAutonomia(
                "listar_capturas",
                NivelAutonomia.LIBRE,
                0,
                "Consultar capturas visuales ya registradas.",
            ),

        "construir_estado_visual":
            PoliticaAutonomia(
                "construir_estado_visual",
                NivelAutonomia.CONTROLADA,
                1,
                "Construir una escena visual local del escritorio.",
            ),

        "interpretar_escena":
            PoliticaAutonomia(
                "interpretar_escena",
                NivelAutonomia.CONTROLADA,
                1,
                "Interpretar semánticamente una escena visual local.",
            ),

        "verificar_resultado_visual":
            PoliticaAutonomia(
                "verificar_resultado_visual",
                NivelAutonomia.LIBRE,
                0,
                "Verificar visualmente el resultado de una acción.",
            ),

        "planificar_tarea_escritorio":
            PoliticaAutonomia(
                "planificar_tarea_escritorio",
                NivelAutonomia.LIBRE,
                0,
                "Convertir un objetivo en un plan estructurado.",
            ),

        "crear_tarea_escritorio":
            PoliticaAutonomia(
                "crear_tarea_escritorio",
                NivelAutonomia.CONTROLADA,
                1,
                "Crear una planificación persistente de escritorio.",
            ),

        "replanificar_tarea_escritorio":
            PoliticaAutonomia(
                "replanificar_tarea_escritorio",
                NivelAutonomia.CONTROLADA,
                1,
                "Reemplazar únicamente pasos futuros de una tarea.",
            ),

        "continuar_tarea_escritorio":
            PoliticaAutonomia(
                "continuar_tarea_escritorio",
                NivelAutonomia.CONTROLADA,
                2,
                "Continuar una tarea de escritorio por pasos acotados.",
            ),

        "consultar_contexto_operativo":
            PoliticaAutonomia(
                "consultar_contexto_operativo",
                NivelAutonomia.LIBRE,
                0,
                "Consultar memoria operativa local.",
            ),

        "actualizar_contexto_operativo":
            PoliticaAutonomia(
                "actualizar_contexto_operativo",
                NivelAutonomia.CONTROLADA,
                1,
                "Actualizar contexto operacional persistente.",
            ),

        "consultar_sesion_trabajo":
            PoliticaAutonomia(
                "consultar_sesion_trabajo",
                NivelAutonomia.LIBRE,
                0,
                "Consultar la sesión de trabajo operativa actual.",
            ),

        "crear_sesion_trabajo":
            PoliticaAutonomia(
                "crear_sesion_trabajo",
                NivelAutonomia.CONTROLADA,
                1,
                "Crear una sesión persistente para un objetivo superior.",
            ),

        "actualizar_sesion_trabajo":
            PoliticaAutonomia(
                "actualizar_sesion_trabajo",
                NivelAutonomia.CONTROLADA,
                1,
                "Actualizar progreso y estado de una sesión de trabajo.",
            ),

        # Confirmación
        "instalar_dependencia":
            PoliticaAutonomia(
                "instalar_dependencia",
                NivelAutonomia.CONFIRMACION,
                3,
                "Instalar terceros requiere confirmación.",
            ),

        "eliminar_archivo":
            PoliticaAutonomia(
                "eliminar_archivo",
                NivelAutonomia.CONFIRMACION,
                3,
                "Eliminar requiere confirmación.",
            ),

        "posicion_mouse":
            PoliticaAutonomia(
                "posicion_mouse",
                NivelAutonomia.LIBRE,
                0,
                "Consultar la posición del cursor.",
            ),

        "mover_mouse":
            PoliticaAutonomia(
                "mover_mouse",
                NivelAutonomia.CONTROLADA,
                1,
                "Mover el cursor de forma estructurada.",
            ),

        "mover_mouse_ventana":
            PoliticaAutonomia(
                "mover_mouse_ventana",
                NivelAutonomia.CONTROLADA,
                1,
                "Mover el cursor relativo a una ventana conocida.",
            ),

        "click_mouse":
            PoliticaAutonomia(
                "click_mouse",
                NivelAutonomia.CONFIRMACION,
                2,
                "Un click puede producir efectos en aplicaciones externas.",
            ),

        "doble_click_mouse":
            PoliticaAutonomia(
                "doble_click_mouse",
                NivelAutonomia.CONFIRMACION,
                2,
                "Un doble click puede producir efectos externos.",
            ),

        "click_mouse_ventana":
            PoliticaAutonomia(
                "click_mouse_ventana",
                NivelAutonomia.CONFIRMACION,
                2,
                "Hacer click dentro de una aplicación requiere confirmación.",
            ),

        "scroll_mouse":
            PoliticaAutonomia(
                "scroll_mouse",
                NivelAutonomia.CONTROLADA,
                1,
                "Desplazar la vista mediante scroll.",
            ),

        "control_mouse":
            PoliticaAutonomia(
                "control_mouse",
                NivelAutonomia.CONFIRMACION,
                2,
                "Compatibilidad con política GUI general.",
            ),

        "escribir_teclado":
            PoliticaAutonomia(
                "escribir_teclado",
                NivelAutonomia.CONFIRMACION,
                2,
                "Escribir mediante teclado puede producir efectos externos.",
            ),

        "pulsar_tecla":
            PoliticaAutonomia(
                "pulsar_tecla",
                NivelAutonomia.CONFIRMACION,
                2,
                "Una tecla puede ejecutar acciones en la aplicación activa.",
            ),

        "combinacion_teclas":
            PoliticaAutonomia(
                "combinacion_teclas",
                NivelAutonomia.CONFIRMACION,
                2,
                "Una combinación puede guardar, cerrar o modificar contenido.",
            ),

        "escribir_en_ventana":
            PoliticaAutonomia(
                "escribir_en_ventana",
                NivelAutonomia.CONFIRMACION,
                2,
                "Escribir dentro de una aplicación requiere confirmación.",
            ),

        "combinacion_teclas_ventana":
            PoliticaAutonomia(
                "combinacion_teclas_ventana",
                NivelAutonomia.CONFIRMACION,
                2,
                "Enviar teclas a una ventana requiere confirmación.",
            ),

        "escribir_aplicacion":
            PoliticaAutonomia(
                "escribir_aplicacion",
                NivelAutonomia.CONFIRMACION,
                2,
                "Compatibilidad con política GUI general.",
            ),

        "enviar_mensaje":
            PoliticaAutonomia(
                "enviar_mensaje",
                NivelAutonomia.CONFIRMACION,
                4,
                "Enviar requiere confirmación.",
            ),

        # Bloqueadas
        "comando_arbitrario":
            PoliticaAutonomia(
                "comando_arbitrario",
                NivelAutonomia.BLOQUEADA,
                99,
                "No se ejecutan comandos libres del LLM.",
            ),

        "modificar_politica_seguridad":
            PoliticaAutonomia(
                "modificar_politica_seguridad",
                NivelAutonomia.BLOQUEADA,
                99,
                "ATENAS no cambia sola su política.",
            ),
    }

    def __init__(
        self,
        presupuesto_por_ciclo: int = 10,
    ):

        self.presupuesto_por_ciclo = max(
            1,
            int(
                presupuesto_por_ciclo
            ),
        )

        self.presupuesto_restante = (
            self.presupuesto_por_ciclo
        )

    def reiniciar_ciclo(
        self,
    ) -> None:

        self.presupuesto_restante = (
            self.presupuesto_por_ciclo
        )

    def politica(
        self,
        accion: str,
    ) -> PoliticaAutonomia:

        clave = (
            accion
            or ""
        ).strip().lower()

        return self.POLITICAS.get(
            clave,
            PoliticaAutonomia(
                clave or "desconocida",
                NivelAutonomia.CONFIRMACION,
                2,
                "La acción no posee política explícita.",
            ),
        )

    def evaluar(
        self,
        accion: str,
        es_autonoma: bool = True,
        confirmada: bool = False,
    ) -> EvaluacionAutonomia:

        politica = (
            self.politica(
                accion
            )
        )

        if (
            politica.nivel
            == NivelAutonomia.BLOQUEADA
        ):

            return EvaluacionAutonomia(
                False,
                False,
                True,
                politica.accion,
                politica.nivel,
                politica.costo,
                self.presupuesto_restante,
                politica.descripcion,
            )

        if (
            politica.nivel
            == NivelAutonomia.CONFIRMACION
            and not confirmada
        ):

            return EvaluacionAutonomia(
                False,
                True,
                False,
                politica.accion,
                politica.nivel,
                politica.costo,
                self.presupuesto_restante,
                politica.descripcion,
            )

        if not es_autonoma:

            return EvaluacionAutonomia(
                True,
                False,
                False,
                politica.accion,
                politica.nivel,
                0,
                self.presupuesto_restante,
                "Acción explícita permitida.",
            )

        if (
            politica.costo
            > self.presupuesto_restante
        ):

            return EvaluacionAutonomia(
                False,
                False,
                False,
                politica.accion,
                politica.nivel,
                politica.costo,
                self.presupuesto_restante,
                "Presupuesto autónomo insuficiente.",
            )

        return EvaluacionAutonomia(
            True,
            False,
            False,
            politica.accion,
            politica.nivel,
            politica.costo,
            self.presupuesto_restante,
            "Acción permitida.",
        )

    def consumir(
        self,
        evaluacion: EvaluacionAutonomia,
        es_autonoma: bool = True,
    ) -> bool:

        if not evaluacion.permitida:
            return False

        if not es_autonoma:
            return True

        if (
            evaluacion.costo
            > self.presupuesto_restante
        ):
            return False

        self.presupuesto_restante -= (
            evaluacion.costo
        )

        return True