from __future__ import annotations

import json
import sqlite3
import uuid

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .parche import CambioCodigo
from .verificador import ResultadoVerificacion


@dataclass
class RegistroCambio:
    id: str
    archivo: str
    descripcion: str
    riesgo: str
    estado: str

    hash_antes: str | None = None
    hash_despues: str | None = None

    diff: str = ""

    creado_en: str | None = None
    aplicado_en: str | None = None
    revertido_en: str | None = None


class HistorialCambios:

    def __init__(
        self,
        db_path: str | Path = "data/atenas_desarrollo.db",
    ):
        self.db_path = Path(
            db_path
        ).resolve()

        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._crear_tabla()

    # =========================================================
    # CONEXIÓN
    # =========================================================

    def _conexion(
        self,
    ) -> sqlite3.Connection:

        conn = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
        )

        conn.row_factory = sqlite3.Row

        return conn

    # =========================================================
    # TABLA
    # =========================================================

    def _crear_tabla(
        self,
    ) -> None:

        with closing(
            self._conexion()
        ) as conn:

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cambios_codigo (
                    id TEXT PRIMARY KEY,

                    archivo TEXT NOT NULL,

                    descripcion TEXT NOT NULL,

                    riesgo TEXT NOT NULL,

                    estado TEXT NOT NULL,

                    hash_antes TEXT,
                    hash_despues TEXT,

                    diff TEXT,

                    contenido_original TEXT,
                    contenido_nuevo TEXT,

                    pruebas_json TEXT,

                    creado_en TEXT NOT NULL,

                    aplicado_en TEXT,
                    revertido_en TEXT
                )
                """
            )

            conn.commit()

    # =========================================================
    # REGISTRAR PROPUESTA
    # =========================================================

    def registrar_propuesta(
        self,
        cambio: CambioCodigo,
        verificacion: ResultadoVerificacion,
        contenido_original: str,
        pruebas: dict | None = None,
    ) -> str:

        cambio_id = str(
            uuid.uuid4()
        )

        creado_en = (
            datetime.now()
            .astimezone()
            .isoformat()
        )

        pruebas_json = json.dumps(
            pruebas or {},
            ensure_ascii=False,
        )

        with closing(
            self._conexion()
        ) as conn:

            conn.execute(
                """
                INSERT INTO cambios_codigo (
                    id,
                    archivo,
                    descripcion,
                    riesgo,
                    estado,
                    hash_antes,
                    diff,
                    contenido_original,
                    contenido_nuevo,
                    pruebas_json,
                    creado_en
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cambio_id,
                    cambio.archivo,
                    cambio.razon,
                    verificacion.riesgo.value,
                    "validado",
                    cambio.contenido_original_hash,
                    cambio.diff,
                    contenido_original,
                    cambio.contenido_nuevo,
                    pruebas_json,
                    creado_en,
                ),
            )

            conn.commit()

        return cambio_id

    # =========================================================
    # MARCAR APLICADO
    # =========================================================

    def marcar_aplicado(
        self,
        cambio_id: str,
        hash_despues: str,
    ) -> None:

        aplicado_en = (
            datetime.now()
            .astimezone()
            .isoformat()
        )

        with closing(
            self._conexion()
        ) as conn:

            conn.execute(
                """
                UPDATE cambios_codigo

                SET
                    estado = ?,
                    hash_despues = ?,
                    aplicado_en = ?

                WHERE id = ?
                """,
                (
                    "aplicado",
                    hash_despues,
                    aplicado_en,
                    cambio_id,
                ),
            )

            conn.commit()

    # =========================================================
    # MARCAR REVERTIDO
    # =========================================================

    def marcar_revertido(
        self,
        cambio_id: str,
    ) -> None:

        revertido_en = (
            datetime.now()
            .astimezone()
            .isoformat()
        )

        with closing(
            self._conexion()
        ) as conn:

            conn.execute(
                """
                UPDATE cambios_codigo

                SET
                    estado = ?,
                    revertido_en = ?

                WHERE id = ?
                """,
                (
                    "revertido",
                    revertido_en,
                    cambio_id,
                ),
            )

            conn.commit()

    # =========================================================
    # MARCAR FALLIDO
    # =========================================================

    def marcar_fallido(
        self,
        cambio_id: str,
    ) -> None:

        with closing(
            self._conexion()
        ) as conn:

            conn.execute(
                """
                UPDATE cambios_codigo
                SET estado = ?
                WHERE id = ?
                """,
                (
                    "fallido",
                    cambio_id,
                ),
            )

            conn.commit()

    # =========================================================
    # OBTENER
    # =========================================================

    def obtener(
        self,
        cambio_id: str,
    ) -> dict | None:

        with closing(
            self._conexion()
        ) as conn:

            row = conn.execute(
                """
                SELECT *
                FROM cambios_codigo
                WHERE id = ?
                LIMIT 1
                """,
                (
                    cambio_id,
                ),
            ).fetchone()

            if row is None:
                return None

            return dict(
                row
            )

    # =========================================================
    # ÚLTIMOS
    # =========================================================

    def ultimos(
        self,
        limite: int = 20,
    ) -> list[dict]:

        limite = max(
            1,
            min(
                int(limite),
                100,
            ),
        )

        with closing(
            self._conexion()
        ) as conn:

            rows = conn.execute(
                """
                SELECT *
                FROM cambios_codigo
                ORDER BY creado_en DESC
                LIMIT ?
                """,
                (
                    limite,
                ),
            ).fetchall()

            return [
                dict(row)
                for row in rows
            ]

    # =========================================================
    # ÚLTIMO APLICADO
    # =========================================================

    def ultimo_aplicado(
        self,
    ) -> dict | None:

        with closing(
            self._conexion()
        ) as conn:

            row = conn.execute(
                """
                SELECT *
                FROM cambios_codigo

                WHERE estado = 'aplicado'

                ORDER BY aplicado_en DESC

                LIMIT 1
                """
            ).fetchone()

            if row is None:
                return None

            return dict(
                row
            )

    # =========================================================
    # CONTAR
    # =========================================================

    def contar(
        self,
    ) -> int:

        with closing(
            self._conexion()
        ) as conn:

            row = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM cambios_codigo
                """
            ).fetchone()

            return int(
                row["total"]
                if row
                else 0
            )