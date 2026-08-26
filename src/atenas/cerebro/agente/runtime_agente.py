from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .agente import AgenteAtenas
from .capacidad_sistema import CapacidadSistema
from .gestor_confirmaciones import GestorConfirmaciones
from .gestor_contexto_operativo import GestorContextoOperativo
from .gestor_sesion_trabajo import GestorSesionTrabajo
from .registro_actividad_agente import RegistroActividadAgente


@dataclass
class RuntimeAtenas:
    """
    Contenedor principal del Agente V1.

    Garantiza que AgenteAtenas y CapacidadSistema compartan
    las MISMAS instancias persistentes de:
    - contexto operativo;
    - sesiones;
    - confirmaciones;
    - actividad.

    Esto evita estados duplicados al integrar luego con NucleoAtenas.
    """

    agente: AgenteAtenas
    capacidad_sistema: CapacidadSistema

    contexto_operativo: GestorContextoOperativo
    gestor_sesiones: GestorSesionTrabajo
    gestor_confirmaciones: GestorConfirmaciones
    registro_actividad: RegistroActividadAgente

    @classmethod
    def crear(
        cls,
        raiz_datos: str | Path = "data/agente",
    ) -> "RuntimeAtenas":

        raiz = Path(
            raiz_datos
        ).expanduser().resolve()

        raiz.mkdir(
            parents=True,
            exist_ok=True,
        )

        contexto = GestorContextoOperativo(
            raiz
            / "contexto_operativo"
            / "contexto.json"
        )

        sesiones = GestorSesionTrabajo(
            raiz
            / "sesiones_trabajo"
            / "sesiones.json"
        )

        confirmaciones = GestorConfirmaciones(
            raiz
            / "confirmaciones"
            / "confirmaciones.json"
        )

        actividad = RegistroActividadAgente(
            raiz
            / "actividad"
            / "actividad.jsonl"
        )

        capacidad = CapacidadSistema(
            contexto_operativo=contexto,
            gestor_sesiones=sesiones,
            gestor_confirmaciones=confirmaciones,
            registro_actividad=actividad,
        )

        agente = AgenteAtenas(
            capacidad_sistema=capacidad,
            contexto_operativo=contexto,
            gestor_sesiones=sesiones,
            gestor_confirmaciones=confirmaciones,
            registro_actividad=actividad,
        )

        return cls(
            agente=agente,
            capacidad_sistema=capacidad,
            contexto_operativo=contexto,
            gestor_sesiones=sesiones,
            gestor_confirmaciones=confirmaciones,
            registro_actividad=actividad,
        )

    def estado(
        self,
    ) -> dict:
        return (
            self.agente
            .estado_actual_dict()
        )

    def tick(
        self,
    ):
        return (
            self.agente
            .tick_autonomo()
        )

    def ejecutar(
        self,
        ciclos: int = 1,
        intervalo_segundos: float = 0.25,
    ):
        return (
            self.agente
            .ejecutar_ciclos_autonomos(
                max_ciclos=ciclos,
                intervalo_segundos=intervalo_segundos,
            )
        )