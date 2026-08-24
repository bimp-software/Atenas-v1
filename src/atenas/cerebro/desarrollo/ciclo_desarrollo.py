from __future__ import annotations

import json

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .director_desarrollo import (
    ResultadoDirectorDesarrollo,
    TipoIniciativaDesarrollo,
)


@dataclass
class EstadoCicloDesarrollo:
    turnos_desde_revision: int = 0
    revisiones_totales: int = 0
    ejecuciones_totales: int = 0

    ultima_revision: str | None = None
    ultima_ejecucion: str | None = None

    ultima_iniciativa: str | None = None
    ultimo_resultado: str | None = None


@dataclass
class ResultadoCicloDesarrollo:
    ok: bool

    revisado: bool

    ejecutado: bool

    motivo: str

    resultado_director: ResultadoDirectorDesarrollo | None = None

    error: str | None = None


class CicloDesarrolloAutonomo:
    """
    Ciclo de iniciativa general para el desarrollo interno de ATENAS.

    A diferencia del antiguo ciclo de vida dedicado solo a
    automejora, este ciclo pregunta:

        "¿Qué trabajo de ingeniería necesito hacer ahora?"

    Puede terminar en:
    - reparar un error;
    - revalidar una propuesta;
    - preparar una mejora;
    - crear tests;
    - organizar/refactorizar;
    - no hacer nada.

    Seguridad:
    - por defecto NO permite aplicar cambios al proyecto real;
    - respeta el DirectorDesarrolloAutonomo;
    - respeta políticas, sandbox, tests, historial y rollback;
    - limita la frecuencia para evitar bucles de autorrevisión.
    """

    def __init__(
        self,
        desarrollo,
        estado_path: str | Path,
        revisar_cada_turnos: int = 10,
        cooldown_minutos: int = 30,
        max_ejecuciones_diarias: int = 12,
        permitir_aplicacion_automatica: bool = False,
    ):
        self.desarrollo = desarrollo

        self.estado_path = Path(
            estado_path
        ).resolve()

        self.estado_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.revisar_cada_turnos = max(
            1,
            int(revisar_cada_turnos),
        )

        self.cooldown = timedelta(
            minutes=max(
                0,
                int(cooldown_minutos),
            )
        )

        self.max_ejecuciones_diarias = max(
            1,
            int(max_ejecuciones_diarias),
        )

        self.permitir_aplicacion_automatica = bool(
            permitir_aplicacion_automatica
        )

        self.estado = (
            self._cargar_estado()
        )

        self._fecha_contador = None
        self._ejecuciones_hoy = 0

    # =========================================================
    # TIEMPO
    # =========================================================

    @staticmethod
    def _ahora() -> datetime:

        return datetime.now(
            timezone.utc
        )

    # =========================================================
    # PERSISTENCIA
    # =========================================================

    def _cargar_estado(
        self,
    ) -> EstadoCicloDesarrollo:

        if not self.estado_path.exists():

            return EstadoCicloDesarrollo()

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

                return EstadoCicloDesarrollo()

            return EstadoCicloDesarrollo(
                turnos_desde_revision=int(
                    datos.get(
                        "turnos_desde_revision",
                        0,
                    )
                    or 0
                ),
                revisiones_totales=int(
                    datos.get(
                        "revisiones_totales",
                        0,
                    )
                    or 0
                ),
                ejecuciones_totales=int(
                    datos.get(
                        "ejecuciones_totales",
                        0,
                    )
                    or 0
                ),
                ultima_revision=datos.get(
                    "ultima_revision"
                ),
                ultima_ejecucion=datos.get(
                    "ultima_ejecucion"
                ),
                ultima_iniciativa=datos.get(
                    "ultima_iniciativa"
                ),
                ultimo_resultado=datos.get(
                    "ultimo_resultado"
                ),
            )

        except Exception:

            return EstadoCicloDesarrollo()

    def _guardar_estado(
        self,
    ) -> None:

        datos = {
            "turnos_desde_revision":
                self.estado.turnos_desde_revision,

            "revisiones_totales":
                self.estado.revisiones_totales,

            "ejecuciones_totales":
                self.estado.ejecuciones_totales,

            "ultima_revision":
                self.estado.ultima_revision,

            "ultima_ejecucion":
                self.estado.ultima_ejecucion,

            "ultima_iniciativa":
                self.estado.ultima_iniciativa,

            "ultimo_resultado":
                self.estado.ultimo_resultado,
        }

        self.estado_path.write_text(
            json.dumps(
                datos,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    # =========================================================
    # TURNO
    # =========================================================

    def registrar_turno(
        self,
    ) -> None:

        self.estado.turnos_desde_revision += 1

        self._guardar_estado()

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

        if self._fecha_contador != fecha:

            self._fecha_contador = fecha
            self._ejecuciones_hoy = 0

    # =========================================================
    # COOLDOWN
    # =========================================================

    def _ultima_ejecucion_dt(
        self,
    ) -> datetime | None:

        valor = (
            self.estado.ultima_ejecucion
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
    # ¿CORRESPONDE REVISAR?
    # =========================================================

    def debe_revisar(
        self,
        forzar: bool = False,
    ) -> tuple[bool, str]:

        if self.desarrollo is None:

            return (
                False,
                "Sistema de desarrollo no disponible.",
            )

        if forzar:

            return (
                True,
                "Revisión forzada.",
            )

        if (
            self.estado.turnos_desde_revision
            < self.revisar_cada_turnos
        ):

            return (
                False,
                "Todavía no corresponde una revisión.",
            )

        ahora = self._ahora()

        self._actualizar_contador_diario(
            ahora
        )

        if (
            self._ejecuciones_hoy
            >= self.max_ejecuciones_diarias
        ):

            return (
                False,
                "Se alcanzó el límite diario de "
                "ejecuciones de desarrollo autónomo.",
            )

        ultima = (
            self._ultima_ejecucion_dt()
        )

        if ultima is not None:

            transcurrido = (
                ahora
                - ultima
            )

            if transcurrido < self.cooldown:

                return (
                    False,
                    "El ciclo de desarrollo está "
                    "en cooldown.",
                )

        return (
            True,
            "Corresponde revisar el estado de desarrollo.",
        )

    # =========================================================
    # REVISAR / EJECUTAR
    # =========================================================

    def revisar_si_corresponde(
        self,
        tests: list[str] | None = None,
        forzar: bool = False,
        permitir_aplicacion: bool | None = None,
    ) -> ResultadoCicloDesarrollo:

        permitido, motivo = (
            self.debe_revisar(
                forzar=forzar
            )
        )

        if not permitido:

            return ResultadoCicloDesarrollo(
                ok=True,
                revisado=False,
                ejecutado=False,
                motivo=motivo,
            )

        ahora = self._ahora()

        self.estado.turnos_desde_revision = 0
        self.estado.revisiones_totales += 1
        self.estado.ultima_revision = (
            ahora.isoformat()
        )

        try:

            iniciativa = (
                self.desarrollo
                .decidir_siguiente_trabajo_desarrollo()
            )

        except Exception as error:

            self.estado.ultimo_resultado = (
                "fallo_decision"
            )

            self._guardar_estado()

            return ResultadoCicloDesarrollo(
                ok=False,
                revisado=True,
                ejecutado=False,
                motivo=(
                    "Falló la decisión de desarrollo."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        self.estado.ultima_iniciativa = (
            iniciativa.tipo.value
        )

        if (
            iniciativa.tipo
            == TipoIniciativaDesarrollo.SIN_ACCION
        ):

            self.estado.ultimo_resultado = (
                "sin_accion"
            )

            self._guardar_estado()

            return ResultadoCicloDesarrollo(
                ok=True,
                revisado=True,
                ejecutado=False,
                motivo=(
                    iniciativa.descripcion
                ),
            )

        if permitir_aplicacion is None:

            aplicar = (
                self.permitir_aplicacion_automatica
            )

        else:

            aplicar = bool(
                permitir_aplicacion
            )

        # Nunca se fuerza una aplicación por encima de la
        # decisión de seguridad de la iniciativa.
        aplicar = bool(
            aplicar
            and iniciativa.puede_ejecutarse_sola
            and not iniciativa.requiere_confirmacion
        )

        try:

            resultado_director = (
                self.desarrollo
                .ejecutar_siguiente_trabajo_desarrollo(
                    tests=tests,
                    permitir_aplicacion=(
                        aplicar
                    ),
                )
            )

        except Exception as error:

            self.estado.ultimo_resultado = (
                "fallo_ejecucion"
            )

            self._guardar_estado()

            return ResultadoCicloDesarrollo(
                ok=False,
                revisado=True,
                ejecutado=False,
                motivo=(
                    "Falló la ejecución del "
                    "trabajo de desarrollo."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        self._actualizar_contador_diario(
            ahora
        )

        self._ejecuciones_hoy += 1

        self.estado.ejecuciones_totales += 1
        self.estado.ultima_ejecucion = (
            ahora.isoformat()
        )

        self.estado.ultimo_resultado = (
            "ok"
            if resultado_director.ok
            else "error"
        )

        self._guardar_estado()

        return ResultadoCicloDesarrollo(
            ok=bool(
                resultado_director.ok
            ),
            revisado=True,
            ejecutado=bool(
                resultado_director.ejecutada
            ),
            motivo=(
                resultado_director.mensaje
                or iniciativa.descripcion
            ),
            resultado_director=(
                resultado_director
            ),
            error=(
                resultado_director.error
            ),
        )

    # =========================================================
    # CONTEXTO
    # =========================================================

    def contexto_para_llm(
        self,
    ) -> str:

        return (
            "CICLO AUTÓNOMO DE DESARROLLO:\n"
            f"- Turnos desde revisión: "
            f"{self.estado.turnos_desde_revision}\n"
            f"- Revisiones totales: "
            f"{self.estado.revisiones_totales}\n"
            f"- Ejecuciones totales: "
            f"{self.estado.ejecuciones_totales}\n"
            f"- Última iniciativa: "
            f"{self.estado.ultima_iniciativa or 'ninguna'}\n"
            f"- Último resultado: "
            f"{self.estado.ultimo_resultado or 'ninguno'}\n"
            "- La aplicación automática de cambios "
            f"está "
            f"{'habilitada' if self.permitir_aplicacion_automatica else 'deshabilitada'}."
        )