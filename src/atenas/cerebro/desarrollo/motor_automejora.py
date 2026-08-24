from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .automejora import (
    HallazgoMejora,
    InformeAutoMejora,
    TipoHallazgo,
)

from .planificador_mejoras import (
    PlanificadorMejoras,
    PropuestaMejora,
)

from .politica import (
    NivelRiesgo,
    PoliticaDesarrollo,
)


@dataclass
class DecisionAutoMejora:
    intentar: bool

    motivo: str

    hallazgo: HallazgoMejora | None = None

    score: float = 0.0

    requiere_confirmacion: bool = False


@dataclass
class ResultadoMotorAutoMejora:
    procesado: bool

    decision: DecisionAutoMejora

    propuesta: PropuestaMejora | None = None

    error: str | None = None


class MotorAutoMejora:
    """
    Decide qué oportunidad de mejora conviene estudiar.

    Este motor NO aplica cambios al proyecto real.

    Flujo:

        InformeAutoMejora
            ↓
        filtrar hallazgos
            ↓
        priorizar
            ↓
        elegir uno
            ↓
        PlanificadorMejoras
            ↓
        Qwen
            ↓
        sandbox + tests + verificación
            ↓
        propuesta validada

    La aplicación final queda fuera de este motor.
    """

    TIPOS_AUTORIZADOS = {
        TipoHallazgo.FUNCION_GRANDE,
        TipoHallazgo.CLASE_GRANDE,
        TipoHallazgo.MODULO_GRANDE,
        TipoHallazgo.MUCHOS_IMPORTS,
        TipoHallazgo.TEST_FALTANTE,
        TipoHallazgo.ERROR_REPETIDO,
    }

    # Hallazgos que normalmente tienen más valor para empezar.
    PESO_TIPO = {
        TipoHallazgo.ERROR_REPETIDO: 1.00,
        TipoHallazgo.FUNCION_GRANDE: 0.95,
        TipoHallazgo.CLASE_GRANDE: 0.85,
        TipoHallazgo.MODULO_GRANDE: 0.80,
        TipoHallazgo.MUCHOS_IMPORTS: 0.65,
        TipoHallazgo.TEST_FALTANTE: 0.55,
        TipoHallazgo.CODIGO_DUPLICADO_SIMPLE: 0.50,
    }

    def __init__(
        self,
        politica: PoliticaDesarrollo,
        planificador: PlanificadorMejoras,
        severidad_minima: float = 0.55,
        confianza_minima: float = 0.75,
        permitir_riesgo_medio: bool = False,
    ):
        self.politica = politica
        self.planificador = planificador

        self.severidad_minima = max(
            0.0,
            min(
                float(severidad_minima),
                1.0,
            ),
        )

        self.confianza_minima = max(
            0.0,
            min(
                float(confianza_minima),
                1.0,
            ),
        )

        self.permitir_riesgo_medio = bool(
            permitir_riesgo_medio
        )

    # =========================================================
    # SCORE
    # =========================================================

    def _score(
        self,
        hallazgo: HallazgoMejora,
    ) -> float:

        peso_tipo = (
            self.PESO_TIPO
            .get(
                hallazgo.tipo,
                0.40,
            )
        )

        score = (
            hallazgo.severidad * 0.45
            + hallazgo.confianza * 0.35
            + peso_tipo * 0.20
        )

        if hallazgo.requiere_confirmacion:
            score -= 0.10

        if (
            hallazgo.riesgo_estimado
            == NivelRiesgo.MEDIO
        ):
            score -= 0.15

        if (
            hallazgo.riesgo_estimado
            in {
                NivelRiesgo.ALTO,
                NivelRiesgo.CRITICO,
            }
        ):
            score -= 0.50

        return max(
            0.0,
            min(
                score,
                1.0,
            ),
        )

    # =========================================================
    # ¿ES CANDIDATO?
    # =========================================================

    def _es_candidato(
        self,
        hallazgo: HallazgoMejora,
    ) -> tuple[bool, str]:

        if (
            hallazgo.tipo
            not in self.TIPOS_AUTORIZADOS
        ):

            return (
                False,
                "El tipo de hallazgo no está habilitado.",
            )

        if (
            hallazgo.severidad
            < self.severidad_minima
        ):

            return (
                False,
                "La severidad es demasiado baja.",
            )

        if (
            hallazgo.confianza
            < self.confianza_minima
        ):

            return (
                False,
                "La confianza del hallazgo es insuficiente.",
            )

        evaluacion = (
            self.politica
            .evaluar_modificacion(
                hallazgo.archivo
            )
        )

        if not evaluacion.permitido:

            return (
                False,
                (
                    "La política bloqueó el archivo: "
                    f"{evaluacion.motivo}"
                ),
            )

        if (
            evaluacion.riesgo
            in {
                NivelRiesgo.ALTO,
                NivelRiesgo.CRITICO,
            }
        ):

            return (
                False,
                "El archivo tiene un nivel de riesgo demasiado alto.",
            )

        if (
            evaluacion.riesgo
            == NivelRiesgo.MEDIO
            and not self.permitir_riesgo_medio
        ):

            return (
                False,
                "El archivo es de riesgo medio y este motor solo estudia riesgo bajo.",
            )

        return (
            True,
            "Hallazgo apto para propuesta de mejora.",
        )

    # =========================================================
    # CANDIDATOS
    # =========================================================

    def candidatos(
        self,
        informe: InformeAutoMejora,
        limite: int = 20,
    ) -> list[
        tuple[HallazgoMejora, float]
    ]:

        candidatos = []

        for hallazgo in (
            informe.hallazgos
        ):

            permitido, _ = (
                self._es_candidato(
                    hallazgo
                )
            )

            if not permitido:
                continue

            candidatos.append(
                (
                    hallazgo,
                    self._score(
                        hallazgo
                    ),
                )
            )

        candidatos.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return candidatos[
            :max(
                1,
                int(limite),
            )
        ]

    # =========================================================
    # DECIDIR
    # =========================================================

    def decidir(
        self,
        informe: InformeAutoMejora,
    ) -> DecisionAutoMejora:

        candidatos = (
            self.candidatos(
                informe,
                limite=1,
            )
        )

        if not candidatos:

            return DecisionAutoMejora(
                intentar=False,
                motivo=(
                    "No existen hallazgos con suficiente "
                    "severidad, confianza y seguridad."
                ),
            )

        hallazgo, score = (
            candidatos[0]
        )

        evaluacion = (
            self.politica
            .evaluar_modificacion(
                hallazgo.archivo
            )
        )

        return DecisionAutoMejora(
            intentar=True,

            motivo=(
                "Es el hallazgo seguro con mayor prioridad "
                "según severidad, confianza y tipo."
            ),

            hallazgo=hallazgo,

            score=score,

            requiere_confirmacion=(
                evaluacion
                .requiere_confirmacion
            ),
        )

    # =========================================================
    # PROCESAR
    # =========================================================

    def procesar(
        self,
        informe: InformeAutoMejora,
        tests: list[str] | None = None,
    ) -> ResultadoMotorAutoMejora:

        decision = (
            self.decidir(
                informe
            )
        )

        if (
            not decision.intentar
            or decision.hallazgo is None
        ):

            return ResultadoMotorAutoMejora(
                procesado=False,
                decision=decision,
                propuesta=None,
            )

        try:

            propuesta = (
                self.planificador
                .proponer(
                    hallazgo=(
                        decision.hallazgo
                    ),
                    tests=tests,
                )
            )

        except Exception as error:

            return ResultadoMotorAutoMejora(
                procesado=True,
                decision=decision,
                propuesta=None,
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        return ResultadoMotorAutoMejora(
            procesado=True,
            decision=decision,
            propuesta=propuesta,
        )