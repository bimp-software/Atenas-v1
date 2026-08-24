from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .ciclo_automejora import (
    CicloAutoMejora,
    ResultadoCicloAutoMejora,
)


@dataclass
class DecisionIniciativaAutoMejora:
    ejecutar: bool

    motivo: str

    permitir_aplicacion: bool = False

    intentos_hoy: int = 0

    ultima_ejecucion: str | None = None


@dataclass
class ResultadoIniciativaAutoMejora:
    ok: bool

    decision: DecisionIniciativaAutoMejora

    ciclo: ResultadoCicloAutoMejora | None = None

    error: str | None = None


class IniciativaAutoMejora:
    """
    Decide CUÁNDO ATENAS debe iniciar por sí misma un ciclo
    de automejora.

    Esta capa evita que ATENAS analice o modifique su código
    continuamente.

    Controles:

    - cooldown entre ciclos;
    - máximo de ciclos diarios;
    - persistencia del último intento;
    - aplicación automática desactivada por defecto;
    - posibilidad de ejecutar solo una propuesta por ciclo.

    El estado se guarda en JSON para sobrevivir reinicios.
    """

    def __init__(
        self,
        ciclo: CicloAutoMejora,
        estado_path: str | Path,
        cooldown_minutos: int = 360,
        max_ciclos_diarios: int = 3,
        autoaplicar: bool = False,
    ):
        self.ciclo = ciclo

        self.estado_path = Path(
            estado_path
        )

        self.estado_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.cooldown = timedelta(
            minutes=max(
                0,
                int(cooldown_minutos),
            )
        )

        self.max_ciclos_diarios = max(
            1,
            int(max_ciclos_diarios),
        )

        self.autoaplicar = bool(
            autoaplicar
        )

        self._estado = (
            self._cargar_estado()
        )

    # =========================================================
    # ESTADO
    # =========================================================

    @staticmethod
    def _ahora() -> datetime:

        return datetime.now(
            timezone.utc
        )

    def _estado_inicial(
        self,
    ) -> dict:

        return {
            "ultima_ejecucion": None,
            "fecha_contador": None,
            "intentos_hoy": 0,
            "ultimo_estado": None,
            "ultimo_error": None,
        }

    def _cargar_estado(
        self,
    ) -> dict:

        if not self.estado_path.exists():
            return self._estado_inicial()

        try:

            datos = json.loads(
                self.estado_path.read_text(
                    encoding="utf-8"
                )
            )

            if not isinstance(
                datos,
                dict,
            ):
                return self._estado_inicial()

            base = self._estado_inicial()
            base.update(
                datos
            )

            return base

        except Exception:

            return self._estado_inicial()

    def _guardar_estado(
        self,
    ) -> None:

        self.estado_path.write_text(
            json.dumps(
                self._estado,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    # =========================================================
    # CONTADOR DIARIO
    # =========================================================

    def _actualizar_contador_diario(
        self,
        ahora: datetime,
    ) -> None:

        fecha = (
            ahora.date()
            .isoformat()
        )

        if (
            self._estado.get(
                "fecha_contador"
            )
            != fecha
        ):

            self._estado[
                "fecha_contador"
            ] = fecha

            self._estado[
                "intentos_hoy"
            ] = 0

    # =========================================================
    # ÚLTIMA EJECUCIÓN
    # =========================================================

    def _ultima_ejecucion_dt(
        self,
    ) -> datetime | None:

        valor = (
            self._estado.get(
                "ultima_ejecucion"
            )
        )

        if not valor:
            return None

        try:

            return datetime.fromisoformat(
                valor
            )

        except ValueError:

            return None

    # =========================================================
    # DECIDIR
    # =========================================================

    def decidir(
        self,
        forzar: bool = False,
        permitir_aplicacion: bool | None = None,
    ) -> DecisionIniciativaAutoMejora:

        ahora = self._ahora()

        self._actualizar_contador_diario(
            ahora
        )

        intentos_hoy = int(
            self._estado.get(
                "intentos_hoy",
                0,
            )
            or 0
        )

        ultima = (
            self._ultima_ejecucion_dt()
        )

        aplicar = (
            self.autoaplicar
            if permitir_aplicacion
            is None
            else bool(
                permitir_aplicacion
            )
        )

        if forzar:

            return DecisionIniciativaAutoMejora(
                ejecutar=True,
                motivo=(
                    "El ciclo fue solicitado "
                    "de forma forzada."
                ),
                permitir_aplicacion=(
                    aplicar
                ),
                intentos_hoy=(
                    intentos_hoy
                ),
                ultima_ejecucion=(
                    ultima.isoformat()
                    if ultima
                    else None
                ),
            )

        if (
            intentos_hoy
            >= self.max_ciclos_diarios
        ):

            return DecisionIniciativaAutoMejora(
                ejecutar=False,
                motivo=(
                    "Se alcanzó el máximo de "
                    "ciclos de automejora del día."
                ),
                permitir_aplicacion=False,
                intentos_hoy=(
                    intentos_hoy
                ),
                ultima_ejecucion=(
                    ultima.isoformat()
                    if ultima
                    else None
                ),
            )

        if ultima is not None:

            transcurrido = (
                ahora
                - ultima
            )

            if (
                transcurrido
                < self.cooldown
            ):

                faltante = (
                    self.cooldown
                    - transcurrido
                )

                return DecisionIniciativaAutoMejora(
                    ejecutar=False,
                    motivo=(
                        "ATENAS ya ejecutó un ciclo "
                        "recientemente. Falta aproximadamente "
                        f"{int(faltante.total_seconds() // 60)} "
                        "minutos para el siguiente."
                    ),
                    permitir_aplicacion=False,
                    intentos_hoy=(
                        intentos_hoy
                    ),
                    ultima_ejecucion=(
                        ultima.isoformat()
                    ),
                )

        return DecisionIniciativaAutoMejora(
            ejecutar=True,
            motivo=(
                "No existe un ciclo reciente y "
                "el límite diario permite revisar "
                "oportunidades de mejora."
            ),
            permitir_aplicacion=(
                aplicar
            ),
            intentos_hoy=(
                intentos_hoy
            ),
            ultima_ejecucion=(
                ultima.isoformat()
                if ultima
                else None
            ),
        )

    # =========================================================
    # EJECUTAR SI CORRESPONDE
    # =========================================================

    def ejecutar_si_corresponde(
        self,
        tests: list[str] | None = None,
        forzar: bool = False,
        permitir_aplicacion: bool | None = None,
        limite_archivos: int | None = None,
    ) -> ResultadoIniciativaAutoMejora:

        decision = (
            self.decidir(
                forzar=forzar,
                permitir_aplicacion=(
                    permitir_aplicacion
                ),
            )
        )

        if not decision.ejecutar:

            return ResultadoIniciativaAutoMejora(
                ok=True,
                decision=decision,
                ciclo=None,
            )

        ahora = self._ahora()

        self._actualizar_contador_diario(
            ahora
        )

        self._estado[
            "intentos_hoy"
        ] = (
            int(
                self._estado.get(
                    "intentos_hoy",
                    0,
                )
                or 0
            )
            + 1
        )

        self._estado[
            "ultima_ejecucion"
        ] = (
            ahora.isoformat()
        )

        self._guardar_estado()

        try:

            resultado_ciclo = (
                self.ciclo
                .ejecutar(
                    tests=tests,
                    permitir_aplicacion=(
                        decision
                        .permitir_aplicacion
                    ),
                    limite_archivos=(
                        limite_archivos
                    ),
                )
            )

        except Exception as error:

            self._estado[
                "ultimo_estado"
            ] = "fallo"

            self._estado[
                "ultimo_error"
            ] = (
                f"{type(error).__name__}: "
                f"{error}"
            )

            self._guardar_estado()

            return ResultadoIniciativaAutoMejora(
                ok=False,
                decision=decision,
                ciclo=None,
                error=(
                    self._estado[
                        "ultimo_error"
                    ]
                ),
            )

        self._estado[
            "ultimo_estado"
        ] = (
            resultado_ciclo.estado
        )

        self._estado[
            "ultimo_error"
        ] = (
            resultado_ciclo.error
        )

        self._guardar_estado()

        return ResultadoIniciativaAutoMejora(
            ok=(
                resultado_ciclo.ok
            ),
            decision=decision,
            ciclo=(
                resultado_ciclo
            ),
            error=(
                resultado_ciclo.error
            ),
        )

    # =========================================================
    # CONSULTAR ESTADO
    # =========================================================

    def estado(
        self,
    ) -> dict:

        return dict(
            self._estado
        )