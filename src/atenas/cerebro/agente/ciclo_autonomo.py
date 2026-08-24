from __future__ import annotations

import time

from dataclasses import dataclass, field
from enum import Enum

from .agente import AgenteAtenas
from .gestor_presupuesto_autonomia import (
    GestorPresupuestoAutonomia,
)


class EstadoCicloAutonomo(str, Enum):
    SIN_TRABAJO = "sin_trabajo"
    EJECUTADO = "ejecutado"
    PAUSADO_CONFIRMACION = "pausado_confirmacion"
    DETENIDO_ERROR = "detenido_error"
    DETENIDO_PRESUPUESTO = "detenido_presupuesto"
    LIMITE_ALCANZADO = "limite_alcanzado"


@dataclass
class PasoCicloAutonomo:
    numero: int
    actuo: bool
    exito: bool | None

    tipo_decision: str | None = None
    capacidad: str | None = None
    accion_capacidad: str | None = None

    proyecto_id: str | None = None
    pendiente_id: str | None = None

    costo_autonomia: int = 0
    presupuesto_restante: int | None = None

    mensaje: str = ""
    error: str | None = None


@dataclass
class ResultadoCicloAutonomo:
    ok: bool
    estado: EstadoCicloAutonomo

    pasos: list[PasoCicloAutonomo] = field(
        default_factory=list
    )

    acciones_ejecutadas: int = 0
    duracion_segundos: float = 0.0

    presupuesto_inicial: int = 0
    presupuesto_restante: int = 0

    detenido_por_confirmacion: bool = False

    mensaje: str = ""
    error: str | None = None


