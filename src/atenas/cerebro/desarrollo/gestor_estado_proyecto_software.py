from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from .planificador_sistema_software import (
    EstadoTarea,
    PlanSistemaSoftware,
    PlanificadorSistemaSoftware,
)


class EstadoProyectoSoftware(str, Enum):
    NUEVO = "nuevo"
    ANALIZANDO = "analizando"
    PLANIFICADO = "planificado"
    PREPARANDO_ENTORNO = "preparando_entorno"
    EN_DESARROLLO = "en_desarrollo"
    BLOQUEADO = "bloqueado"
    VALIDANDO = "validando"
    DOCUMENTANDO = "documentando"
    LISTO_ENTREGA = "listo_entrega"
    COMPLETADO = "completado"
    FALLIDO = "fallido"
    PAUSADO = "pausado"


@dataclass
class ResumenTareasProyecto:
    total: int = 0
    pendientes: int = 0
    bloqueadas: int = 0
    en_progreso: int = 0
    completadas: int = 0
    fallidas: int = 0
    canceladas: int = 0


@dataclass
class BloqueoProyecto:
    tipo: str
    descripcion: str
    requiere_confirmacion: bool = False
    creado_en: str = ""


@dataclass
class EntregableProyecto:
    nombre: str
    ruta: str
    tipo: str
    generado: bool = False
    version: str | None = None


@dataclass
class EventoProyecto:
    timestamp: str
    tipo: str
    mensaje: str
    datos: dict[str, Any] = field(default_factory=dict)


@dataclass
class EstadoIntegralProyecto:
    proyecto_id: str
    nombre: str
    carpeta: str

    estado: EstadoProyectoSoftware

    progreso: float = 0.0

    tarea_actual_id: str | None = None
    tarea_actual_titulo: str | None = None

    fase_actual: str | None = None
    epica_actual: str | None = None

    tareas: ResumenTareasProyecto = field(
        default_factory=ResumenTareasProyecto
    )

    bloqueos: list[BloqueoProyecto] = field(
        default_factory=list
    )

    entregables: list[EntregableProyecto] = field(
        default_factory=list
    )

    tecnologias: dict[str, Any] = field(
        default_factory=dict
    )

    base_datos: dict[str, Any] | None = None

    entorno: dict[str, Any] = field(
        default_factory=dict
    )

    ultima_validacion_ok: bool | None = None

    version: str = "0.1.0"

    creado_en: str = ""
    actualizado_en: str = ""

    eventos: list[EventoProyecto] = field(
        default_factory=list
    )


