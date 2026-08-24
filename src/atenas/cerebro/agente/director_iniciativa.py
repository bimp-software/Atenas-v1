from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .capacidad_desarrollo import (
    CapacidadDesarrollo,
    ProyectoSoftwareAgente,
)

from .pendientes import (
    GestorPendientes,
    Pendiente,
)


class TipoTrabajoAgente(str, Enum):
    PENDIENTE = "pendiente"
    PROYECTO = "proyecto"
    NADA = "nada"


@dataclass
class TrabajoCandidato:
    tipo: TipoTrabajoAgente
    id: str | None
    descripcion: str

    score: float

    prioridad_base: float = 0.0
    urgencia: float = 0.0
    continuidad: float = 0.0
    explicito: float = 0.0

    datos: dict[str, Any] | None = None


class DirectorIniciativaAgente:
    """
    Selecciona qué merece atención en cada ciclo autónomo.

    No ejecuta trabajo: solo puntúa y elige.

    Criterios V1:
    - prioridad explícita;
    - urgencia;
    - solicitud directa del usuario;
    - continuidad de proyectos ya iniciados;
    - progreso;
    - bloqueos/estados terminales.

    Esto evita que ATENAS continúe siempre "el primer proyecto" y
    permite comparar trabajo heterogéneo.
    """

    def __init__(
        self,
        peso_prioridad: float = 0.45,
        peso_urgencia: float = 0.20,
        peso_explicito: float = 0.20,
        peso_continuidad: float = 0.15,
    ):
        self.peso_prioridad = peso_prioridad
        self.peso_urgencia = peso_urgencia
        self.peso_explicito = peso_explicito
        self.peso_continuidad = peso_continuidad

    @staticmethod
    def _clamp(valor: float) -> float:
        return max(
            0.0,
            min(
                1.0,
                float(valor),
            ),
        )

    # =========================================================
    # PENDIENTES
    # =========================================================

    def _candidato_pendiente(
        self,
        pendiente: Pendiente,
    ) -> TrabajoCandidato:

        prioridad = self._clamp(
            getattr(
                pendiente,
                "prioridad",
                0.5,
            )
            or 0.5
        )

        accion = (
            getattr(
                pendiente,
                "accion_sugerida",
                None,
            )
            or ""
        ).lower()

        mensaje_origen = (
            getattr(
                pendiente,
                "mensaje_origen",
                None,
            )
            or ""
        ).strip()

        explicito = (
            1.0
            if mensaje_origen
            else 0.35
        )

        urgencia = 0.0

        texto = (
            f"{pendiente.descripcion} "
            f"{mensaje_origen}"
        ).lower()

        if any(
            palabra in texto
            for palabra in (
                "urgente",
                "ahora",
                "hoy",
                "inmediato",
                "inmediatamente",
                "prioridad",
                "lo antes posible",
            )
        ):
            urgencia = 1.0

        elif any(
            palabra in texto
            for palabra in (
                "pronto",
                "después",
                "despues",
                "cuando puedas",
            )
        ):
            urgencia = 0.4

        continuidad = 0.0

        if (
            accion
            == "desarrollo_software:crear_proyecto"
        ):
            continuidad = 0.15

        score = (
            prioridad
            * self.peso_prioridad
            + urgencia
            * self.peso_urgencia
            + explicito
            * self.peso_explicito
            + continuidad
            * self.peso_continuidad
        )

        return TrabajoCandidato(
            tipo=TipoTrabajoAgente.PENDIENTE,
            id=pendiente.id,
            descripcion=pendiente.descripcion,
            score=round(
                score,
                4,
            ),
            prioridad_base=prioridad,
            urgencia=urgencia,
            continuidad=continuidad,
            explicito=explicito,
            datos={
                "accion_sugerida":
                    accion,

                "mensaje_origen":
                    mensaje_origen,
            },
        )

    # =========================================================
    # PROYECTOS
    # =========================================================

    def _candidato_proyecto(
        self,
        proyecto: ProyectoSoftwareAgente,
    ) -> TrabajoCandidato | None:

        if proyecto.estado in {
            "completado",
            "fallido",
            "bloqueado",
            "pausado",
        }:
            return None

        prioridad = self._clamp(
            proyecto.prioridad
        )

        progreso = self._clamp(
            proyecto.progreso
            / 100.0
        )

        # Favorece terminar trabajo ya avanzado sin convertirlo
        # en prioridad absoluta.
        continuidad = (
            0.35
            + 0.65
            * progreso
        )

        urgencia = self._clamp(
            proyecto.urgencia
        )

        explicito = (
            0.55
            if proyecto.creado_por
            == "usuario"
            else 0.35
        )

        score = (
            prioridad
            * self.peso_prioridad
            + urgencia
            * self.peso_urgencia
            + explicito
            * self.peso_explicito
            + continuidad
            * self.peso_continuidad
        )

        return TrabajoCandidato(
            tipo=TipoTrabajoAgente.PROYECTO,
            id=proyecto.id,
            descripcion=proyecto.nombre,
            score=round(
                score,
                4,
            ),
            prioridad_base=prioridad,
            urgencia=urgencia,
            continuidad=continuidad,
            explicito=explicito,
            datos={
                "estado":
                    proyecto.estado,

                "progreso":
                    proyecto.progreso,

                "carpeta":
                    proyecto.carpeta,
            },
        )

    # =========================================================
    # ELEGIR
    # =========================================================

    def candidatos(
        self,
        pendientes: GestorPendientes,
        capacidad_desarrollo: (
            CapacidadDesarrollo
            | None
        ),
        permitir_proyectos: bool = True,
    ) -> list[TrabajoCandidato]:

        resultado: list[
            TrabajoCandidato
        ] = []

        try:

            for pendiente in (
                pendientes.pendientes()
            ):

                resultado.append(
                    self._candidato_pendiente(
                        pendiente
                    )
                )

        except Exception:
            pass

        if (
            permitir_proyectos
            and capacidad_desarrollo
            is not None
        ):

            try:

                proyectos = (
                    capacidad_desarrollo
                    .proyectos_registrados()
                )

            except Exception:

                proyectos = []

            for proyecto in proyectos:

                candidato = (
                    self._candidato_proyecto(
                        proyecto
                    )
                )

                if candidato is not None:

                    resultado.append(
                        candidato
                    )

        resultado.sort(
            key=lambda item: (
                item.score,
                item.prioridad_base,
                item.continuidad,
            ),
            reverse=True,
        )

        return resultado

    def elegir(
        self,
        pendientes: GestorPendientes,
        capacidad_desarrollo: (
            CapacidadDesarrollo
            | None
        ),
        permitir_proyectos: bool = True,
    ) -> TrabajoCandidato:

        candidatos = self.candidatos(
            pendientes=pendientes,
            capacidad_desarrollo=(
                capacidad_desarrollo
            ),
            permitir_proyectos=(
                permitir_proyectos
            ),
        )

        if not candidatos:

            return TrabajoCandidato(
                tipo=TipoTrabajoAgente.NADA,
                id=None,
                descripcion=(
                    "No hay trabajo ejecutable."
                ),
                score=0.0,
            )

        return candidatos[0]