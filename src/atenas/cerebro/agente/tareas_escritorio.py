from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EstadoTareaEscritorio(str, Enum):
    NUEVA = "nueva"
    EN_PROGRESO = "en_progreso"
    PAUSADA = "pausada"
    REQUIERE_CONFIRMACION = "requiere_confirmacion"
    COMPLETADA = "completada"
    FALLIDA = "fallida"


class EstadoPasoEscritorio(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    REQUIERE_CONFIRMACION = "requiere_confirmacion"
    FALLIDO = "fallido"
    OMITIDO = "omitido"


class TipoPasoEscritorio(str, Enum):
    CREAR_CARPETA = "crear_carpeta"
    ESCRIBIR_ARCHIVO = "escribir_archivo"
    ABRIR_RUTA = "abrir_ruta"
    ABRIR_APLICACION = "abrir_aplicacion"
    ESPERAR_VENTANA = "esperar_ventana"
    ACTIVAR_VENTANA = "activar_ventana"
    OBSERVAR = "observar"
    INTERPRETAR_ESCENA = "interpretar_escena"
    ACCION_GUI = "accion_gui"
    VERIFICAR_ARCHIVO = "verificar_archivo"
    VERIFICAR_CARPETA = "verificar_carpeta"
    VERIFICAR_VENTANA = "verificar_ventana"


@dataclass
class PasoTareaEscritorio:
    id: str
    tipo: TipoPasoEscritorio
    descripcion: str
    argumentos: dict[str, Any] = field(default_factory=dict)
    estado: EstadoPasoEscritorio = EstadoPasoEscritorio.PENDIENTE
    intentos: int = 0
    max_intentos: int = 2
    requiere_confirmacion: bool = False
    resultado: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class TareaEscritorio:
    id: str
    nombre: str
    descripcion: str
    pasos: list[PasoTareaEscritorio] = field(default_factory=list)
    estado: EstadoTareaEscritorio = EstadoTareaEscritorio.NUEVA
    prioridad: float = 0.70
    creada_por: str = "agente"
    proyecto_id: str | None = None
    paso_actual: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    ultimo_error: str | None = None

    @property
    def completada(self) -> bool:
        return self.estado == EstadoTareaEscritorio.COMPLETADA

    @property
    def progreso(self) -> float:
        if not self.pasos:
            return 100.0
        completados = sum(
            1 for paso in self.pasos
            if paso.estado in {
                EstadoPasoEscritorio.COMPLETADO,
                EstadoPasoEscritorio.OMITIDO,
            }
        )
        return round((completados / len(self.pasos)) * 100.0, 2)