class CicloAutonomoAgente:
    """
    Ciclo autónomo acotado de ATENAS.

    Antes de cada acción:
    1. piensa;
    2. identifica la acción prevista;
    3. consulta GestorPresupuestoAutonomia;
    4. solo entonces ejecuta;
    5. consume presupuesto;
    6. vuelve a evaluar.

    Así el agente no puede convertir autonomía en ejecución ilimitada.
    """

    def __init__(
        self,
        agente: AgenteAtenas,
        max_acciones: int = 5,
        max_segundos: float = 120.0,
        presupuesto: (
            GestorPresupuestoAutonomia
            | None
        ) = None,
    ):
        self.agente = agente

        self.max_acciones = max(
            1,
            int(max_acciones),
        )

        self.max_segundos = max(
            1.0,
            float(max_segundos),
        )

        self.presupuesto = (
            presupuesto
            or GestorPresupuestoAutonomia()
        )

    # =========================================================
    # ACCIÓN PREVISTA
    # =========================================================

    @staticmethod
    def _accion_desde_decision(
        decision,
    ) -> str:

        accion = (
            getattr(
                decision,
                "accion_capacidad",
                None,
            )
            or ""
        ).strip()

        if accion:
            return accion

        tipo = getattr(
            getattr(
                decision,
                "tipo",
                None,
            ),
            "value",
            "",
        )

        if tipo == "pendiente":
            return "crear_nota"

        return (
            tipo
            or "pensar"
        )

    # =========================================================
    # EJECUTAR
    # =========================================================

    def ejecutar(
        self,
        permitir_iniciativa_desarrollo: bool = True,
    ) -> ResultadoCicloAutonomo:

        inicio = time.monotonic()

        self.presupuesto.reiniciar_ciclo()

        presupuesto_inicial = (
            self.presupuesto
            .presupuesto_restante
        )

        pasos: list[
            PasoCicloAutonomo
        ] = []

        acciones = 0

        try:
            self.agente.estado.iniciar_ciclo_autonomo()
        except Exception:
            pass

        estado_final = (
            EstadoCicloAutonomo
            .LIMITE_ALCANZADO
        )

        mensaje_final = ""

        error_final = None

        try:

            for numero in range(
                1,
                self.max_acciones + 1,
            ):

                if (
                    time.monotonic()
                    - inicio
                    >= self.max_segundos
                ):

                    estado_final = (
                        EstadoCicloAutonomo
                        .LIMITE_ALCANZADO
                    )

                    mensaje_final = (
                        "Se alcanzó el límite de tiempo."
                    )

                    break

                pensamiento = (
                    self.agente.pensar(
                        permitir_iniciativa_desarrollo=(
                            permitir_iniciativa_desarrollo
                        )
                    )
                )

                decision = (
                    pensamiento[
                        "decision"
                    ]
                )

                if not decision.actuar:

                    pasos.append(
                        PasoCicloAutonomo(
                            numero=numero,
                            actuo=False,
                            exito=None,
                            tipo_decision=(
                                decision.tipo.value
                            ),
                            mensaje=(
                                decision.motivo
                            ),
                            presupuesto_restante=(
                                self.presupuesto
                                .presupuesto_restante
                            ),
                        )
                    )

                    estado_final = (
                        EstadoCicloAutonomo
                        .SIN_TRABAJO
                    )

                    mensaje_final = (
                        "No existe más trabajo ejecutable."
                    )

                    break

                accion = (
                    self._accion_desde_decision(
                        decision
                    )
                )

                evaluacion = (
                    self.presupuesto
                    .evaluar(
                        accion=accion,
                        es_autonoma=True,
                        confirmada=False,
                    )
                )

                if (
                    evaluacion
                    .requiere_confirmacion
                ):

                    pasos.append(
                        PasoCicloAutonomo(
                            numero=numero,
                            actuo=False,
                            exito=None,
                            tipo_decision=(
                                decision.tipo.value
                            ),
                            capacidad=(
                                decision.capacidad
                            ),
                            accion_capacidad=(
                                decision
                                .accion_capacidad
                            ),
                            proyecto_id=(
                                decision.proyecto_id
                            ),
                            pendiente_id=(
                                decision.pendiente_id
                            ),
                            costo_autonomia=(
                                evaluacion.costo
                            ),
                            presupuesto_restante=(
                                self.presupuesto
                                .presupuesto_restante
                            ),
                            mensaje=(
                                evaluacion.motivo
                            ),
                        )
                    )

                    estado_final = (
                        EstadoCicloAutonomo
                        .PAUSADO_CONFIRMACION
                    )

                    mensaje_final = (
                        evaluacion.motivo
                    )

                    break

                if not evaluacion.permitida:

                    pasos.append(
                        PasoCicloAutonomo(
                            numero=numero,
                            actuo=False,
                            exito=False,
                            tipo_decision=(
                                decision.tipo.value
                            ),
                            capacidad=(
                                decision.capacidad
                            ),
                            accion_capacidad=(
                                decision
                                .accion_capacidad
                            ),
                            proyecto_id=(
                                decision.proyecto_id
                            ),
                            pendiente_id=(
                                decision.pendiente_id
                            ),
                            costo_autonomia=(
                                evaluacion.costo
                            ),
                            presupuesto_restante=(
                                self.presupuesto
                                .presupuesto_restante
                            ),
                            mensaje=(
                                evaluacion.motivo
                            ),
                        )
                    )

                    estado_final = (
                        EstadoCicloAutonomo
                        .DETENIDO_PRESUPUESTO
                    )

                    mensaje_final = (
                        evaluacion.motivo
                    )

                    break

                resultado = (
                    self.agente.actuar(
                        permitir_iniciativa_desarrollo=(
                            permitir_iniciativa_desarrollo
                        )
                    )
                )

                consumido = (
                    self.presupuesto
                    .consumir(
                        evaluacion,
                        es_autonoma=True,
                    )
                )

                if not consumido:

                    estado_final = (
                        EstadoCicloAutonomo
                        .DETENIDO_PRESUPUESTO
                    )

                    mensaje_final = (
                        "No fue posible consumir el "
                        "presupuesto de autonomía."
                    )

                    break

                acciones += 1

                decision_real = (
                    resultado.get(
                        "decision"
                    )
                    or decision
                )

                paso = PasoCicloAutonomo(
                    numero=numero,
                    actuo=bool(
                        resultado.get(
                            "actuo",
                            False,
                        )
                    ),
                    exito=(
                        resultado.get(
                            "exito"
                        )
                    ),
                    tipo_decision=(
                        getattr(
                            getattr(
                                decision_real,
                                "tipo",
                                None,
                            ),
                            "value",
                            None,
                        )
                    ),
                    capacidad=(
                        resultado.get(
                            "capacidad"
                        )
                    ),
                    accion_capacidad=(
                        resultado.get(
                            "accion_capacidad"
                        )
                    ),
                    proyecto_id=(
                        resultado.get(
                            "proyecto_id"
                        )
                        or getattr(
                            decision_real,
                            "proyecto_id",
                            None,
                        )
                    ),
                    pendiente_id=(
                        getattr(
                            decision_real,
                            "pendiente_id",
                            None,
                        )
                    ),
                    costo_autonomia=(
                        evaluacion.costo
                    ),
                    presupuesto_restante=(
                        self.presupuesto
                        .presupuesto_restante
                    ),
                    mensaje=str(
                        resultado.get(
                            "mensaje",
                            "",
                        )
                        or ""
                    ),
                    error=(
                        str(
                            resultado[
                                "error"
                            ]
                        )
                        if resultado.get(
                            "error"
                        )
                        else None
                    ),
                )

                pasos.append(
                    paso
                )

                if resultado.get(
                    "requiere_confirmacion",
                    False,
                ):

                    estado_final = (
                        EstadoCicloAutonomo
                        .PAUSADO_CONFIRMACION
                    )

                    mensaje_final = (
                        resultado.get(
                            "mensaje"
                        )
                        or (
                            "La acción requiere confirmación."
                        )
                    )

                    break

                if paso.exito is False:

                    estado_final = (
                        EstadoCicloAutonomo
                        .DETENIDO_ERROR
                    )

                    mensaje_final = (
                        paso.mensaje
                        or "Una acción falló."
                    )

                    error_final = (
                        paso.error
                        or "accion_fallida"
                    )

                    break

            else:

                estado_final = (
                    EstadoCicloAutonomo
                    .LIMITE_ALCANZADO
                )

                mensaje_final = (
                    "Se alcanzó el máximo de acciones."
                )

        finally:

            try:
                self.agente.estado.finalizar_ciclo_autonomo(
                    estado_final.value
                )
            except Exception:
                pass

        return ResultadoCicloAutonomo(
            ok=(
                estado_final
                not in {
                    EstadoCicloAutonomo
                    .DETENIDO_ERROR,
                }
            ),
            estado=estado_final,
            pasos=pasos,
            acciones_ejecutadas=acciones,
            duracion_segundos=(
                time.monotonic()
                - inicio
            ),
            presupuesto_inicial=(
                presupuesto_inicial
            ),
            presupuesto_restante=(
                self.presupuesto
                .presupuesto_restante
            ),
            detenido_por_confirmacion=(
                estado_final
                == EstadoCicloAutonomo
                .PAUSADO_CONFIRMACION
            ),
            mensaje=mensaje_final,
            error=error_final,
        )