from __future__ import annotations

import json
import re
import uuid

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from src.atenas.cerebro.desarrollo.orquestador_desarrollo import (
    OrquestadorDesarrollo,
    ResultadoCicloDesarrollo,
    ResultadoInicioDesarrollo,
)

from src.atenas.cerebro.desarrollo.gestor_estado_proyecto_software import (
    GestorEstadoProyectoSoftware,
)

from .restaurador_contexto_desarrollo import (
    RestauradorContextoDesarrollo,
)


class AccionDesarrollo(str, Enum):
    CREAR_PROYECTO = "crear_proyecto"
    CONTINUAR_PROYECTO = "continuar_proyecto"
    CONSULTAR_ESTADO = "consultar_estado"
    LISTAR_PROYECTOS = "listar_proyectos"
    DESCONOCIDA = "desconocida"


@dataclass
class ProyectoSoftwareAgente:
    id: str
    nombre: str
    carpeta: str

    descripcion: str = ""

    estado: str = "nuevo"
    progreso: float = 0.0

    prioridad: float = 0.65
    urgencia: float = 0.0

    creado_por: str = "agente"

    ultimo_error: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ResultadoCapacidadDesarrollo:
    ok: bool
    accion: AccionDesarrollo

    proyecto_id: str | None = None
    carpeta: str | None = None

    estado: str | None = None
    progreso: float | None = None

    mensaje: str = ""

    requiere_confirmacion: bool = False

    dependencias_pendientes: list[str] = field(
        default_factory=list
    )

    datos: dict[str, Any] = field(
        default_factory=dict
    )

    error: str | None = None