class GestorEstadoProyectoSoftware:
    """
    Estado integral y persistente de un proyecto desarrollado por ATENAS.

    Este módulo sirve como fuente de verdad para:
    - el futuro Agente;
    - la futura interfaz web;
    - reanudación después de reinicios;
    - seguimiento de progreso;
    - bloqueos;
    - entregables;
    - historial.

    Archivo persistente:
        <proyecto>/.atenas/estado_proyecto.json
    """

    MAX_EVENTOS = 500

    def __init__(
        self,
        carpeta_proyecto: str | Path,
    ):
        self.carpeta = Path(
            carpeta_proyecto
        ).resolve()

        self.carpeta.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.carpeta_atenas = (
            self.carpeta
            / ".atenas"
        )

        self.carpeta_atenas.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.archivo_estado = (
            self.carpeta_atenas
            / "estado_proyecto.json"
        )

    # =========================================================
    # TIEMPO
    # =========================================================

    @staticmethod
    def _ahora() -> str:

        return (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

    # =========================================================
    # SERIALIZACIÓN
    # =========================================================

    @staticmethod
    def _estado_desde_dict(
        datos: dict,
    ) -> EstadoIntegralProyecto:

        tareas_raw = (
            datos.get(
                "tareas",
                {}
            )
            or {}
        )

        tareas = ResumenTareasProyecto(
            total=int(
                tareas_raw.get(
                    "total",
                    0,
                )
            ),
            pendientes=int(
                tareas_raw.get(
                    "pendientes",
                    0,
                )
            ),
            bloqueadas=int(
                tareas_raw.get(
                    "bloqueadas",
                    0,
                )
            ),
            en_progreso=int(
                tareas_raw.get(
                    "en_progreso",
                    0,
                )
            ),
            completadas=int(
                tareas_raw.get(
                    "completadas",
                    0,
                )
            ),
            fallidas=int(
                tareas_raw.get(
                    "fallidas",
                    0,
                )
            ),
            canceladas=int(
                tareas_raw.get(
                    "canceladas",
                    0,
                )
            ),
        )

        bloqueos = [
            BloqueoProyecto(
                tipo=str(
                    item.get(
                        "tipo",
                        "general",
                    )
                ),
                descripcion=str(
                    item.get(
                        "descripcion",
                        "",
                    )
                ),
                requiere_confirmacion=bool(
                    item.get(
                        "requiere_confirmacion",
                        False,
                    )
                ),
                creado_en=str(
                    item.get(
                        "creado_en",
                        "",
                    )
                ),
            )
            for item in (
                datos.get(
                    "bloqueos",
                    []
                )
                or []
            )
            if isinstance(
                item,
                dict,
            )
        ]

        entregables = [
            EntregableProyecto(
                nombre=str(
                    item.get(
                        "nombre",
                        "",
                    )
                ),
                ruta=str(
                    item.get(
                        "ruta",
                        "",
                    )
                ),
                tipo=str(
                    item.get(
                        "tipo",
                        "archivo",
                    )
                ),
                generado=bool(
                    item.get(
                        "generado",
                        False,
                    )
                ),
                version=(
                    str(
                        item[
                            "version"
                        ]
                    )
                    if item.get(
                        "version"
                    )
                    else None
                ),
            )
            for item in (
                datos.get(
                    "entregables",
                    []
                )
                or []
            )
            if isinstance(
                item,
                dict,
            )
        ]

        eventos = [
            EventoProyecto(
                timestamp=str(
                    item.get(
                        "timestamp",
                        "",
                    )
                ),
                tipo=str(
                    item.get(
                        "tipo",
                        "evento",
                    )
                ),
                mensaje=str(
                    item.get(
                        "mensaje",
                        "",
                    )
                ),
                datos=(
                    item.get(
                        "datos",
                        {}
                    )
                    or {}
                ),
            )
            for item in (
                datos.get(
                    "eventos",
                    []
                )
                or []
            )
            if isinstance(
                item,
                dict,
            )
        ]

        try:

            estado = EstadoProyectoSoftware(
                str(
                    datos.get(
                        "estado",
                        "nuevo",
                    )
                )
            )

        except ValueError:

            estado = (
                EstadoProyectoSoftware.NUEVO
            )

        return EstadoIntegralProyecto(
            proyecto_id=str(
                datos.get(
                    "proyecto_id",
                    "",
                )
            ),
            nombre=str(
                datos.get(
                    "nombre",
                    "Proyecto",
                )
            ),
            carpeta=str(
                datos.get(
                    "carpeta",
                    "",
                )
            ),
            estado=estado,
            progreso=float(
                datos.get(
                    "progreso",
                    0.0,
                )
                or 0.0
            ),
            tarea_actual_id=(
                str(
                    datos[
                        "tarea_actual_id"
                    ]
                )
                if datos.get(
                    "tarea_actual_id"
                )
                else None
            ),
            tarea_actual_titulo=(
                str(
                    datos[
                        "tarea_actual_titulo"
                    ]
                )
                if datos.get(
                    "tarea_actual_titulo"
                )
                else None
            ),
            fase_actual=(
                str(
                    datos[
                        "fase_actual"
                    ]
                )
                if datos.get(
                    "fase_actual"
                )
                else None
            ),
            epica_actual=(
                str(
                    datos[
                        "epica_actual"
                    ]
                )
                if datos.get(
                    "epica_actual"
                )
                else None
            ),
            tareas=tareas,
            bloqueos=bloqueos,
            entregables=entregables,
            tecnologias=(
                datos.get(
                    "tecnologias",
                    {}
                )
                or {}
            ),
            base_datos=(
                datos.get(
                    "base_datos"
                )
            ),
            entorno=(
                datos.get(
                    "entorno",
                    {}
                )
                or {}
            ),
            ultima_validacion_ok=(
                datos.get(
                    "ultima_validacion_ok"
                )
            ),
            version=str(
                datos.get(
                    "version",
                    "0.1.0",
                )
            ),
            creado_en=str(
                datos.get(
                    "creado_en",
                    "",
                )
            ),
            actualizado_en=str(
                datos.get(
                    "actualizado_en",
                    "",
                )
            ),
            eventos=eventos,
        )

    # =========================================================
    # CREAR / CARGAR
    # =========================================================

    def crear(
        self,
        proyecto_id: str,
        nombre: str,
        version: str = "0.1.0",
    ) -> EstadoIntegralProyecto:

        ahora = self._ahora()

        estado = EstadoIntegralProyecto(
            proyecto_id=proyecto_id,
            nombre=nombre,
            carpeta=str(
                self.carpeta
            ),
            estado=(
                EstadoProyectoSoftware.NUEVO
            ),
            version=version,
            creado_en=ahora,
            actualizado_en=ahora,
            eventos=[
                EventoProyecto(
                    timestamp=ahora,
                    tipo="proyecto_creado",
                    mensaje=(
                        "ATENAS creó el estado "
                        "integral del proyecto."
                    ),
                )
            ],
        )

        self.guardar(
            estado
        )

        return estado

    def cargar(
        self,
    ) -> EstadoIntegralProyecto | None:

        if not self.archivo_estado.exists():

            return None

        try:

            datos = json.loads(
                self.archivo_estado.read_text(
                    encoding="utf-8"
                )
            )

            return (
                self._estado_desde_dict(
                    datos
                )
            )

        except Exception:

            return None

    def cargar_o_crear(
        self,
        proyecto_id: str,
        nombre: str,
        version: str = "0.1.0",
    ) -> EstadoIntegralProyecto:

        existente = self.cargar()

        if existente is not None:
            return existente

        return self.crear(
            proyecto_id=proyecto_id,
            nombre=nombre,
            version=version,
        )

    # =========================================================
    # GUARDAR
    # =========================================================

    def guardar(
        self,
        estado: EstadoIntegralProyecto,
    ) -> None:

        estado.actualizado_en = (
            self._ahora()
        )

        estado.eventos = (
            estado.eventos[
                -self.MAX_EVENTOS:
            ]
        )

        self.archivo_estado.write_text(
            json.dumps(
                asdict(
                    estado
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    # =========================================================
    # EVENTOS
    # =========================================================

    def registrar_evento(
        self,
        estado: EstadoIntegralProyecto,
        tipo: str,
        mensaje: str,
        datos: dict[str, Any] | None = None,
    ) -> None:

        estado.eventos.append(
            EventoProyecto(
                timestamp=self._ahora(),
                tipo=tipo,
                mensaje=mensaje,
                datos=datos or {},
            )
        )

        self.guardar(
            estado
        )

    # =========================================================
    # SINCRONIZAR PLAN
    # =========================================================

    def sincronizar_plan(
        self,
        estado: EstadoIntegralProyecto,
        plan: PlanSistemaSoftware,
    ) -> EstadoIntegralProyecto:

        tareas = (
            PlanificadorSistemaSoftware
            .todas_las_tareas(
                plan
            )
        )

        resumen = (
            ResumenTareasProyecto()
        )

        resumen.total = len(
            tareas
        )

        for tarea in tareas:

            if (
                tarea.estado
                == EstadoTarea.PENDIENTE
            ):
                resumen.pendientes += 1

            elif (
                tarea.estado
                == EstadoTarea.BLOQUEADA
            ):
                resumen.bloqueadas += 1

            elif (
                tarea.estado
                == EstadoTarea.EN_PROGRESO
            ):
                resumen.en_progreso += 1

            elif (
                tarea.estado
                == EstadoTarea.COMPLETADA
            ):
                resumen.completadas += 1

            elif (
                tarea.estado
                == EstadoTarea.FALLIDA
            ):
                resumen.fallidas += 1

            elif (
                tarea.estado
                == EstadoTarea.CANCELADA
            ):
                resumen.canceladas += 1

        estado.tareas = resumen

        if resumen.total > 0:

            estado.progreso = round(
                (
                    resumen.completadas
                    / resumen.total
                )
                * 100.0,
                2,
            )

        else:

            estado.progreso = 0.0

        # Encontrar tarea actualmente activa.
        activa = next(
            (
                tarea
                for tarea
                in tareas
                if (
                    tarea.estado
                    == EstadoTarea.EN_PROGRESO
                )
            ),
            None,
        )

        if activa is not None:

            estado.tarea_actual_id = (
                activa.id
            )

            estado.tarea_actual_titulo = (
                activa.titulo
            )

            estado.estado = (
                EstadoProyectoSoftware
                .EN_DESARROLLO
            )

        else:

            siguiente = (
                PlanificadorSistemaSoftware
                .siguiente_tarea(
                    plan
                )
            )

            if siguiente is not None:

                estado.tarea_actual_id = (
                    siguiente.id
                )

                estado.tarea_actual_titulo = (
                    siguiente.titulo
                )

            else:

                estado.tarea_actual_id = None
                estado.tarea_actual_titulo = None

        # Resolver fase y épica asociadas a tarea actual.
        estado.fase_actual = None
        estado.epica_actual = None

        if estado.tarea_actual_id:

            for fase in plan.fases:

                encontrado = False

                for epica in fase.epicas:

                    if any(
                        tarea.id
                        == estado.tarea_actual_id
                        for tarea
                        in epica.tareas
                    ):

                        estado.fase_actual = (
                            fase.nombre
                        )

                        estado.epica_actual = (
                            epica.nombre
                        )

                        encontrado = True
                        break

                if encontrado:
                    break

        if (
            resumen.total > 0
            and resumen.completadas
            == resumen.total
        ):

            estado.estado = (
                EstadoProyectoSoftware
                .COMPLETADO
            )

            estado.progreso = 100.0

            estado.tarea_actual_id = None
            estado.tarea_actual_titulo = None

        elif resumen.fallidas > 0:

            estado.estado = (
                EstadoProyectoSoftware
                .BLOQUEADO
            )

        self.guardar(
            estado
        )

        return estado

    # =========================================================
    # BLOQUEOS
    # =========================================================

    def agregar_bloqueo(
        self,
        estado: EstadoIntegralProyecto,
        tipo: str,
        descripcion: str,
        requiere_confirmacion: bool = False,
    ) -> None:

        estado.bloqueos.append(
            BloqueoProyecto(
                tipo=tipo,
                descripcion=descripcion,
                requiere_confirmacion=(
                    requiere_confirmacion
                ),
                creado_en=self._ahora(),
            )
        )

        estado.estado = (
            EstadoProyectoSoftware
            .BLOQUEADO
        )

        self.registrar_evento(
            estado=estado,
            tipo="bloqueo_agregado",
            mensaje=descripcion,
            datos={
                "tipo":
                    tipo,

                "requiere_confirmacion":
                    requiere_confirmacion,
            },
        )

    def limpiar_bloqueos(
        self,
        estado: EstadoIntegralProyecto,
        tipo: str | None = None,
    ) -> None:

        if tipo is None:

            estado.bloqueos = []

        else:

            estado.bloqueos = [
                bloqueo
                for bloqueo
                in estado.bloqueos
                if bloqueo.tipo != tipo
            ]

        if not estado.bloqueos:

            if (
                estado.estado
                == EstadoProyectoSoftware.BLOQUEADO
            ):

                estado.estado = (
                    EstadoProyectoSoftware
                    .EN_DESARROLLO
                )

        self.guardar(
            estado
        )

    # =========================================================
    # ENTREGABLES
    # =========================================================

    def registrar_entregable(
        self,
        estado: EstadoIntegralProyecto,
        nombre: str,
        ruta: str | Path,
        tipo: str,
        version: str | None = None,
    ) -> None:

        ruta_resuelta = str(
            Path(
                ruta
            ).resolve()
        )

        existente = next(
            (
                item
                for item
                in estado.entregables
                if (
                    item.ruta
                    == ruta_resuelta
                )
            ),
            None,
        )

        if existente is not None:

            existente.nombre = nombre
            existente.tipo = tipo
            existente.version = version
            existente.generado = Path(
                ruta_resuelta
            ).exists()

        else:

            estado.entregables.append(
                EntregableProyecto(
                    nombre=nombre,
                    ruta=ruta_resuelta,
                    tipo=tipo,
                    generado=Path(
                        ruta_resuelta
                    ).exists(),
                    version=version,
                )
            )

        self.registrar_evento(
            estado=estado,
            tipo="entregable_registrado",
            mensaje=(
                f"Entregable registrado: {nombre}"
            ),
            datos={
                "ruta":
                    ruta_resuelta,

                "tipo":
                    tipo,

                "version":
                    version,
            },
        )

    # =========================================================
    # TECNOLOGÍAS / BD / ENTORNO
    # =========================================================

    def actualizar_tecnologias(
        self,
        estado: EstadoIntegralProyecto,
        tecnologias: dict[str, Any],
    ) -> None:

        estado.tecnologias = (
            tecnologias
        )

        self.guardar(
            estado
        )

    def actualizar_base_datos(
        self,
        estado: EstadoIntegralProyecto,
        datos: dict[str, Any] | None,
    ) -> None:

        estado.base_datos = datos

        self.guardar(
            estado
        )

    def actualizar_entorno(
        self,
        estado: EstadoIntegralProyecto,
        entorno: dict[str, Any],
    ) -> None:

        estado.entorno = entorno

        self.guardar(
            estado
        )

    # =========================================================
    # VALIDACIÓN / VERSIONADO
    # =========================================================

    def registrar_validacion(
        self,
        estado: EstadoIntegralProyecto,
        ok: bool,
        resumen: str,
    ) -> None:

        estado.ultima_validacion_ok = bool(
            ok
        )

        self.registrar_evento(
            estado=estado,
            tipo=(
                "validacion_correcta"
                if ok
                else "validacion_fallida"
            ),
            mensaje=resumen,
        )

    def cambiar_version(
        self,
        estado: EstadoIntegralProyecto,
        version: str,
    ) -> None:

        anterior = (
            estado.version
        )

        estado.version = (
            version
        )

        self.registrar_evento(
            estado=estado,
            tipo="version_actualizada",
            mensaje=(
                f"Versión {anterior} → {version}"
            ),
        )

    # =========================================================
    # RESUMEN PARA AGENTE / WEB
    # =========================================================

    @staticmethod
    def resumen_para_agente(
        estado: EstadoIntegralProyecto,
    ) -> dict[str, Any]:

        return {
            "proyecto_id":
                estado.proyecto_id,

            "nombre":
                estado.nombre,

            "estado":
                estado.estado.value,

            "progreso":
                estado.progreso,

            "tarea_actual":
                estado.tarea_actual_titulo,

            "fase_actual":
                estado.fase_actual,

            "epica_actual":
                estado.epica_actual,

            "tareas":
                asdict(
                    estado.tareas
                ),

            "bloqueos": [
                asdict(
                    bloqueo
                )
                for bloqueo
                in estado.bloqueos
            ],

            "entregables": [
                asdict(
                    entregable
                )
                for entregable
                in estado.entregables
            ],

            "ultima_validacion_ok":
                estado.ultima_validacion_ok,

            "version":
                estado.version,

            "actualizado_en":
                estado.actualizado_en,
        }