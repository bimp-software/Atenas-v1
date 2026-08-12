from __future__ import annotations

import json

from src.atenas.memoria.database import Database

from .objetivos import Objetivo, EstadoObjetivo
from .pendientes import Pendiente, EstadoPendiente


class PersistenciaAgente:

    def __init__(
        self,
        db: Database | None = None,
    ):
        self.db = db or Database()

    # =========================================================
    # OBJETIVOS
    # =========================================================

    def guardar_objetivo(
        self,
        objetivo: Objetivo,
    ) -> None:

        with self.db.conexion() as conn:

            conn.execute("""
                INSERT INTO agent_objectives (
                    id,
                    nombre,
                    descripcion,
                    prioridad,
                    estado,
                    autonomia
                )
                VALUES (?, ?, ?, ?, ?, ?)

                ON CONFLICT(id)
                DO UPDATE SET
                    nombre = excluded.nombre,
                    descripcion = excluded.descripcion,
                    prioridad = excluded.prioridad,
                    estado = excluded.estado,
                    autonomia = excluded.autonomia,
                    actualizado_en = CURRENT_TIMESTAMP
            """, (
                objetivo.id,
                objetivo.nombre,
                objetivo.descripcion,
                objetivo.prioridad,
                objetivo.estado.value,
                1 if objetivo.autonomia else 0,
            ))

    def cargar_objetivos(
        self,
    ) -> list[Objetivo]:

        with self.db.conexion() as conn:

            rows = conn.execute("""
                SELECT *
                FROM agent_objectives
            """).fetchall()

        return [
            Objetivo(
                id=row["id"],
                nombre=row["nombre"],
                descripcion=row["descripcion"],
                prioridad=row["prioridad"],
                estado=EstadoObjetivo(
                    row["estado"]
                ),
                autonomia=bool(
                    row["autonomia"]
                ),
            )
            for row in rows
        ]

    # =========================================================
    # PENDIENTES
    # =========================================================

    def guardar_pendiente(
        self,
        pendiente: Pendiente,
    ) -> None:

        with self.db.conexion() as conn:

            conn.execute("""
                INSERT INTO agent_tasks (
                    id,
                    descripcion,
                    objetivo_id,
                    prioridad,
                    estado,
                    requiere_confirmacion,
                    resultado
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(id)
                DO UPDATE SET
                    descripcion = excluded.descripcion,
                    objetivo_id = excluded.objetivo_id,
                    prioridad = excluded.prioridad,
                    estado = excluded.estado,
                    requiere_confirmacion = excluded.requiere_confirmacion,
                    resultado = excluded.resultado,
                    actualizado_en = CURRENT_TIMESTAMP
            """, (
                pendiente.id,
                pendiente.descripcion,
                pendiente.objetivo_id,
                pendiente.prioridad,
                pendiente.estado.value,
                1 if pendiente.requiere_confirmacion else 0,
                pendiente.resultado,
            ))

    def cargar_pendientes(
        self,
    ) -> list[Pendiente]:

        with self.db.conexion() as conn:

            rows = conn.execute("""
                SELECT *
                FROM agent_tasks
                WHERE estado IN (
                    'pendiente',
                    'en_proceso'
                )
            """).fetchall()

        return [
            Pendiente(
                id=row["id"],
                descripcion=row["descripcion"],
                objetivo_id=row["objetivo_id"],
                prioridad=row["prioridad"],
                estado=EstadoPendiente(
                    row["estado"]
                ),
                requiere_confirmacion=bool(
                    row["requiere_confirmacion"]
                ),
                resultado=row["resultado"],
            )
            for row in rows
        ]

    # =========================================================
    # HISTORIAL DE ACCIONES
    # =========================================================

    def registrar_accion(
        self,
        pendiente_id: str | None,
        herramienta: str,
        argumentos: dict,
        resultado: dict,
    ) -> None:

        with self.db.conexion() as conn:

            conn.execute("""
                INSERT INTO agent_actions (
                    pendiente_id,
                    herramienta,
                    argumentos,
                    exito,
                    resultado
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                pendiente_id,
                herramienta,
                json.dumps(
                    argumentos,
                    ensure_ascii=False,
                ),
                1 if resultado.get(
                    "ok",
                    False,
                ) else 0,
                json.dumps(
                    resultado,
                    ensure_ascii=False,
                ),
            ))