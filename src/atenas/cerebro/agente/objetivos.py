from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

class EstadoObjetivo(str, Enum):
    ACTIVO = "activo"
    PAUSADO = "pausado"
    COMPLETADO = "completado"

@dataclass
class Objetivo:
    id: str
    nombre: str
    descripcion: str
    prioridad: float = 0.5
    estado: EstadoObjetivo = EstadoObjetivo.ACTIVO
    autonomia: bool = True

class GestorObjetivos:

    def __init__(self):
        self._objetivos: dict[str, Objetivo] = {}

    def cargar(
        self,
        objetivos: list[Objetivo],
    ) -> None:

        for objetivo in objetivos:
            self._objetivos[
                objetivo.id
            ] = objetivo

    def agregar(
        self,
        objetivo: Objetivo,
    ) -> None:
        self._objetivos[objetivo.id] = objetivo

    def obtener(
        self,
        objetivo_id: str,
    ) -> Objetivo | None:
        return self._objetivos.get(objetivo_id)

    def activos(self) -> list[Objetivo]:
        return sorted(
            [
                objetivo
                for objetivo in self._objetivos.values()
                if objetivo.estado == EstadoObjetivo.ACTIVO
            ],
            key=lambda obj: obj.prioridad,
            reverse=True,
        )

    def completar(
        self,
        objetivo_id: str,
    ) -> bool:
        objetivo = self.obtener(objetivo_id)

        if not objetivo:
            return False

        objetivo.estado = EstadoObjetivo.COMPLETADO
        return True