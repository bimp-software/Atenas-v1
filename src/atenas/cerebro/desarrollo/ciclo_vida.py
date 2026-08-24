from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class EstadoCicloVida:
    turnos_desde_revision: int = 0
    total_revisiones: int = 0
    ultima_revision: str | None = None


class GestorCicloVidaAtenas:
    """
    Decide cuándo conviene consultar la iniciativa de automejora
    durante la vida normal de ATENAS.

    No aplica mejoras por sí mismo. Solo puede solicitar una
    revisión al SistemaDesarrolloAtenas, que mantiene la
    aplicación automática desactivada por defecto.
    """

    def __init__(
        self,
        desarrollo,
        revisar_cada_turnos: int = 20,
    ):
        self.desarrollo = desarrollo

        self.revisar_cada_turnos = max(
            1,
            int(revisar_cada_turnos),
        )

        self.estado = EstadoCicloVida()

    def registrar_turno(
        self,
    ) -> None:
        self.estado.turnos_desde_revision += 1

    def debe_revisar(
        self,
    ) -> bool:
        if self.desarrollo is None:
            return False

        return (
            self.estado.turnos_desde_revision
            >= self.revisar_cada_turnos
        )

    def revisar_si_corresponde(
        self,
        tests: list[str] | None = None,
    ):
        if not self.debe_revisar():
            return None

        resultado = (
            self.desarrollo
            .ejecutar_iniciativa_automejora(
                tests=tests,
                forzar=False,
                permitir_aplicacion=False,
            )
        )

        self.estado.turnos_desde_revision = 0
        self.estado.total_revisiones += 1
        self.estado.ultima_revision = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        return resultado