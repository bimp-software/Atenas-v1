from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EstadoMundo:
    usuario_activo: bool = True

    app_activa: str | None = None

    proyecto_actual: str | None = None

    ultimo_mensaje: str | None = None

    contexto: dict = field(
        default_factory=dict
    )

    def actualizar_mensaje(
        self,
        mensaje: str,
    ) -> None:
        self.ultimo_mensaje = mensaje

    def establecer_proyecto(
        self,
        nombre: str,
    ) -> None:
        self.proyecto_actual = nombre