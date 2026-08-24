from __future__ import annotations
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

class EstadoTarea(str, Enum):
    ACTIVA = "activa"
    PAUSADA = "pausada"
    COMPLETADA = "completada"
    ERROR = "error"
    ELIMINADA = "eliminada"

class TipoDisparo(str, Enum):
    MANUAL = "manual"
    INTERVALO = "intervalo"
    FECHA = "fecha"
    EVENTO = "evento"

@dataclass
class TareaProgramada:
    id: str
    nombre: str
    descripcion: str
    herramienta: str
    argumentos: dict[str, Any] = field(default_factory=dict)
    tipo_disparo: TipoDisparo = TipoDisparo.MANUAL
    configuracion_disparo: dict[str, Any] = field(default_factory=dict)
    estado: EstadoTarea = EstadoTarea.ACTIVA
    requiere_confirmacion: bool = False
    origen: str = "usuario"
    creada_en: str = ""
    actualizada_en: str = ""
    ultima_ejecucion: str | None = None
    proxima_ejecucion: str | None = None
    ultimo_resultado: dict[str, Any] | None = None
    veces_ejecutada: int = 0

    def a_dict(self) -> dict[str, Any]:
        datos = asdict(self)
        datos["estado"] = self.estado.value
        datos["tipo_disparo"] = self.tipo_disparo.value
        return datos

@dataclass
class ResultadoEjecucionTarea:
    ok: bool
    tarea_id: str
    ejecutada: bool
    herramienta: str | None = None
    resultado: dict[str, Any] | None = None
    requiere_confirmacion: bool = False
    error: str | None = None
