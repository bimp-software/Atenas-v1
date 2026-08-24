from __future__ import annotations

from dataclasses import dataclass

from .automejora import (
    InformeAutoMejora,
)

from .motor_automejora import (
    MotorAutoMejora,
    ResultadoMotorAutoMejora,
)

from .politica_aplicacion_mejoras import (
    AplicadorMejoras,
    PoliticaAplicacionMejoras,
    ResultadoAplicacionMejora,
)

from .registro_propuestas import (
    EstadoPropuesta,
    RegistroPropuestasMejora,
)


@dataclass
class ResultadoCicloAutoMejora:
    ok: bool

    estado: str

    informe: InformeAutoMejora | None = None

    resultado_motor: ResultadoMotorAutoMejora | None = None

    aplicacion: ResultadoAplicacionMejora | None = None

    aplicada: bool = False

    requiere_confirmacion: bool = False

    propuesta_id: str | None = None

    mensaje: str = ""

    error: str | None = None


class CicloAutoMejora:
    """
    Orquesta un ciclo completo de automejora de ATENAS.

    Flujo:

        analizar proyecto
            ↓
        MotorAutoMejora
            ↓
        elegir hallazgo seguro
            ↓
        PlanificadorMejoras / Qwen
            ↓
        sandbox
            ↓
        tests
            ↓
        verificación
            ↓
        PoliticaAplicacionMejoras
            ↓
        aplicar opcionalmente
            ↓
        historial + rollback disponible

    IMPORTANTE:

    - Nunca aplica cambios si permitir_aplicacion=False.
    - Incluso con permitir_aplicacion=True, la política específica
      de automejora puede bloquear la aplicación.
    - Solo procesa una mejora por ciclo.
    """

    def __init__(
        self,
        analizador,
        motor: MotorAutoMejora,
        politica_aplicacion: PoliticaAplicacionMejoras,
        aplicador: AplicadorMejoras,
        registro_propuestas: RegistroPropuestasMejora | None = None,
    ):
        self.analizador = analizador
        self.motor = motor
        self.politica_aplicacion = (
            politica_aplicacion
        )
        self.aplicador = aplicador
        self.registro_propuestas = (
            registro_propuestas
        )

        self.ultimo_resultado: (
            ResultadoCicloAutoMejora | None
        ) = None

    # =========================================================
    # EJECUTAR
    # =========================================================

    def ejecutar(
        self,
        tests: list[str] | None = None,
        permitir_aplicacion: bool = False,
        limite_archivos: int | None = None,
    ) -> ResultadoCicloAutoMejora:

        # =====================================================
        # 1. ANALIZAR
        # =====================================================

        try:

            informe = (
                self.analizador
                .analizar_proyecto(
                    limite_archivos=(
                        limite_archivos
                    )
                )
            )

        except Exception as error:

            resultado = ResultadoCicloAutoMejora(
                ok=False,
                estado="fallo_analisis",
                mensaje=(
                    "No fue posible analizar "
                    "el proyecto."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        if not informe.hallazgos:

            resultado = ResultadoCicloAutoMejora(
                ok=True,
                estado="sin_hallazgos",
                informe=informe,
                mensaje=(
                    "No se detectaron mejoras "
                    "prioritarias."
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        # =====================================================
        # 2. MOTOR
        # =====================================================

        try:

            resultado_motor = (
                self.motor
                .procesar(
                    informe=informe,
                    tests=tests,
                )
            )

        except Exception as error:

            resultado = ResultadoCicloAutoMejora(
                ok=False,
                estado="fallo_motor",
                informe=informe,
                mensaje=(
                    "El motor de automejora "
                    "falló."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        # =====================================================
        # 3. NO HAY CANDIDATO
        # =====================================================

        if not resultado_motor.procesado:

            resultado = ResultadoCicloAutoMejora(
                ok=True,
                estado="sin_candidato_seguro",
                informe=informe,
                resultado_motor=(
                    resultado_motor
                ),
                mensaje=(
                    resultado_motor
                    .decision
                    .motivo
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        if resultado_motor.error:

            resultado = ResultadoCicloAutoMejora(
                ok=False,
                estado="fallo_planificacion",
                informe=informe,
                resultado_motor=(
                    resultado_motor
                ),
                mensaje=(
                    "No fue posible preparar "
                    "la mejora."
                ),
                error=(
                    resultado_motor.error
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        propuesta = (
            resultado_motor
            .propuesta
        )

        if propuesta is None:

            resultado = ResultadoCicloAutoMejora(
                ok=False,
                estado="sin_propuesta",
                informe=informe,
                resultado_motor=(
                    resultado_motor
                ),
                mensaje=(
                    "El motor no produjo "
                    "una propuesta."
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        # =====================================================
        # 4. PROPUESTA RECHAZADA
        # =====================================================

        if not propuesta.ok:

            resultado = ResultadoCicloAutoMejora(
                ok=False,
                estado="propuesta_rechazada",
                informe=informe,
                resultado_motor=(
                    resultado_motor
                ),
                mensaje=(
                    propuesta.mensaje
                ),
                error=(
                    propuesta.error
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        # =====================================================
        # 5. PERSISTIR PROPUESTA VALIDADA
        # =====================================================

        propuesta_id = None

        if (
            self.registro_propuestas
            is not None
        ):

            try:

                registro = (
                    self.registro_propuestas
                    .guardar(
                        propuesta,
                        metadata={
                            "origen":
                                "ciclo_automejora",

                            "decision_score":
                                getattr(
                                    resultado_motor
                                    .decision,
                                    "score",
                                    None,
                                ),

                            "requiere_confirmacion_motor":
                                getattr(
                                    resultado_motor
                                    .decision,
                                    "requiere_confirmacion",
                                    None,
                                ),
                        },
                    )
                )

                propuesta_id = (
                    registro.id
                )

            except Exception as error:

                resultado = ResultadoCicloAutoMejora(
                    ok=False,
                    estado="fallo_persistencia_propuesta",
                    informe=informe,
                    resultado_motor=(
                        resultado_motor
                    ),
                    aplicada=False,
                    mensaje=(
                        "La propuesta fue validada, "
                        "pero no pudo guardarse de "
                        "forma persistente."
                    ),
                    error=(
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                )

                self.ultimo_resultado = (
                    resultado
                )

                return resultado

        # =====================================================
        # 6. EVALUAR POLÍTICA DE APLICACIÓN
        # =====================================================

        decision_aplicacion = (
            self.politica_aplicacion
            .evaluar(
                propuesta
            )
        )

        # =====================================================
        # 7. SOLO PREPARAR
        # =====================================================

        if not permitir_aplicacion:

            resultado = ResultadoCicloAutoMejora(
                ok=True,
                estado="propuesta_validada",
                informe=informe,
                resultado_motor=(
                    resultado_motor
                ),
                aplicada=False,
                requiere_confirmacion=(
                    decision_aplicacion
                    .requiere_confirmacion
                ),
                propuesta_id=(
                    propuesta_id
                ),
                mensaje=(
                    "La mejora fue preparada y "
                    "validada, pero no se permitió "
                    "su aplicación."
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        # =====================================================
        # 8. POLÍTICA BLOQUEA
        # =====================================================

        if not decision_aplicacion.aplicar:

            resultado = ResultadoCicloAutoMejora(
                ok=True,
                estado="esperando_confirmacion",
                informe=informe,
                resultado_motor=(
                    resultado_motor
                ),
                aplicada=False,
                requiere_confirmacion=True,
                propuesta_id=(
                    propuesta_id
                ),
                mensaje=(
                    decision_aplicacion
                    .motivo
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        # =====================================================
        # 9. APLICAR
        # =====================================================

        try:

            aplicacion = (
                self.aplicador
                .aplicar(
                    propuesta
                )
            )

        except Exception as error:

            resultado = ResultadoCicloAutoMejora(
                ok=False,
                estado="fallo_aplicacion",
                informe=informe,
                resultado_motor=(
                    resultado_motor
                ),
                mensaje=(
                    "La mejora estaba validada "
                    "pero falló al aplicarse."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        # =====================================================
        # 10. RESULTADO FINAL
        # =====================================================

        if not aplicacion.ok:

            resultado = ResultadoCicloAutoMejora(
                ok=False,
                estado="fallo_aplicacion",
                informe=informe,
                resultado_motor=(
                    resultado_motor
                ),
                aplicacion=aplicacion,
                aplicada=False,
                propuesta_id=(
                    propuesta_id
                ),
                mensaje=(
                    aplicacion.mensaje
                ),
                error=(
                    aplicacion.error
                ),
            )

            self.ultimo_resultado = resultado

            return resultado

        if (
            propuesta_id is not None
            and self.registro_propuestas
            is not None
        ):

            try:

                if (
                    aplicacion.aplicada
                    and aplicacion.cambio_id
                ):

                    self.registro_propuestas.marcar_aplicada(
                        propuesta_id,
                        cambio_id=(
                            aplicacion.cambio_id
                        ),
                    )

                elif not aplicacion.aplicada:

                    self.registro_propuestas.marcar_estado(
                        propuesta_id,
                        EstadoPropuesta.VALIDADA,
                    )

            except Exception as error:

                print(
                    "[ATENAS][AUTOMEJORA][REGISTRO] "
                    "No fue posible actualizar el "
                    f"estado de la propuesta: {error}"
                )

        resultado = ResultadoCicloAutoMejora(
            ok=True,
            estado=(
                "aplicado"
                if aplicacion.aplicada
                else "no_aplicado"
            ),
            informe=informe,
            resultado_motor=(
                resultado_motor
            ),
            aplicacion=aplicacion,
            aplicada=(
                aplicacion.aplicada
            ),
            requiere_confirmacion=(
                aplicacion
                .decision
                .requiere_confirmacion
            ),
            propuesta_id=(
                propuesta_id
            ),
            mensaje=(
                aplicacion.mensaje
            ),
        )

        self.ultimo_resultado = resultado

        return resultado