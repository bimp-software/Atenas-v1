from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


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
    Controla cuánto puede hacer ATENAS por iniciativa propia.

    El objetivo NO es quitar autonomía, sino separar:

    - acciones internas y reversibles;
    - acciones con impacto moderado;
    - acciones que requieren confirmación;
    - acciones bloqueadas.

    El presupuesto funciona por ciclo autónomo. Cada acción autónoma
    consume unidades. Cuando se agota, ATENAS debe detener el ciclo y
    esperar una nueva oportunidad de ejecución.

    Esto será reutilizable más adelante para:
    - mouse/teclado;
    - aplicaciones;
    - terminal;
    - archivos externos;
    - instalaciones;
    - red;
    - dispositivos físicos.
    """

    POLITICAS: dict[str, PoliticaAutonomia] = {
        # =====================================================
        # INTERNAS / BAJO IMPACTO
        # =====================================================
        "pensar": PoliticaAutonomia(
            accion="pensar",
            nivel=NivelAutonomia.LIBRE,
            costo=0,
            descripcion="Evaluar estado y decidir.",
        ),
        "consultar_estado": PoliticaAutonomia(
            accion="consultar_estado",
            nivel=NivelAutonomia.LIBRE,
            costo=0,
            descripcion="Leer estado interno.",
        ),
        "listar_proyectos": PoliticaAutonomia(
            accion="listar_proyectos",
            nivel=NivelAutonomia.LIBRE,
            costo=0,
            descripcion="Consultar proyectos registrados.",
        ),
        "continuar_proyecto": PoliticaAutonomia(
            accion="continuar_proyecto",
            nivel=NivelAutonomia.CONTROLADA,
            costo=2,
            descripcion=(
                "Continuar una unidad de trabajo dentro de un "
                "proyecto ya existente."
            ),
        ),
        "crear_proyecto": PoliticaAutonomia(
            accion="crear_proyecto",
            nivel=NivelAutonomia.CONTROLADA,
            costo=3,
            descripcion=(
                "Crear estructura, planificación y archivos de un "
                "nuevo proyecto solicitado explícitamente."
            ),
        ),
        "crear_nota": PoliticaAutonomia(
            accion="crear_nota",
            nivel=NivelAutonomia.CONTROLADA,
            costo=1,
            descripcion="Crear una nota interna.",
        ),
        "buscar_memoria": PoliticaAutonomia(
            accion="buscar_memoria",
            nivel=NivelAutonomia.LIBRE,
            costo=0,
            descripcion="Consultar memoria interna.",
        ),
        "investigar": PoliticaAutonomia(
            accion="investigar",
            nivel=NivelAutonomia.CONTROLADA,
            costo=1,
            descripcion="Realizar una investigación permitida.",
        ),

        # =====================================================
        # IMPACTO EXTERNO / CONFIRMACIÓN
        # =====================================================
        "instalar_dependencia": PoliticaAutonomia(
            accion="instalar_dependencia",
            nivel=NivelAutonomia.CONFIRMACION,
            costo=3,
            descripcion=(
                "Instalar código de terceros puede modificar el entorno "
                "y ejecutar scripts de instalación."
            ),
        ),
        "eliminar_archivo": PoliticaAutonomia(
            accion="eliminar_archivo",
            nivel=NivelAutonomia.CONFIRMACION,
            costo=3,
            descripcion="Eliminar archivos requiere confirmación.",
        ),
        "mover_archivo_externo": PoliticaAutonomia(
            accion="mover_archivo_externo",
            nivel=NivelAutonomia.CONFIRMACION,
            costo=2,
            descripcion=(
                "Mover archivos fuera del espacio gestionado requiere "
                "confirmación."
            ),
        ),
        "control_mouse": PoliticaAutonomia(
            accion="control_mouse",
            nivel=NivelAutonomia.CONFIRMACION,
            costo=2,
            descripcion=(
                "El control de interfaz gráfica externa requiere una "
                "política específica."
            ),
        ),
        "escribir_aplicacion": PoliticaAutonomia(
            accion="escribir_aplicacion",
            nivel=NivelAutonomia.CONFIRMACION,
            costo=2,
            descripcion=(
                "Escribir en aplicaciones externas puede producir "
                "efectos reales."
            ),
        ),
        "enviar_mensaje": PoliticaAutonomia(
            accion="enviar_mensaje",
            nivel=NivelAutonomia.CONFIRMACION,
            costo=4,
            descripcion="Enviar contenido externo requiere confirmación.",
        ),

        # =====================================================
        # BLOQUEADAS POR DEFECTO
        # =====================================================
        "comando_arbitrario": PoliticaAutonomia(
            accion="comando_arbitrario",
            nivel=NivelAutonomia.BLOQUEADA,
            costo=99,
            descripcion=(
                "El LLM no puede convertir texto libre directamente "
                "en comandos arbitrarios del sistema."
            ),
        ),
        "modificar_politica_seguridad": PoliticaAutonomia(
            accion="modificar_politica_seguridad",
            nivel=NivelAutonomia.BLOQUEADA,
            costo=99,
            descripcion=(
                "ATENAS no puede modificar autónomamente sus propias "
                "políticas de seguridad."
            ),
        ),
    }

    def __init__(
        self,
        presupuesto_por_ciclo: int = 10,
    ):
        self.presupuesto_por_ciclo = max(
            1,
            int(presupuesto_por_ciclo),
        )

        self.presupuesto_restante = (
            self.presupuesto_por_ciclo
        )

    # =========================================================
    # CICLO
    # =========================================================

    def reiniciar_ciclo(
        self,
    ) -> None:

        self.presupuesto_restante = (
            self.presupuesto_por_ciclo
        )

    # =========================================================
    # POLÍTICA
    # =========================================================

    def politica(
        self,
        accion: str,
    ) -> PoliticaAutonomia:

        clave = (
            accion
            or ""
        ).strip().lower()

        politica = self.POLITICAS.get(
            clave
        )

        if politica is not None:
            return politica

        # Acciones nuevas/desconocidas son conservadoras.
        return PoliticaAutonomia(
            accion=clave or "desconocida",
            nivel=NivelAutonomia.CONFIRMACION,
            costo=2,
            descripcion=(
                "La acción aún no tiene una política explícita."
            ),
        )

    # =========================================================
    # EVALUAR
    # =========================================================

    def evaluar(
        self,
        accion: str,
        es_autonoma: bool = True,
        confirmada: bool = False,
    ) -> EvaluacionAutonomia:

        politica = self.politica(
            accion
        )

        if (
            politica.nivel
            == NivelAutonomia.BLOQUEADA
        ):

            return EvaluacionAutonomia(
                permitida=False,
                requiere_confirmacion=False,
                bloqueada=True,
                accion=politica.accion,
                nivel=politica.nivel,
                costo=politica.costo,
                presupuesto_restante=(
                    self.presupuesto_restante
                ),
                motivo=politica.descripcion,
            )

        if (
            politica.nivel
            == NivelAutonomia.CONFIRMACION
            and not confirmada
        ):

            return EvaluacionAutonomia(
                permitida=False,
                requiere_confirmacion=True,
                bloqueada=False,
                accion=politica.accion,
                nivel=politica.nivel,
                costo=politica.costo,
                presupuesto_restante=(
                    self.presupuesto_restante
                ),
                motivo=politica.descripcion,
            )

        # Las acciones explícitamente ordenadas por el usuario no consumen
        # presupuesto autónomo. Siguen respetando bloqueos/confirmación.
        if not es_autonoma:

            return EvaluacionAutonomia(
                permitida=True,
                requiere_confirmacion=False,
                bloqueada=False,
                accion=politica.accion,
                nivel=politica.nivel,
                costo=0,
                presupuesto_restante=(
                    self.presupuesto_restante
                ),
                motivo=(
                    "Acción explícita permitida por la política."
                ),
            )

        if (
            politica.costo
            > self.presupuesto_restante
        ):

            return EvaluacionAutonomia(
                permitida=False,
                requiere_confirmacion=False,
                bloqueada=False,
                accion=politica.accion,
                nivel=politica.nivel,
                costo=politica.costo,
                presupuesto_restante=(
                    self.presupuesto_restante
                ),
                motivo=(
                    "No queda presupuesto autónomo suficiente "
                    "para esta acción."
                ),
            )

        return EvaluacionAutonomia(
            permitida=True,
            requiere_confirmacion=False,
            bloqueada=False,
            accion=politica.accion,
            nivel=politica.nivel,
            costo=politica.costo,
            presupuesto_restante=(
                self.presupuesto_restante
            ),
            motivo="Acción permitida.",
        )

    # =========================================================
    # CONSUMIR
    # =========================================================

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