from __future__ import annotations

import json
import re

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .disenador_base_datos import (
    CampoBD,
    ModeloBaseDatos,
    RelacionBD,
    TablaBD,
)


@dataclass
class ArtefactoBaseDatos:
    ruta: str
    tipo: str
    contenido: str


@dataclass
class ResultadoGeneracionBaseDatos:
    ok: bool

    motor: str
    carpeta: str

    artefactos: list[
        ArtefactoBaseDatos
    ] = field(
        default_factory=list
    )

    manifiesto: str | None = None

    resumen: str = ""

    error: str | None = None


class GeneradorArtefactosBaseDatos:
    """
    Convierte ModeloBaseDatos en artefactos reales.

    Primera versión soportada:
    - PostgreSQL
    - SQLite

    Puede generar:
    - db/schema.sql
    - db/migrations/0001_initial.sql
    - db/README.md
    - .atenas/base_datos.json

    No se conecta todavía a una base real.
    No ejecuta migraciones automáticamente.
    No borra datos.
    """

    def __init__(
        self,
    ):
        pass

    # =========================================================
    # UTILIDADES SQL
    # =========================================================

    @staticmethod
    def _identificador(
        nombre: str,
    ) -> str:

        nombre = (
            nombre
            or ""
        ).strip()

        nombre = re.sub(
            r"[^a-zA-Z0-9_]+",
            "_",
            nombre,
        )

        nombre = nombre.strip(
            "_"
        )

        if not nombre:

            nombre = "campo"

        return nombre.lower()

    @staticmethod
    def _tipo_sql_postgres(
        tipo: str,
    ) -> str:

        valor = (
            tipo
            or ""
        ).strip().lower()

        mapa = {
            "uuid":
                "UUID",

            "string":
                "VARCHAR(255)",

            "text":
                "TEXT",

            "integer":
                "INTEGER",

            "int":
                "INTEGER",

            "bigint":
                "BIGINT",

            "float":
                "DOUBLE PRECISION",

            "decimal":
                "NUMERIC",

            "numeric":
                "NUMERIC",

            "boolean":
                "BOOLEAN",

            "bool":
                "BOOLEAN",

            "date":
                "DATE",

            "datetime":
                "TIMESTAMP WITH TIME ZONE",

            "timestamp":
                "TIMESTAMP WITH TIME ZONE",

            "json":
                "JSONB",

            "jsonb":
                "JSONB",

            "bytes":
                "BYTEA",
        }

        if valor.startswith(
            "varchar("
        ):

            return valor.upper()

        if valor.startswith(
            "numeric("
        ):

            return valor.upper()

        return mapa.get(
            valor,
            valor.upper()
            or "TEXT",
        )

    @staticmethod
    def _tipo_sqlite(
        tipo: str,
    ) -> str:

        valor = (
            tipo
            or ""
        ).strip().lower()

        if any(
            palabra in valor
            for palabra
            in [
                "int",
                "bool",
            ]
        ):

            return "INTEGER"

        if any(
            palabra in valor
            for palabra
            in [
                "real",
                "float",
                "double",
                "decimal",
                "numeric",
            ]
        ):

            return "REAL"

        if any(
            palabra in valor
            for palabra
            in [
                "blob",
                "byte",
            ]
        ):

            return "BLOB"

        return "TEXT"

    @staticmethod
    def _default_sql(
        valor: str | None,
    ) -> str | None:

        if valor is None:

            return None

        raw = (
            str(
                valor
            )
            .strip()
        )

        if not raw:

            return None

        lower = raw.lower()

        if lower in {
            "null",
            "true",
            "false",
            "current_timestamp",
            "current_date",
            "current_time",
        }:

            return raw.upper()

        if re.fullmatch(
            r"-?\d+(?:\.\d+)?",
            raw,
        ):

            return raw

        if (
            raw.startswith("'")
            and raw.endswith("'")
        ):

            return raw

        escaped = raw.replace(
            "'",
            "''",
        )

        return (
            "'"
            + escaped
            + "'"
        )

    # =========================================================
    # CREATE TABLE
    # =========================================================

    def _campo_sql(
        self,
        campo: CampoBD,
        motor: str,
        es_pk_simple: bool,
    ) -> str:

        nombre = (
            self._identificador(
                campo.nombre
            )
        )

        if motor == "postgresql":

            tipo = (
                self._tipo_sql_postgres(
                    campo.tipo
                )
            )

        else:

            tipo = (
                self._tipo_sqlite(
                    campo.tipo
                )
            )

        partes = [
            nombre,
            tipo,
        ]

        if es_pk_simple:

            partes.append(
                "PRIMARY KEY"
            )

        if not campo.nullable:

            partes.append(
                "NOT NULL"
            )

        if campo.unique:

            partes.append(
                "UNIQUE"
            )

        default = (
            self._default_sql(
                campo.default
            )
        )

        if default is not None:

            partes.extend([
                "DEFAULT",
                default,
            ])

        return " ".join(
            partes
        )

    def _tabla_sql(
        self,
        tabla: TablaBD,
        modelo: ModeloBaseDatos,
        motor: str,
    ) -> str:

        nombre_tabla = (
            self._identificador(
                tabla.nombre
            )
        )

        pk = [
            self._identificador(
                campo
            )
            for campo
            in tabla.clave_primaria
        ]

        columnas = []

        for campo in tabla.campos:

            nombre_campo = (
                self._identificador(
                    campo.nombre
                )
            )

            columnas.append(
                self._campo_sql(
                    campo=campo,
                    motor=motor,
                    es_pk_simple=(
                        len(pk) == 1
                        and nombre_campo
                        == pk[0]
                    ),
                )
            )

        restricciones = []

        if len(pk) > 1:

            restricciones.append(
                "PRIMARY KEY ("
                + ", ".join(
                    pk
                )
                + ")"
            )

        for relacion in modelo.relaciones:

            if (
                self._identificador(
                    relacion.origen_tabla
                )
                != nombre_tabla
            ):

                continue

            origen_campo = (
                self._identificador(
                    relacion.origen_campo
                )
            )

            destino_tabla = (
                self._identificador(
                    relacion.destino_tabla
                )
            )

            destino_campo = (
                self._identificador(
                    relacion.destino_campo
                )
            )

            on_delete = (
                relacion.on_delete
                or "restrict"
            ).upper()

            on_update = (
                relacion.on_update
                or "cascade"
            ).upper()

            restricciones.append(
                (
                    f"FOREIGN KEY ({origen_campo}) "
                    f"REFERENCES {destino_tabla}"
                    f"({destino_campo}) "
                    f"ON DELETE {on_delete} "
                    f"ON UPDATE {on_update}"
                )
            )

        lineas = (
            columnas
            + restricciones
        )

        return (
            f"CREATE TABLE IF NOT EXISTS "
            f"{nombre_tabla} (\n    "
            + ",\n    ".join(
                lineas
            )
            + "\n);"
        )

    # =========================================================
    # ÍNDICES
    # =========================================================

    def _indices_sql(
        self,
        modelo: ModeloBaseDatos,
    ) -> list[str]:

        sentencias = []

        for tabla in modelo.tablas:

            tabla_nombre = (
                self._identificador(
                    tabla.nombre
                )
            )

            for indice in tabla.indices:

                campos = [
                    self._identificador(
                        campo
                    )
                    for campo
                    in indice
                ]

                if not campos:
                    continue

                nombre_indice = (
                    "idx_"
                    + tabla_nombre
                    + "_"
                    + "_".join(
                        campos
                    )
                )

                sentencias.append(
                    (
                        f"CREATE INDEX IF NOT EXISTS "
                        f"{nombre_indice} "
                        f"ON {tabla_nombre} "
                        f"({', '.join(campos)});"
                    )
                )

        return sentencias

    # =========================================================
    # SQL COMPLETO
    # =========================================================

    def generar_sql(
        self,
        modelo: ModeloBaseDatos,
    ) -> str:

        motor = (
            modelo.motor
            .strip()
            .lower()
        )

        if motor not in {
            "postgresql",
            "sqlite",
        }:

            raise ValueError(
                (
                    "Motor no soportado todavía: "
                    f"{modelo.motor}"
                )
            )

        bloques = [
            "-- =====================================================",
            "-- ESQUEMA GENERADO POR ATENAS",
            f"-- Motor: {motor}",
            f"-- Base de datos: {modelo.nombre}",
            "-- =====================================================",
            "",
        ]

        if motor == "postgresql":

            bloques.extend([
                "BEGIN;",
                "",
            ])

        for tabla in modelo.tablas:

            bloques.append(
                self._tabla_sql(
                    tabla=tabla,
                    modelo=modelo,
                    motor=motor,
                )
            )

            bloques.append(
                ""
            )

        indices = (
            self._indices_sql(
                modelo
            )
        )

        if indices:

            bloques.append(
                "-- Índices"
            )

            bloques.extend(
                indices
            )

            bloques.append(
                ""
            )

        if motor == "postgresql":

            bloques.append(
                "COMMIT;"
            )

        return "\n".join(
            bloques
        ).strip() + "\n"

    # =========================================================
    # README
    # =========================================================

    @staticmethod
    def _readme(
        modelo: ModeloBaseDatos,
    ) -> str:

        lineas = [
            "# Base de datos",
            "",
            (
                f"Motor seleccionado: "
                f"**{modelo.motor}**"
            ),
            "",
            (
                f"Nombre lógico: "
                f"`{modelo.nombre}`"
            ),
            "",
            "## Estrategia de migraciones",
            "",
            (
                modelo.estrategia_migraciones
                or "Pendiente de definir."
            ),
            "",
            "## Estrategia de respaldo",
            "",
            (
                modelo.estrategia_backup
                or "Pendiente de definir."
            ),
            "",
            "## Integridad",
            "",
        ]

        if modelo.estrategia_integridad:

            lineas.extend(
                (
                    "- "
                    + item
                )
                for item
                in modelo.estrategia_integridad
            )

        else:

            lineas.append(
                "- Pendiente de definir."
            )

        lineas.extend([
            "",
            "## Decisiones",
            "",
        ])

        if modelo.decisiones:

            lineas.extend(
                (
                    "- "
                    + item
                )
                for item
                in modelo.decisiones
            )

        else:

            lineas.append(
                "- Sin decisiones registradas."
            )

        lineas.extend([
            "",
            "## Archivos",
            "",
            "- `schema.sql`: esquema completo.",
            (
                "- `migrations/0001_initial.sql`: "
                "migración inicial."
            ),
            "",
            (
                "> ATENAS genera estos artefactos, "
                "pero no ejecuta migraciones "
                "automáticamente en esta etapa."
            ),
            "",
        ])

        return "\n".join(
            lineas
        )

    # =========================================================
    # GENERAR EN PROYECTO
    # =========================================================

    def generar(
        self,
        carpeta_proyecto: str | Path,
        modelo: ModeloBaseDatos,
    ) -> ResultadoGeneracionBaseDatos:

        raiz = Path(
            carpeta_proyecto
        ).resolve()

        raiz.mkdir(
            parents=True,
            exist_ok=True,
        )

        motor = (
            modelo.motor
            .strip()
            .lower()
        )

        try:

            sql = self.generar_sql(
                modelo
            )

        except Exception as error:

            return ResultadoGeneracionBaseDatos(
                ok=False,
                motor=motor,
                carpeta=str(
                    raiz
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        carpeta_db = (
            raiz
            / "db"
        )

        migraciones = (
            carpeta_db
            / "migrations"
        )

        carpeta_atenas = (
            raiz
            / ".atenas"
        )

        migraciones.mkdir(
            parents=True,
            exist_ok=True,
        )

        carpeta_atenas.mkdir(
            parents=True,
            exist_ok=True,
        )

        schema = (
            carpeta_db
            / "schema.sql"
        )

        migracion_inicial = (
            migraciones
            / "0001_initial.sql"
        )

        readme = (
            carpeta_db
            / "README.md"
        )

        manifiesto = (
            carpeta_atenas
            / "base_datos.json"
        )

        schema.write_text(
            sql,
            encoding="utf-8",
        )

        migracion_inicial.write_text(
            sql,
            encoding="utf-8",
        )

        readme.write_text(
            self._readme(
                modelo
            ),
            encoding="utf-8",
        )

        manifiesto.write_text(
            json.dumps(
                asdict(
                    modelo
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        artefactos = [
            ArtefactoBaseDatos(
                ruta=str(
                    schema
                ),
                tipo="schema_sql",
                contenido=sql,
            ),
            ArtefactoBaseDatos(
                ruta=str(
                    migracion_inicial
                ),
                tipo="migration_sql",
                contenido=sql,
            ),
            ArtefactoBaseDatos(
                ruta=str(
                    readme
                ),
                tipo="documentacion",
                contenido=(
                    readme.read_text(
                        encoding="utf-8"
                    )
                ),
            ),
        ]

        return ResultadoGeneracionBaseDatos(
            ok=True,
            motor=motor,
            carpeta=str(
                carpeta_db
            ),
            artefactos=artefactos,
            manifiesto=str(
                manifiesto
            ),
            resumen=(
                "ATENAS generó el esquema, "
                "la migración inicial y la "
                "documentación de base de datos."
            ),
        )