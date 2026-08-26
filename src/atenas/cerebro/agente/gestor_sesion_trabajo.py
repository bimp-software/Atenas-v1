from __future__ import annotations

import json
import uuid

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class EstadoSesionTrabajo(str, Enum):
    NUEVA = "nueva"
    ACTIVA = "activa"
    PAUSADA = "pausada"
    BLOQUEADA = "bloqueada"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


@dataclass
class SesionTrabajo:
    id: str
    nombre: str
    objetivo_superior: str

    estado: EstadoSesionTrabajo = EstadoSesionTrabajo.NUEVA

    proyecto_id: str | None = None
    tarea_actual_id: str | None = None

    tareas_relacionadas: list[str] = field(default_factory=list)
    tareas_completadas: list[str] = field(default_factory=list)

    resultado_esperado: str | None = None

    bloqueos: list[str] = field(default_factory=list)

    creada_en: str = ""
    actualizada_en: str = ""

    progreso: float = 0.0

    metadata: dict[str, Any] = field(default_factory=dict)


class GestorSesionTrabajo:
    """
    Gestor persistente de sesiones de trabajo de ATENAS.

    Una sesión representa un objetivo superior que puede contener:
    - un proyecto;
    - varias tareas;
    - bloqueos;
    - progreso;
    - un resultado esperado.

    No reemplaza ContextoOperativo:
    - ContextoOperativo = "qué sabe ATENAS ahora";
    - SesionTrabajo = "qué está intentando lograr ATENAS ahora".
    """

    def __init__(
        self,
        ruta: str | Path = "data/agente/sesiones_trabajo/sesiones.json",
    ):
        self.ruta = Path(ruta).expanduser().resolve()
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

        if not self.ruta.exists():
            self.ruta.write_text("[]", encoding="utf-8")

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _ahora() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _unicos(valores: list[str]) -> list[str]:
        salida = []
        vistos = set()

        for valor in valores:
            texto = str(valor).strip()
            if not texto or texto in vistos:
                continue

            vistos.add(texto)
            salida.append(texto)

        return salida

    # =========================================================
    # SERIALIZACIÓN
    # =========================================================

    @classmethod
    def _a_dict(cls, sesion: SesionTrabajo) -> dict[str, Any]:
        return {
            "id": sesion.id,
            "nombre": sesion.nombre,
            "objetivo_superior": sesion.objetivo_superior,
            "estado": sesion.estado.value,
            "proyecto_id": sesion.proyecto_id,
            "tarea_actual_id": sesion.tarea_actual_id,
            "tareas_relacionadas": cls._unicos(sesion.tareas_relacionadas),
            "tareas_completadas": cls._unicos(sesion.tareas_completadas),
            "resultado_esperado": sesion.resultado_esperado,
            "bloqueos": cls._unicos(sesion.bloqueos),
            "creada_en": sesion.creada_en,
            "actualizada_en": sesion.actualizada_en,
            "progreso": round(max(0.0, min(100.0, float(sesion.progreso))), 2),
            "metadata": sesion.metadata,
        }

    @staticmethod
    def _desde_dict(datos: dict[str, Any]) -> SesionTrabajo:
        return SesionTrabajo(
            id=str(datos["id"]),
            nombre=str(datos.get("nombre", "Sesión de trabajo")),
            objetivo_superior=str(datos.get("objetivo_superior", "")),
            estado=EstadoSesionTrabajo(datos.get("estado", "nueva")),
            proyecto_id=(
                str(datos["proyecto_id"])
                if datos.get("proyecto_id")
                else None
            ),
            tarea_actual_id=(
                str(datos["tarea_actual_id"])
                if datos.get("tarea_actual_id")
                else None
            ),
            tareas_relacionadas=list(datos.get("tareas_relacionadas", []) or []),
            tareas_completadas=list(datos.get("tareas_completadas", []) or []),
            resultado_esperado=(
                str(datos["resultado_esperado"])
                if datos.get("resultado_esperado")
                else None
            ),
            bloqueos=list(datos.get("bloqueos", []) or []),
            creada_en=str(datos.get("creada_en", "")),
            actualizada_en=str(datos.get("actualizada_en", "")),
            progreso=float(datos.get("progreso", 0.0) or 0.0),
            metadata=datos.get("metadata", {}) or {},
        )

    # =========================================================
    # PERSISTENCIA
    # =========================================================

    def listar(self) -> list[SesionTrabajo]:
        try:
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
        except Exception:
            datos = []

        if not isinstance(datos, list):
            datos = []

        salida = []

        for item in datos:
            if not isinstance(item, dict):
                continue

            try:
                salida.append(self._desde_dict(item))
            except Exception:
                continue

        return salida

    def guardar_todas(self, sesiones: list[SesionTrabajo]) -> None:
        temporal = self.ruta.with_suffix(".tmp")

        temporal.write_text(
            json.dumps(
                [self._a_dict(s) for s in sesiones],
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        temporal.replace(self.ruta)

    def guardar(self, sesion: SesionTrabajo) -> None:
        sesion.actualizada_en = self._ahora()

        sesiones = [
            actual
            for actual in self.listar()
            if actual.id != sesion.id
        ]

        sesiones.append(sesion)
        self.guardar_todas(sesiones)

    def obtener(self, sesion_id: str) -> SesionTrabajo | None:
        for sesion in self.listar():
            if sesion.id == sesion_id:
                return sesion
        return None

    # =========================================================
    # SESIÓN ACTUAL
    # =========================================================

    def activa(self) -> SesionTrabajo | None:
        candidatas = [
            sesion
            for sesion in self.listar()
            if sesion.estado in {
                EstadoSesionTrabajo.ACTIVA,
                EstadoSesionTrabajo.PAUSADA,
                EstadoSesionTrabajo.BLOQUEADA,
            }
        ]

        if not candidatas:
            return None

        candidatas.sort(
            key=lambda s: s.actualizada_en or s.creada_en,
            reverse=True,
        )

        return candidatas[0]

    # =========================================================
    # CREAR / CAMBIAR ESTADO
    # =========================================================

    def crear(
        self,
        nombre: str,
        objetivo_superior: str,
        proyecto_id: str | None = None,
        resultado_esperado: str | None = None,
        metadata: dict[str, Any] | None = None,
        activar: bool = True,
    ) -> SesionTrabajo:
        ahora = self._ahora()

        sesion = SesionTrabajo(
            id=str(uuid.uuid4()),
            nombre=(nombre or "Sesión de trabajo").strip(),
            objetivo_superior=(objetivo_superior or "").strip(),
            estado=(
                EstadoSesionTrabajo.ACTIVA
                if activar
                else EstadoSesionTrabajo.NUEVA
            ),
            proyecto_id=proyecto_id,
            resultado_esperado=resultado_esperado,
            creada_en=ahora,
            actualizada_en=ahora,
            metadata=metadata or {},
        )

        if activar:
            actual = self.activa()
            if (
                actual is not None
                and actual.estado == EstadoSesionTrabajo.ACTIVA
            ):
                actual.estado = EstadoSesionTrabajo.PAUSADA
                self.guardar(actual)

        self.guardar(sesion)
        return sesion

    def pausar(self, sesion_id: str) -> SesionTrabajo | None:
        sesion = self.obtener(sesion_id)
        if sesion is None:
            return None

        sesion.estado = EstadoSesionTrabajo.PAUSADA
        self.guardar(sesion)
        return sesion

    def reanudar(self, sesion_id: str) -> SesionTrabajo | None:
        sesion = self.obtener(sesion_id)
        if sesion is None:
            return None

        actual = self.activa()
        if (
            actual is not None
            and actual.id != sesion.id
            and actual.estado == EstadoSesionTrabajo.ACTIVA
        ):
            actual.estado = EstadoSesionTrabajo.PAUSADA
            self.guardar(actual)

        sesion.estado = EstadoSesionTrabajo.ACTIVA
        self.guardar(sesion)
        return sesion

    def completar(
        self,
        sesion_id: str,
        resultado: str | None = None,
    ) -> SesionTrabajo | None:
        sesion = self.obtener(sesion_id)
        if sesion is None:
            return None

        sesion.estado = EstadoSesionTrabajo.COMPLETADA
        sesion.progreso = 100.0

        if resultado:
            sesion.metadata["resultado_final"] = str(resultado)

        self.guardar(sesion)
        return sesion

    def bloquear(
        self,
        sesion_id: str,
        motivo: str,
    ) -> SesionTrabajo | None:
        sesion = self.obtener(sesion_id)
        if sesion is None:
            return None

        sesion.estado = EstadoSesionTrabajo.BLOQUEADA
        sesion.bloqueos.append(str(motivo))
        self.guardar(sesion)
        return sesion

    # =========================================================
    # TAREAS
    # =========================================================

    def asociar_tarea(
        self,
        sesion_id: str,
        tarea_id: str,
        hacer_actual: bool = True,
    ) -> SesionTrabajo | None:
        sesion = self.obtener(sesion_id)
        if sesion is None:
            return None

        sesion.tareas_relacionadas.append(str(tarea_id))

        if hacer_actual:
            sesion.tarea_actual_id = str(tarea_id)

        self.guardar(sesion)
        return sesion

    def marcar_tarea_completada(
        self,
        sesion_id: str,
        tarea_id: str,
    ) -> SesionTrabajo | None:
        sesion = self.obtener(sesion_id)
        if sesion is None:
            return None

        tarea_id = str(tarea_id)

        sesion.tareas_relacionadas.append(tarea_id)
        sesion.tareas_completadas.append(tarea_id)

        if sesion.tarea_actual_id == tarea_id:
            sesion.tarea_actual_id = None

        total = len(self._unicos(sesion.tareas_relacionadas))
        hechas = len(self._unicos(sesion.tareas_completadas))

        if total > 0:
            sesion.progreso = round((hechas / total) * 100.0, 2)

        self.guardar(sesion)
        return sesion

    # =========================================================
    # BLOQUEOS
    # =========================================================

    def limpiar_bloqueos(
        self,
        sesion_id: str,
    ) -> SesionTrabajo | None:
        sesion = self.obtener(sesion_id)
        if sesion is None:
            return None

        sesion.bloqueos = []

        if sesion.estado == EstadoSesionTrabajo.BLOQUEADA:
            sesion.estado = EstadoSesionTrabajo.ACTIVA

        self.guardar(sesion)
        return sesion

    # =========================================================
    # RESUMEN
    # =========================================================

    def resumen_activa(self) -> dict[str, Any]:
        sesion = self.activa()

        if sesion is None:
            return {
                "activa": False,
                "mensaje": "No existe una sesión de trabajo activa.",
            }

        return {
            "activa": True,
            "id": sesion.id,
            "nombre": sesion.nombre,
            "objetivo_superior": sesion.objetivo_superior,
            "estado": sesion.estado.value,
            "proyecto_id": sesion.proyecto_id,
            "tarea_actual_id": sesion.tarea_actual_id,
            "tareas_relacionadas": len(
                self._unicos(sesion.tareas_relacionadas)
            ),
            "tareas_completadas": len(
                self._unicos(sesion.tareas_completadas)
            ),
            "progreso": sesion.progreso,
            "resultado_esperado": sesion.resultado_esperado,
            "bloqueos": list(sesion.bloqueos),
            "actualizada_en": sesion.actualizada_en,
        }