from __future__ import annotations

import json
import sqlite3
import uuid

from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class EstadoProyecto(str, Enum):
    PROPUESTO = "propuesto"
    ACTIVO = "activo"
    PAUSADO = "pausado"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"
    BLOQUEADO = "bloqueado"


class EstadoObjetivoProyecto(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADO = "completado"
    BLOQUEADO = "bloqueado"
    CANCELADO = "cancelado"


@dataclass
class ObjetivoProyecto:
    id: str
    proyecto_id: str
    descripcion: str

    prioridad: float = 0.5
    estado: EstadoObjetivoProyecto = (
        EstadoObjetivoProyecto.PENDIENTE
    )

    orden: int = 0

    depende_de: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    creado_en: str = ""
    actualizado_en: str = ""


@dataclass
class ProyectoInterno:
    id: str

    nombre: str
    descripcion: str

    origen: str

    prioridad: float = 0.5

    estado: EstadoProyecto = (
        EstadoProyecto.PROPUESTO
    )

    autonomia: bool = True

    requiere_confirmacion: bool = False

    creado_en: str = ""
    actualizado_en: str = ""

    ultimo_trabajo: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    objetivos: list[
        ObjetivoProyecto
    ] = field(
        default_factory=list
    )


class GestorProyectosInternos:
    """
    Memoria de trabajo de medio/largo plazo para ATENAS.

    Permite que ATENAS cree y mantenga proyectos propios de
    ingeniería, por ejemplo:

    - aumentar cobertura de tests;
    - preparar visión;
    - preparar controlador de servos;
    - reorganizar memoria;
    - investigar un protocolo;
    - construir una nueva capacidad.

    Este gestor NO programa por sí mismo.
    Conserva proyectos, objetivos, dependencias y progreso.
    """

    def __init__(
        self,
        db_path: str | Path,
    ):
        self.db_path = Path(
            db_path
        ).resolve()

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._crear_esquema()

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _ahora() -> str:

        return (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

    def _conexion(
        self,
    ) -> sqlite3.Connection:

        conn = sqlite3.connect(
            str(
                self.db_path
            ),
            timeout=10.0,
        )

        conn.row_factory = (
            sqlite3.Row
        )

        return conn

    # =========================================================
    # ESQUEMA
    # =========================================================

    def _crear_esquema(
        self,
    ) -> None:

        with closing(
            self._conexion()
        ) as conn:

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS proyectos_internos (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    origen TEXT NOT NULL,
                    prioridad REAL NOT NULL,
                    estado TEXT NOT NULL,
                    autonomia INTEGER NOT NULL,
                    requiere_confirmacion INTEGER NOT NULL,
                    creado_en TEXT NOT NULL,
                    actualizado_en TEXT NOT NULL,
                    ultimo_trabajo TEXT,
                    metadata_json TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS objetivos_proyecto (
                    id TEXT PRIMARY KEY,
                    proyecto_id TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    prioridad REAL NOT NULL,
                    estado TEXT NOT NULL,
                    orden_objetivo INTEGER NOT NULL,
                    depende_de_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    creado_en TEXT NOT NULL,
                    actualizado_en TEXT NOT NULL,
                    FOREIGN KEY(proyecto_id)
                        REFERENCES proyectos_internos(id)
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_proyectos_estado
                ON proyectos_internos(estado)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_objetivos_proyecto
                ON objetivos_proyecto(proyecto_id)
                """
            )

            conn.commit()

    # =========================================================
    # CONVERSIÓN
    # =========================================================

    @staticmethod
    def _json(
        texto: str | None,
        defecto,
    ):

        if not texto:
            return defecto

        try:

            return json.loads(
                texto
            )

        except Exception:

            return defecto

    def _fila_objetivo(
        self,
        fila: sqlite3.Row,
    ) -> ObjetivoProyecto:

        return ObjetivoProyecto(
            id=fila["id"],
            proyecto_id=(
                fila["proyecto_id"]
            ),
            descripcion=(
                fila["descripcion"]
            ),
            prioridad=float(
                fila["prioridad"]
            ),
            estado=(
                EstadoObjetivoProyecto(
                    fila["estado"]
                )
            ),
            orden=int(
                fila["orden_objetivo"]
            ),
            depende_de=(
                self._json(
                    fila[
                        "depende_de_json"
                    ],
                    [],
                )
            ),
            metadata=(
                self._json(
                    fila[
                        "metadata_json"
                    ],
                    {},
                )
            ),
            creado_en=(
                fila["creado_en"]
            ),
            actualizado_en=(
                fila[
                    "actualizado_en"
                ]
            ),
        )

    def _cargar_objetivos(
        self,
        proyecto_id: str,
    ) -> list[ObjetivoProyecto]:

        with closing(
            self._conexion()
        ) as conn:

            filas = conn.execute(
                """
                SELECT *
                FROM objetivos_proyecto
                WHERE proyecto_id = ?
                ORDER BY orden_objetivo ASC,
                         prioridad DESC,
                         creado_en ASC
                """,
                (
                    proyecto_id,
                ),
            ).fetchall()

        return [
            self._fila_objetivo(
                fila
            )
            for fila in filas
        ]

    def _fila_proyecto(
        self,
        fila: sqlite3.Row,
        cargar_objetivos: bool = True,
    ) -> ProyectoInterno:

        proyecto = ProyectoInterno(
            id=fila["id"],
            nombre=fila["nombre"],
            descripcion=(
                fila["descripcion"]
            ),
            origen=fila["origen"],
            prioridad=float(
                fila["prioridad"]
            ),
            estado=EstadoProyecto(
                fila["estado"]
            ),
            autonomia=bool(
                fila["autonomia"]
            ),
            requiere_confirmacion=bool(
                fila[
                    "requiere_confirmacion"
                ]
            ),
            creado_en=(
                fila["creado_en"]
            ),
            actualizado_en=(
                fila["actualizado_en"]
            ),
            ultimo_trabajo=(
                fila["ultimo_trabajo"]
            ),
            metadata=(
                self._json(
                    fila[
                        "metadata_json"
                    ],
                    {},
                )
            ),
        )

        if cargar_objetivos:

            proyecto.objetivos = (
                self._cargar_objetivos(
                    proyecto.id
                )
            )

        return proyecto

    # =========================================================
    # CREAR PROYECTO
    # =========================================================

    def crear_proyecto(
        self,
        nombre: str,
        descripcion: str,
        origen: str = "atenas",
        prioridad: float = 0.5,
        autonomia: bool = True,
        requiere_confirmacion: bool = False,
        metadata: dict[str, Any] | None = None,
        activar: bool = True,
    ) -> ProyectoInterno:

        nombre = (
            nombre
            or ""
        ).strip()

        descripcion = (
            descripcion
            or ""
        ).strip()

        if not nombre:

            raise ValueError(
                "El proyecto necesita nombre."
            )

        ahora = self._ahora()

        proyecto_id = str(
            uuid.uuid4()
        )

        estado = (
            EstadoProyecto.ACTIVO
            if activar
            else EstadoProyecto.PROPUESTO
        )

        with closing(
            self._conexion()
        ) as conn:

            conn.execute(
                """
                INSERT INTO proyectos_internos (
                    id,
                    nombre,
                    descripcion,
                    origen,
                    prioridad,
                    estado,
                    autonomia,
                    requiere_confirmacion,
                    creado_en,
                    actualizado_en,
                    ultimo_trabajo,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    proyecto_id,
                    nombre,
                    descripcion,
                    origen,
                    max(
                        0.0,
                        min(
                            float(
                                prioridad
                            ),
                            1.0,
                        ),
                    ),
                    estado.value,
                    int(
                        bool(
                            autonomia
                        )
                    ),
                    int(
                        bool(
                            requiere_confirmacion
                        )
                    ),
                    ahora,
                    ahora,
                    None,
                    json.dumps(
                        metadata
                        or {},
                        ensure_ascii=False,
                        default=str,
                    ),
                ),
            )

            conn.commit()

        proyecto = self.obtener_proyecto(
            proyecto_id
        )

        assert proyecto is not None

        return proyecto

    # =========================================================
    # OBJETIVOS
    # =========================================================

    def agregar_objetivo(
        self,
        proyecto_id: str,
        descripcion: str,
        prioridad: float = 0.5,
        orden: int | None = None,
        depende_de: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ObjetivoProyecto:

        proyecto = self.obtener_proyecto(
            proyecto_id
        )

        if proyecto is None:

            raise KeyError(
                "Proyecto no encontrado: "
                f"{proyecto_id}"
            )

        descripcion = (
            descripcion
            or ""
        ).strip()

        if not descripcion:

            raise ValueError(
                "El objetivo necesita descripción."
            )

        if orden is None:

            orden = len(
                proyecto.objetivos
            )

        ahora = self._ahora()

        objetivo = ObjetivoProyecto(
            id=str(
                uuid.uuid4()
            ),
            proyecto_id=(
                proyecto_id
            ),
            descripcion=descripcion,
            prioridad=max(
                0.0,
                min(
                    float(
                        prioridad
                    ),
                    1.0,
                ),
            ),
            estado=(
                EstadoObjetivoProyecto
                .PENDIENTE
            ),
            orden=int(
                orden
            ),
            depende_de=list(
                depende_de
                or []
            ),
            metadata=(
                metadata
                or {}
            ),
            creado_en=ahora,
            actualizado_en=ahora,
        )

        with closing(
            self._conexion()
        ) as conn:

            conn.execute(
                """
                INSERT INTO objetivos_proyecto (
                    id,
                    proyecto_id,
                    descripcion,
                    prioridad,
                    estado,
                    orden_objetivo,
                    depende_de_json,
                    metadata_json,
                    creado_en,
                    actualizado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    objetivo.id,
                    objetivo.proyecto_id,
                    objetivo.descripcion,
                    objetivo.prioridad,
                    objetivo.estado.value,
                    objetivo.orden,
                    json.dumps(
                        objetivo.depende_de,
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        objetivo.metadata,
                        ensure_ascii=False,
                        default=str,
                    ),
                    objetivo.creado_en,
                    objetivo.actualizado_en,
                ),
            )

            conn.execute(
                """
                UPDATE proyectos_internos
                SET actualizado_en = ?
                WHERE id = ?
                """,
                (
                    ahora,
                    proyecto_id,
                ),
            )

            conn.commit()

        return objetivo

    # =========================================================
    # CONSULTAS
    # =========================================================

    def obtener_proyecto(
        self,
        proyecto_id: str,
    ) -> ProyectoInterno | None:

        with closing(
            self._conexion()
        ) as conn:

            fila = conn.execute(
                """
                SELECT *
                FROM proyectos_internos
                WHERE id = ?
                LIMIT 1
                """,
                (
                    proyecto_id,
                ),
            ).fetchone()

        if fila is None:
            return None

        return self._fila_proyecto(
            fila
        )

    def listar_proyectos(
        self,
        incluir_finalizados: bool = False,
        limite: int = 100,
    ) -> list[ProyectoInterno]:

        sql = """
            SELECT *
            FROM proyectos_internos
        """

        parametros: list[Any] = []

        if not incluir_finalizados:

            sql += """
                WHERE estado NOT IN (?, ?)
            """

            parametros.extend([
                EstadoProyecto.COMPLETADO.value,
                EstadoProyecto.CANCELADO.value,
            ])

        sql += """
            ORDER BY prioridad DESC,
                     actualizado_en ASC
            LIMIT ?
        """

        parametros.append(
            max(
                1,
                int(
                    limite
                ),
            )
        )

        with closing(
            self._conexion()
        ) as conn:

            filas = conn.execute(
                sql,
                tuple(
                    parametros
                ),
            ).fetchall()

        return [
            self._fila_proyecto(
                fila
            )
            for fila in filas
        ]

    # =========================================================
    # SIGUIENTE OBJETIVO
    # =========================================================

    def siguiente_objetivo(
        self,
        proyecto_id: str,
    ) -> ObjetivoProyecto | None:

        proyecto = self.obtener_proyecto(
            proyecto_id
        )

        if proyecto is None:
            return None

        completados = {
            objetivo.id
            for objetivo
            in proyecto.objetivos
            if (
                objetivo.estado
                == EstadoObjetivoProyecto
                .COMPLETADO
            )
        }

        candidatos = []

        for objetivo in proyecto.objetivos:

            if (
                objetivo.estado
                not in {
                    EstadoObjetivoProyecto
                    .PENDIENTE,

                    EstadoObjetivoProyecto
                    .EN_PROGRESO,
                }
            ):

                continue

            dependencias_ok = all(
                dependencia
                in completados
                for dependencia
                in objetivo.depende_de
            )

            if not dependencias_ok:
                continue

            candidatos.append(
                objetivo
            )

        if not candidatos:
            return None

        candidatos.sort(
            key=lambda item: (
                item.estado
                == EstadoObjetivoProyecto
                .EN_PROGRESO,

                item.prioridad,

                -item.orden,
            ),
            reverse=True,
        )

        return candidatos[0]

    # =========================================================
    # ESTADOS DE OBJETIVOS
    # =========================================================

    def cambiar_estado_objetivo(
        self,
        objetivo_id: str,
        estado: EstadoObjetivoProyecto,
    ) -> ObjetivoProyecto:

        ahora = self._ahora()

        with closing(
            self._conexion()
        ) as conn:

            fila = conn.execute(
                """
                SELECT proyecto_id
                FROM objetivos_proyecto
                WHERE id = ?
                LIMIT 1
                """,
                (
                    objetivo_id,
                ),
            ).fetchone()

            if fila is None:

                raise KeyError(
                    "Objetivo no encontrado: "
                    f"{objetivo_id}"
                )

            proyecto_id = (
                fila["proyecto_id"]
            )

            conn.execute(
                """
                UPDATE objetivos_proyecto
                SET
                    estado = ?,
                    actualizado_en = ?
                WHERE id = ?
                """,
                (
                    estado.value,
                    ahora,
                    objetivo_id,
                ),
            )

            conn.execute(
                """
                UPDATE proyectos_internos
                SET actualizado_en = ?
                WHERE id = ?
                """,
                (
                    ahora,
                    proyecto_id,
                ),
            )

            conn.commit()

        proyecto = self.obtener_proyecto(
            proyecto_id
        )

        assert proyecto is not None

        objetivo = next(
            item
            for item in proyecto.objetivos
            if item.id == objetivo_id
        )

        return objetivo

    def iniciar_objetivo(
        self,
        objetivo_id: str,
    ) -> ObjetivoProyecto:

        return (
            self.cambiar_estado_objetivo(
                objetivo_id,
                EstadoObjetivoProyecto
                .EN_PROGRESO,
            )
        )

    def completar_objetivo(
        self,
        objetivo_id: str,
    ) -> ObjetivoProyecto:

        objetivo = (
            self.cambiar_estado_objetivo(
                objetivo_id,
                EstadoObjetivoProyecto
                .COMPLETADO,
            )
        )

        self._recalcular_proyecto(
            objetivo.proyecto_id
        )

        return objetivo

    # =========================================================
    # ESTADO DEL PROYECTO
    # =========================================================

    def _recalcular_proyecto(
        self,
        proyecto_id: str,
    ) -> None:

        proyecto = self.obtener_proyecto(
            proyecto_id
        )

        if (
            proyecto is None
            or not proyecto.objetivos
        ):
            return

        if all(
            objetivo.estado
            == EstadoObjetivoProyecto
            .COMPLETADO
            for objetivo
            in proyecto.objetivos
        ):

            self.cambiar_estado_proyecto(
                proyecto_id,
                EstadoProyecto.COMPLETADO,
            )

    def cambiar_estado_proyecto(
        self,
        proyecto_id: str,
        estado: EstadoProyecto,
    ) -> ProyectoInterno:

        ahora = self._ahora()

        with closing(
            self._conexion()
        ) as conn:

            cursor = conn.execute(
                """
                UPDATE proyectos_internos
                SET
                    estado = ?,
                    actualizado_en = ?
                WHERE id = ?
                """,
                (
                    estado.value,
                    ahora,
                    proyecto_id,
                ),
            )

            conn.commit()

            if cursor.rowcount == 0:

                raise KeyError(
                    "Proyecto no encontrado: "
                    f"{proyecto_id}"
                )

        proyecto = self.obtener_proyecto(
            proyecto_id
        )

        assert proyecto is not None

        return proyecto

    # =========================================================
    # REGISTRAR TRABAJO
    # =========================================================

    def registrar_trabajo(
        self,
        proyecto_id: str,
        descripcion: str,
    ) -> ProyectoInterno:

        ahora = self._ahora()

        with closing(
            self._conexion()
        ) as conn:

            cursor = conn.execute(
                """
                UPDATE proyectos_internos
                SET
                    ultimo_trabajo = ?,
                    actualizado_en = ?
                WHERE id = ?
                """,
                (
                    descripcion,
                    ahora,
                    proyecto_id,
                ),
            )

            conn.commit()

            if cursor.rowcount == 0:

                raise KeyError(
                    "Proyecto no encontrado: "
                    f"{proyecto_id}"
                )

        proyecto = self.obtener_proyecto(
            proyecto_id
        )

        assert proyecto is not None

        return proyecto

    # =========================================================
    # ELEGIR PROYECTO PRIORITARIO
    # =========================================================

    def proyecto_prioritario(
        self,
    ) -> ProyectoInterno | None:

        proyectos = (
            self.listar_proyectos()
        )

        candidatos = [
            proyecto
            for proyecto
            in proyectos
            if (
                proyecto.estado
                == EstadoProyecto.ACTIVO
                and proyecto.autonomia
            )
        ]

        if not candidatos:
            return None

        candidatos.sort(
            key=lambda item: (
                item.prioridad,
                -len(
                    [
                        objetivo
                        for objetivo
                        in item.objetivos
                        if (
                            objetivo.estado
                            != EstadoObjetivoProyecto
                            .COMPLETADO
                        )
                    ]
                ),
            ),
            reverse=True,
        )

        return candidatos[0]

    # =========================================================
    # CONTEXTO PARA LLM
    # =========================================================

    def contexto_para_llm(
        self,
        limite: int = 10,
    ) -> str:

        proyectos = (
            self.listar_proyectos(
                limite=limite
            )
        )

        if not proyectos:

            return (
                "PROYECTOS INTERNOS DE ATENAS:\n"
                "- Ninguno activo."
            )

        lineas = [
            "PROYECTOS INTERNOS DE ATENAS:"
        ]

        for proyecto in proyectos:

            pendientes = [
                objetivo
                for objetivo
                in proyecto.objetivos
                if (
                    objetivo.estado
                    != EstadoObjetivoProyecto
                    .COMPLETADO
                )
            ]

            lineas.append(
                (
                    f"- {proyecto.id} | "
                    f"{proyecto.nombre} | "
                    f"estado={proyecto.estado.value} | "
                    f"prioridad={proyecto.prioridad:.2f} | "
                    f"objetivos_pendientes={len(pendientes)}"
                )
            )

            siguiente = (
                self.siguiente_objetivo(
                    proyecto.id
                )
            )

            if siguiente is not None:

                lineas.append(
                    "  Siguiente objetivo: "
                    + siguiente.descripcion
                )

        return "\n".join(
            lineas
        )