class CapacidadDesarrollo:
    """
    Adaptador persistente entre AgenteAtenas y desarrollo/.

    V2 añade prioridad y urgencia por proyecto para que el futuro
    director de iniciativa pueda comparar varios proyectos.
    """

    def __init__(
        self,
        llm: Any,
        raiz_datos: str | Path = "data/agente/desarrollo",
        raiz_proyectos: str | Path | None = None,
    ):
        self.llm = llm

        self.raiz_datos = Path(
            raiz_datos
        ).resolve()

        self.raiz_datos.mkdir(
            parents=True,
            exist_ok=True,
        )

        if raiz_proyectos is None:

            self.raiz_proyectos = (
                Path.home()
                / "Documents"
                / "Proyectos"
                / "ATENAS"
            ).resolve()

        else:

            self.raiz_proyectos = Path(
                raiz_proyectos
            ).resolve()

        self.raiz_proyectos.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.raiz_planes = (
            self.raiz_datos
            / "planes"
        )

        self.raiz_planes.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.archivo_registro = (
            self.raiz_datos
            / "proyectos.json"
        )

        self.orquestador = (
            OrquestadorDesarrollo(
                llm=llm,
                raiz_planes=(
                    self.raiz_planes
                ),
            )
        )

        self.restaurador = (
            RestauradorContextoDesarrollo()
        )

        self._proyectos: dict[
            str,
            ProyectoSoftwareAgente
        ] = {}

        self._contextos: dict[
            str,
            ResultadoInicioDesarrollo
        ] = {}

        self._cargar_registro()
        self._restaurar_contextos()

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _clamp(
        valor: float,
    ) -> float:

        return max(
            0.0,
            min(
                1.0,
                float(
                    valor
                ),
            ),
        )

    @staticmethod
    def _nombre_seguro(
        texto: str,
    ) -> str:

        texto = (
            texto
            or "Proyecto"
        ).strip()

        texto = re.sub(
            r'[<>:"/\\|?*]+',
            "_",
            texto,
        )

        texto = re.sub(
            r"\s+",
            " ",
            texto,
        ).strip(" .")

        if not texto:
            texto = "Proyecto"

        return texto[:100]

    @staticmethod
    def _serializar_proyecto(
        proyecto: ProyectoSoftwareAgente,
    ) -> dict[str, Any]:

        return {
            "id":
                proyecto.id,

            "nombre":
                proyecto.nombre,

            "carpeta":
                proyecto.carpeta,

            "descripcion":
                proyecto.descripcion,

            "estado":
                proyecto.estado,

            "progreso":
                proyecto.progreso,

            "prioridad":
                proyecto.prioridad,

            "urgencia":
                proyecto.urgencia,

            "creado_por":
                proyecto.creado_por,

            "ultimo_error":
                proyecto.ultimo_error,

            "metadata":
                proyecto.metadata,
        }

    # =========================================================
    # REGISTRO
    # =========================================================

    def _cargar_registro(
        self,
    ) -> None:

        if not self.archivo_registro.exists():

            self._guardar_registro()
            return

        try:

            datos = json.loads(
                self.archivo_registro.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:

            datos = []

        if not isinstance(
            datos,
            list,
        ):

            datos = []

        for item in datos:

            if not isinstance(
                item,
                dict,
            ):
                continue

            proyecto_id = str(
                item.get(
                    "id",
                    "",
                )
            ).strip()

            carpeta = str(
                item.get(
                    "carpeta",
                    "",
                )
            ).strip()

            if not proyecto_id or not carpeta:
                continue

            self._proyectos[
                proyecto_id
            ] = ProyectoSoftwareAgente(
                id=proyecto_id,
                nombre=str(
                    item.get(
                        "nombre",
                        "Proyecto",
                    )
                ),
                carpeta=carpeta,
                descripcion=str(
                    item.get(
                        "descripcion",
                        "",
                    )
                ),
                estado=str(
                    item.get(
                        "estado",
                        "nuevo",
                    )
                ),
                progreso=float(
                    item.get(
                        "progreso",
                        0.0,
                    )
                    or 0.0
                ),
                prioridad=self._clamp(
                    item.get(
                        "prioridad",
                        0.65,
                    )
                    or 0.65
                ),
                urgencia=self._clamp(
                    item.get(
                        "urgencia",
                        0.0,
                    )
                    or 0.0
                ),
                creado_por=str(
                    item.get(
                        "creado_por",
                        "agente",
                    )
                ),
                ultimo_error=(
                    str(
                        item[
                            "ultimo_error"
                        ]
                    )
                    if item.get(
                        "ultimo_error"
                    )
                    else None
                ),
                metadata=(
                    item.get(
                        "metadata",
                        {},
                    )
                    or {}
                ),
            )

        self._refrescar_estados_desde_disco()

    def _guardar_registro(
        self,
    ) -> None:

        self.archivo_registro.write_text(
            json.dumps(
                [
                    self._serializar_proyecto(
                        proyecto
                    )
                    for proyecto
                    in self._proyectos.values()
                ],
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    def _restaurar_contextos(
        self,
    ) -> None:

        for proyecto_id, proyecto in (
            self._proyectos.items()
        ):

            carpeta = Path(
                proyecto.carpeta
            )

            if not carpeta.exists():

                proyecto.ultimo_error = (
                    "carpeta_proyecto_no_existe"
                )

                continue

            resultado = (
                self.restaurador
                .restaurar(
                    carpeta_proyecto=(
                        carpeta
                    ),
                    proyecto_id=(
                        proyecto_id
                    ),
                )
            )

            if (
                resultado.ok
                and resultado.contexto
                is not None
            ):

                self._contextos[
                    proyecto_id
                ] = resultado.contexto

                proyecto.ultimo_error = None

            else:

                proyecto.ultimo_error = (
                    resultado.error
                )

        self._guardar_registro()

    def _refrescar_estados_desde_disco(
        self,
    ) -> None:

        for proyecto in (
            self._proyectos.values()
        ):

            carpeta = Path(
                proyecto.carpeta
            )

            if not carpeta.exists():
                continue

            gestor = (
                GestorEstadoProyectoSoftware(
                    carpeta
                )
            )

            estado = gestor.cargar()

            if estado is None:
                continue

            proyecto.estado = (
                estado.estado.value
            )

            proyecto.progreso = (
                estado.progreso
            )

        self._guardar_registro()

    # =========================================================
    # CONSULTA INTERNA
    # =========================================================

    def proyectos_registrados(
        self,
    ) -> list[ProyectoSoftwareAgente]:

        self._refrescar_estados_desde_disco()

        return list(
            self._proyectos.values()
        )

    def obtener_proyecto(
        self,
        proyecto_id: str,
    ) -> ProyectoSoftwareAgente | None:

        proyecto = (
            self._proyectos.get(
                proyecto_id
            )
        )

        if proyecto is not None:

            self._refrescar_proyecto(
                proyecto
            )

        return proyecto

    def actualizar_prioridad(
        self,
        proyecto_id: str,
        prioridad: float | None = None,
        urgencia: float | None = None,
    ) -> bool:

        proyecto = (
            self._proyectos.get(
                proyecto_id
            )
        )

        if proyecto is None:
            return False

        if prioridad is not None:

            proyecto.prioridad = (
                self._clamp(
                    prioridad
                )
            )

        if urgencia is not None:

            proyecto.urgencia = (
                self._clamp(
                    urgencia
                )
            )

        self._guardar_registro()

        return True

    # =========================================================
    # DESTINO
    # =========================================================

    def _resolver_carpeta(
        self,
        nombre: str,
        carpeta: str | Path | None = None,
    ) -> Path:

        if carpeta is not None:

            destino = Path(
                carpeta
            ).expanduser().resolve()

        else:

            destino = (
                self.raiz_proyectos
                / self._nombre_seguro(
                    nombre
                )
            ).resolve()

        destino.mkdir(
            parents=True,
            exist_ok=True,
        )

        return destino

    # =========================================================
    # CREAR
    # =========================================================

    def crear_proyecto(
        self,
        descripcion: str,
        carpeta: str | Path | None = None,
        nombre_sugerido: str | None = None,
        creado_por: str = "agente",
        prioridad: float = 0.70,
        urgencia: float = 0.0,
    ) -> ResultadoCapacidadDesarrollo:

        descripcion = (
            descripcion
            or ""
        ).strip()

        if not descripcion:

            return ResultadoCapacidadDesarrollo(
                ok=False,
                accion=(
                    AccionDesarrollo
                    .CREAR_PROYECTO
                ),
                error="descripcion_vacia",
                mensaje=(
                    "No se puede crear un proyecto "
                    "sin descripción."
                ),
            )

        nombre_temporal = (
            nombre_sugerido
            or (
                "Proyecto ATENAS "
                + str(
                    uuid.uuid4()
                )[:8]
            )
        )

        destino = (
            self._resolver_carpeta(
                nombre=nombre_temporal,
                carpeta=carpeta,
            )
        )

        inicio = (
            self.orquestador
            .iniciar(
                descripcion=descripcion,
                carpeta_proyecto=destino,
            )
        )

        if not inicio.ok:

            return ResultadoCapacidadDesarrollo(
                ok=False,
                accion=(
                    AccionDesarrollo
                    .CREAR_PROYECTO
                ),
                proyecto_id=(
                    inicio.proyecto_id
                ),
                carpeta=(
                    inicio.carpeta_proyecto
                ),
                error=(
                    inicio.error
                ),
                mensaje=(
                    "El subsistema de desarrollo "
                    "no pudo iniciar el proyecto."
                ),
            )

        nombre_real = (
            inicio.analisis.nombre_proyecto
            if inicio.analisis
            is not None
            else nombre_temporal
        )

        estado_valor = (
            inicio.estado.estado.value
            if inicio.estado
            is not None
            else "planificado"
        )

        progreso = (
            inicio.estado.progreso
            if inicio.estado
            is not None
            else 0.0
        )

        proyecto = (
            ProyectoSoftwareAgente(
                id=inicio.proyecto_id,
                nombre=nombre_real,
                carpeta=(
                    inicio.carpeta_proyecto
                ),
                descripcion=descripcion,
                estado=estado_valor,
                progreso=progreso,
                prioridad=self._clamp(
                    prioridad
                ),
                urgencia=self._clamp(
                    urgencia
                ),
                creado_por=creado_por,
                metadata={
                    "tipo_solucion": (
                        inicio.analisis
                        .tipo_solucion
                        .value
                        if inicio.analisis
                        is not None
                        else None
                    ),
                    "arquitectura": (
                        inicio.arquitectura
                        .estilo
                        if inicio.arquitectura
                        is not None
                        else None
                    ),
                    "complejidad": (
                        inicio.analisis
                        .complejidad
                        if inicio.analisis
                        is not None
                        else None
                    ),
                },
            )
        )

        self._proyectos[
            proyecto.id
        ] = proyecto

        self._contextos[
            proyecto.id
        ] = inicio

        self._guardar_registro()

        return ResultadoCapacidadDesarrollo(
            ok=True,
            accion=(
                AccionDesarrollo
                .CREAR_PROYECTO
            ),
            proyecto_id=(
                proyecto.id
            ),
            carpeta=(
                proyecto.carpeta
            ),
            estado=(
                proyecto.estado
            ),
            progreso=(
                proyecto.progreso
            ),
            mensaje=(
                f"Proyecto '{proyecto.nombre}' "
                "analizado, diseñado y planificado."
            ),
            datos={
                "nombre":
                    proyecto.nombre,

                "tipo_solucion":
                    proyecto.metadata.get(
                        "tipo_solucion"
                    ),

                "arquitectura":
                    proyecto.metadata.get(
                        "arquitectura"
                    ),

                "complejidad":
                    proyecto.metadata.get(
                        "complejidad"
                    ),

                "prioridad":
                    proyecto.prioridad,

                "urgencia":
                    proyecto.urgencia,
            },
        )

    # =========================================================
    # CONTINUAR
    # =========================================================

    def continuar_proyecto(
        self,
        proyecto_id: str,
        max_ciclos: int = 1,
    ) -> ResultadoCapacidadDesarrollo:

        proyecto = (
            self._proyectos.get(
                proyecto_id
            )
        )

        if proyecto is None:

            return ResultadoCapacidadDesarrollo(
                ok=False,
                accion=(
                    AccionDesarrollo
                    .CONTINUAR_PROYECTO
                ),
                proyecto_id=proyecto_id,
                error=(
                    "proyecto_no_encontrado"
                ),
                mensaje=(
                    "No existe un proyecto registrado "
                    "con ese ID."
                ),
            )

        inicio = (
            self._contextos.get(
                proyecto_id
            )
        )

        if inicio is None:

            restaurado = (
                self.restaurador
                .restaurar(
                    carpeta_proyecto=(
                        proyecto.carpeta
                    ),
                    proyecto_id=(
                        proyecto.id
                    ),
                )
            )

            if (
                not restaurado.ok
                or restaurado.contexto
                is None
            ):

                proyecto.ultimo_error = (
                    restaurado.error
                    or "restauracion_fallida"
                )

                self._guardar_registro()

                return ResultadoCapacidadDesarrollo(
                    ok=False,
                    accion=(
                        AccionDesarrollo
                        .CONTINUAR_PROYECTO
                    ),
                    proyecto_id=(
                        proyecto.id
                    ),
                    carpeta=(
                        proyecto.carpeta
                    ),
                    estado=(
                        proyecto.estado
                    ),
                    progreso=(
                        proyecto.progreso
                    ),
                    error=(
                        proyecto
                        .ultimo_error
                    ),
                    mensaje=(
                        "No fue posible reconstruir "
                        "el contexto persistente del proyecto."
                    ),
                )

            inicio = (
                restaurado.contexto
            )

            self._contextos[
                proyecto.id
            ] = inicio

        if (
            inicio.analisis is None
            or inicio.arquitectura is None
            or inicio.plan is None
        ):

            return ResultadoCapacidadDesarrollo(
                ok=False,
                accion=(
                    AccionDesarrollo
                    .CONTINUAR_PROYECTO
                ),
                proyecto_id=proyecto_id,
                error="contexto_incompleto",
                mensaje=(
                    "El contexto restaurado está incompleto."
                ),
            )

        resultados = (
            self.orquestador
            .ejecutar_hasta_pausa(
                carpeta_proyecto=(
                    proyecto.carpeta
                ),
                proyecto_id=(
                    proyecto.id
                ),
                analisis=(
                    inicio.analisis
                ),
                arquitectura=(
                    inicio.arquitectura
                ),
                modelo_bd=(
                    inicio.modelo_bd
                ),
                plan=(
                    inicio.plan
                ),
                max_ciclos=max(
                    1,
                    int(
                        max_ciclos
                    ),
                ),
            )
        )

        if not resultados:

            return ResultadoCapacidadDesarrollo(
                ok=False,
                accion=(
                    AccionDesarrollo
                    .CONTINUAR_PROYECTO
                ),
                proyecto_id=proyecto_id,
                error="sin_resultados",
            )

        ultimo: ResultadoCicloDesarrollo = (
            resultados[-1]
        )

        proyecto.ultimo_error = (
            ultimo.error
        )

        self._refrescar_proyecto(
            proyecto
        )

        self._guardar_registro()

        return ResultadoCapacidadDesarrollo(
            ok=(
                ultimo.ok
            ),
            accion=(
                AccionDesarrollo
                .CONTINUAR_PROYECTO
            ),
            proyecto_id=(
                proyecto.id
            ),
            carpeta=(
                proyecto.carpeta
            ),
            estado=(
                proyecto.estado
            ),
            progreso=(
                proyecto.progreso
            ),
            mensaje=(
                ultimo.mensaje
            ),
            requiere_confirmacion=(
                ultimo.requiere_confirmacion
            ),
            dependencias_pendientes=(
                ultimo.dependencias_pendientes
            ),
            datos={
                "tarea":
                    ultimo.tarea,

                "plan_completado":
                    ultimo.plan_completado,

                "ciclos_ejecutados":
                    len(
                        resultados
                    ),

                "prioridad":
                    proyecto.prioridad,

                "urgencia":
                    proyecto.urgencia,
            },
            error=(
                ultimo.error
            ),
        )

    # =========================================================
    # ESTADO / LISTADO
    # =========================================================

    def _refrescar_proyecto(
        self,
        proyecto: ProyectoSoftwareAgente,
    ) -> None:

        gestor = (
            GestorEstadoProyectoSoftware(
                proyecto.carpeta
            )
        )

        estado = gestor.cargar()

        if estado is None:
            return

        proyecto.estado = (
            estado.estado.value
        )

        proyecto.progreso = (
            estado.progreso
        )

    def estado_proyecto(
        self,
        proyecto_id: str,
    ) -> ResultadoCapacidadDesarrollo:

        proyecto = (
            self._proyectos.get(
                proyecto_id
            )
        )

        if proyecto is None:

            return ResultadoCapacidadDesarrollo(
                ok=False,
                accion=(
                    AccionDesarrollo
                    .CONSULTAR_ESTADO
                ),
                proyecto_id=proyecto_id,
                error=(
                    "proyecto_no_encontrado"
                ),
            )

        self._refrescar_proyecto(
            proyecto
        )

        gestor = (
            GestorEstadoProyectoSoftware(
                proyecto.carpeta
            )
        )

        estado = gestor.cargar()

        self._guardar_registro()

        if estado is None:

            return ResultadoCapacidadDesarrollo(
                ok=False,
                accion=(
                    AccionDesarrollo
                    .CONSULTAR_ESTADO
                ),
                proyecto_id=(
                    proyecto.id
                ),
                carpeta=(
                    proyecto.carpeta
                ),
                estado=(
                    proyecto.estado
                ),
                progreso=(
                    proyecto.progreso
                ),
                error=(
                    "estado_no_disponible"
                ),
            )

        resumen = (
            gestor.resumen_para_agente(
                estado
            )
        )

        resumen[
            "prioridad"
        ] = proyecto.prioridad

        resumen[
            "urgencia"
        ] = proyecto.urgencia

        return ResultadoCapacidadDesarrollo(
            ok=True,
            accion=(
                AccionDesarrollo
                .CONSULTAR_ESTADO
            ),
            proyecto_id=(
                proyecto.id
            ),
            carpeta=(
                proyecto.carpeta
            ),
            estado=(
                estado.estado.value
            ),
            progreso=(
                estado.progreso
            ),
            mensaje=(
                f"{estado.nombre}: "
                f"{estado.progreso:.1f}% "
                f"({estado.estado.value})."
            ),
            datos=resumen,
        )

    def listar_proyectos(
        self,
        solo_activos: bool = False,
    ) -> ResultadoCapacidadDesarrollo:

        proyectos = (
            self.proyectos_registrados()
        )

        if solo_activos:

            proyectos = [
                proyecto
                for proyecto
                in proyectos
                if proyecto.estado
                not in {
                    "completado",
                    "fallido",
                }
            ]

        proyectos.sort(
            key=lambda item: (
                item.prioridad,
                item.urgencia,
                item.progreso,
            ),
            reverse=True,
        )

        return ResultadoCapacidadDesarrollo(
            ok=True,
            accion=(
                AccionDesarrollo
                .LISTAR_PROYECTOS
            ),
            mensaje=(
                f"{len(proyectos)} proyecto(s) "
                "registrado(s)."
            ),
            datos={
                "proyectos": [
                    self._serializar_proyecto(
                        proyecto
                    )
                    for proyecto
                    in proyectos
                ]
            },
        )

    # =========================================================
    # COMPATIBILIDAD
    # =========================================================

    def seleccionar_proyecto_continuable(
        self,
    ) -> ProyectoSoftwareAgente | None:

        candidatos = [
            proyecto
            for proyecto
            in self.proyectos_registrados()
            if proyecto.estado
            not in {
                "completado",
                "fallido",
                "bloqueado",
                "pausado",
            }
        ]

        if not candidatos:
            return None

        candidatos.sort(
            key=lambda item: (
                item.prioridad,
                item.urgencia,
                item.progreso,
            ),
            reverse=True,
        )

        return candidatos[0]