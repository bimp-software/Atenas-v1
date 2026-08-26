from __future__ import annotations

import time

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from .gestor_confirmaciones import GestorConfirmaciones
from .registro_actividad_agente import RegistroActividadAgente


class EstadoHeartbeat(str, Enum):
    ACTIVO = "activo"
    EN_ESPERA = "en_espera"
    BLOQUEADO = "bloqueado"
    ERROR = "error"


@dataclass
class ResultadoHeartbeat:
    ok: bool
    estado: EstadoHeartbeat

    ciclo: int = 0
    mensaje: str = ""

    supervision: dict[str, Any] = field(default_factory=dict)
    accion: dict[str, Any] = field(default_factory=dict)

    error: str | None = None


class MotorHeartbeatAgente:
    """
    Motor de un ciclo autónomo controlado.

    Cada tick:
      1. revisa confirmaciones;
      2. supervisa la sesión;
      3. ejecuta UNA unidad de decisión/acción;
      4. registra actividad.

    run() permite repetir ticks, pero nunca elimina los controles
    de autonomía ni las confirmaciones.
    """

    def __init__(
        self,
        supervisar: Callable[[], dict[str, Any]],
        actuar: Callable[[], dict[str, Any]],
        confirmaciones: GestorConfirmaciones,
        actividad: RegistroActividadAgente,
    ):
        self.supervisar = supervisar
        self.actuar = actuar
        self.confirmaciones = confirmaciones
        self.actividad = actividad
        self.numero_ciclo = 0

    @staticmethod
    def _ahora() -> str:
        return datetime.now(timezone.utc).isoformat()

    def tick(self) -> ResultadoHeartbeat:
        self.numero_ciclo += 1
        inicio = time.perf_counter()

        pendientes = self.confirmaciones.pendientes()

        if pendientes:
            item = pendientes[0]

            self.actividad.registrar(
                categoria="heartbeat",
                accion="esperar_confirmacion",
                mensaje=item.descripcion,
                ok=True,
                sesion_id=item.sesion_id,
                tarea_id=item.tarea_id,
                proyecto_id=item.proyecto_id,
                datos={
                    "confirmacion_id": item.id,
                    "riesgo": item.riesgo,
                },
            )

            return ResultadoHeartbeat(
                ok=True,
                estado=EstadoHeartbeat.BLOQUEADO,
                ciclo=self.numero_ciclo,
                mensaje="Existe una confirmación humana pendiente.",
                accion={
                    "confirmacion_id": item.id,
                    "accion": item.accion,
                },
            )

        try:
            supervision = self.supervisar()

            # supervisar() puede crear/reanudar/asociar trabajo.
            # Luego actuar() elige la siguiente unidad real.
            accion = self.actuar()

            duracion = (time.perf_counter() - inicio) * 1000.0

            self.actividad.registrar(
                categoria="heartbeat",
                accion="tick",
                mensaje="Ciclo autónomo ejecutado.",
                ok=True,
                sesion_id=(
                    supervision.get("sesion_id")
                    if isinstance(supervision, dict)
                    else None
                ),
                tarea_id=(
                    accion.get("tarea_id")
                    if isinstance(accion, dict)
                    else None
                ),
                duracion_ms=duracion,
                datos={
                    "supervision": supervision,
                    "accion": accion,
                },
            )

            actuo = bool(
                accion.get("actuo", False)
                if isinstance(accion, dict)
                else False
            )

            return ResultadoHeartbeat(
                ok=True,
                estado=(
                    EstadoHeartbeat.ACTIVO
                    if actuo
                    else EstadoHeartbeat.EN_ESPERA
                ),
                ciclo=self.numero_ciclo,
                mensaje=(
                    "ATENAS ejecutó una unidad de trabajo."
                    if actuo
                    else "No había una acción ejecutable en este ciclo."
                ),
                supervision=(
                    supervision
                    if isinstance(supervision, dict)
                    else {}
                ),
                accion=(
                    accion
                    if isinstance(accion, dict)
                    else {}
                ),
            )

        except Exception as exc:
            duracion = (time.perf_counter() - inicio) * 1000.0

            self.actividad.registrar(
                categoria="heartbeat",
                accion="error_tick",
                mensaje=str(exc),
                ok=False,
                duracion_ms=duracion,
                datos={
                    "tipo_error": type(exc).__name__,
                },
            )

            return ResultadoHeartbeat(
                ok=False,
                estado=EstadoHeartbeat.ERROR,
                ciclo=self.numero_ciclo,
                mensaje="El ciclo autónomo produjo un error.",
                error=f"{type(exc).__name__}: {exc}",
            )

    def run(
        self,
        max_ciclos: int = 1,
        intervalo_segundos: float = 0.25,
        detener_si_espera: bool = True,
    ) -> list[ResultadoHeartbeat]:
        resultados = []

        for indice in range(max(1, int(max_ciclos))):
            resultado = self.tick()
            resultados.append(resultado)

            if resultado.estado in {
                EstadoHeartbeat.BLOQUEADO,
                EstadoHeartbeat.ERROR,
            }:
                break

            if (
                detener_si_espera
                and resultado.estado == EstadoHeartbeat.EN_ESPERA
            ):
                break

            if indice + 1 < max_ciclos:
                time.sleep(max(0.0, float(intervalo_segundos)))

        return resultados