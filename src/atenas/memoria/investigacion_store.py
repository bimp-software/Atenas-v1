from __future__ import annotations

import json

from .database import Database


class InvestigacionStore:
    """
    Guarda el historial de investigaciones web realizadas
    por ATENAS.

    La síntesis útil puede convertirse además en memoria
    semántica mediante el Hipocampo.
    """

    def __init__(
        self,
        db: Database | None = None,
    ):
        self.db = db or Database()

    # =========================================================
    # GUARDAR
    # =========================================================

    def guardar(
        self,
        consulta: str,
        sintesis: str,
        fuentes: list[dict],
        confianza: float = 0.75,
        memoria_id: int | None = None,
        tipo_vigencia: str = "media",
        revisar_despues_dias: int = 30,
    ) -> int:

        consulta = consulta.strip()
        sintesis = sintesis.strip()

        if not consulta:
            raise ValueError(
                "La consulta no puede estar vacía."
            )

        if not sintesis:
            raise ValueError(
                "La síntesis no puede estar vacía."
            )

        fuentes_json = json.dumps(
            fuentes,
            ensure_ascii=False,
        )

        with self.db.conexion() as conn:

            cursor = conn.execute("""
                INSERT INTO investigaciones_web (
                    consulta,
                    sintesis,
                    fuentes_json,
                    confianza,
                    memoria_id,
                    tipo_vigencia,
                    revisar_despues_dias,
                    ultima_verificacion
                )

                VALUES (
                    ?, ?, ?, ?, ?, ?, ?,
                    CURRENT_TIMESTAMP
                )
            """, (
                consulta,
                sintesis,
                fuentes_json,
                confianza,
                memoria_id,
                tipo_vigencia,
                revisar_despues_dias,
            ))

            return int(
                cursor.lastrowid
            )

    # =========================================================
    # ÚLTIMAS INVESTIGACIONES
    # =========================================================

    def ultimas(
        self,
        limite: int = 20,
    ) -> list[dict]:

        limite = max(
            1,
            min(limite, 100),
        )

        with self.db.conexion() as conn:

            rows = conn.execute("""
                SELECT *
                FROM investigaciones_web

                ORDER BY creado_en DESC

                LIMIT ?
            """, (
                limite,
            )).fetchall()

        resultados = []

        for row in rows:

            item = dict(row)

            try:
                item["fuentes"] = json.loads(
                    item.pop("fuentes_json")
                )

            except Exception:
                item["fuentes"] = []

            resultados.append(
                item
            )

        return resultados

    # =========================================================
    # BUSCAR INVESTIGACIÓN PREVIA
    # =========================================================

    def buscar(
        self,
        consulta: str,
        limite: int = 5,
    ) -> list[dict]:

        consulta = consulta.strip()

        if not consulta:
            return []

        patron = f"%{consulta}%"

        with self.db.conexion() as conn:

            rows = conn.execute("""
                SELECT *
                FROM investigaciones_web

                WHERE consulta LIKE ?
                   OR sintesis LIKE ?

                ORDER BY creado_en DESC

                LIMIT ?
            """, (
                patron,
                patron,
                limite,
            )).fetchall()

        resultados = []

        for row in rows:

            item = dict(row)

            try:
                item["fuentes"] = json.loads(
                    item.pop("fuentes_json")
                )

            except Exception:
                item["fuentes"] = []

            resultados.append(
                item
            )

        return resultados