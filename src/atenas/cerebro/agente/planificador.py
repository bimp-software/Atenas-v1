from __future__ import annotations

from dataclasses import dataclass, field

from .pendientes import Pendiente
from .generador_acciones import GeneradorAcciones


@dataclass
class PasoPlan:
    herramienta: str
    argumentos: dict = field(
        default_factory=dict
    )

    requiere_confirmacion: bool = False


@dataclass
class Plan:
    descripcion: str
    pasos: list[PasoPlan]


class Planificador:

    def __init__(
        self,
        generador: GeneradorAcciones | None = None,
    ):
        self.generador = (
            generador
            or GeneradorAcciones()
        )

    def crear_plan(
        self,
        pendiente: Pendiente,
    ) -> Plan:

        accion = (
            pendiente.accion_sugerida
            or ""
        )

        # =====================================================
        # CREAR NOTA INTERNA
        # =====================================================

        if accion == "crear_nota":

            texto = (
                self.generador
                .generar_texto_nota(
                    mensaje_usuario=(
                        pendiente.mensaje_origen
                        or pendiente.descripcion
                    ),
                    descripcion_necesidad=(
                        pendiente.descripcion
                    ),
                )
            )

            return Plan(
                descripcion=pendiente.descripcion,
                pasos=[
                    PasoPlan(
                        herramienta="crear_nota",
                        argumentos={
                            "contenido": texto,
                        },
                    )
                ],
            )

        # =====================================================
        # MOSTRAR NOTA EN NOTEPAD
        # =====================================================

        if accion == "mostrar_nota":

            texto = (
                self.generador
                .generar_texto_nota(
                    mensaje_usuario=(
                        pendiente.mensaje_origen
                        or pendiente.descripcion
                    ),
                    descripcion_necesidad=(
                        pendiente.descripcion
                    ),
                )
            )

            return Plan(
                descripcion=pendiente.descripcion,
                pasos=[
                    PasoPlan(
                        herramienta="abrir_programa",
                        argumentos={
                            "programa": "notepad",
                        },
                    ),
                    PasoPlan(
                        herramienta="escribir_texto",
                        argumentos={
                            "texto": texto,
                            "espera_antes": 1.0,
                        },
                    ),
                ],
            )

        return Plan(
            descripcion=pendiente.descripcion,
            pasos=[],
        )