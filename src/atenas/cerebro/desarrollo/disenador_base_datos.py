from __future__ import annotations

import json
import re

from dataclasses import dataclass, field
from typing import Any

from .analista_requisitos import (
    AnalisisRequisitos,
)

from .arquitecto_software import (
    ArquitecturaSoftware,
)


@dataclass
class CampoBD:
    nombre: str
    tipo: str
    nullable: bool = False
    unique: bool = False
    default: str | None = None
    descripcion: str = ""


@dataclass
class TablaBD:
    nombre: str
    descripcion: str

    campos: list[
        CampoBD
    ] = field(
        default_factory=list
    )

    clave_primaria: list[str] = field(
        default_factory=list
    )

    indices: list[
        list[str]
    ] = field(
        default_factory=list
    )


@dataclass
class RelacionBD:
    origen_tabla: str
    origen_campo: str

    destino_tabla: str
    destino_campo: str

    tipo: str

    on_delete: str = "restrict"
    on_update: str = "cascade"


@dataclass
class ModeloBaseDatos:
    motor: str
    nombre: str

    tablas: list[
        TablaBD
    ] = field(
        default_factory=list
    )

    relaciones: list[
        RelacionBD
    ] = field(
        default_factory=list
    )

    decisiones: list[str] = field(
        default_factory=list
    )

    estrategia_migraciones: str = ""
    estrategia_backup: str = ""
    estrategia_integridad: list[str] = field(
        default_factory=list
    )


class DisenadorBaseDatos:
    """
    Diseña un modelo de datos estructurado.

    No crea tablas directamente en una base real.
    Primero genera un modelo verificable.
    """

    def __init__(
        self,
        llm: Any,
    ):
        self.llm = llm

    def _preguntar(
        self,
        mensajes: list[dict],
    ) -> str:

        respuesta = self.llm.chat(
            mensajes
        )

        if isinstance(respuesta, str):
            return respuesta

        if isinstance(respuesta, dict):

            message = (
                respuesta.get("message")
                or {}
            )

            if isinstance(message, dict):

                content = (
                    message.get("content")
                )

                if content:
                    return str(content)

            if respuesta.get("content"):

                return str(
                    respuesta["content"]
                )

        raise RuntimeError(
            "LLM incompatible."
        )

    @staticmethod
    def _extraer_json(
        texto: str,
    ) -> dict:

        texto = (texto or "").strip()

        bloque = re.search(
            r"```(?:json)?\s*(\{.*\})\s*```",
            texto,
            re.DOTALL,
        )

        if bloque:

            texto = bloque.group(1)

        else:

            inicio = texto.find("{")
            fin = texto.rfind("}")

            if inicio < 0 or fin <= inicio:

                raise ValueError(
                    "No se encontró JSON."
                )

            texto = texto[inicio:fin + 1]

        return json.loads(texto)

    def diseñar(
        self,
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
    ) -> ModeloBaseDatos | None:

        if not analisis.necesita_base_datos:
            return None

        system = """
Eres el diseñador de bases de datos de ATENAS.

Debes crear un modelo estructurado, normalizado y eficiente.

Reglas:
- evita duplicación innecesaria;
- usa claves primarias claras;
- agrega índices solo donde aporten valor;
- representa relaciones explícitamente;
- evita datos derivados si pueden calcularse;
- separa autenticación de datos de negocio cuando corresponda;
- contempla auditoría si el sistema lo necesita;
- usa nombres consistentes;
- piensa en integridad referencial;
- define migraciones y respaldo.

Devuelve SOLO JSON:

{
  "motor": "postgresql",
  "nombre": "app_db",
  "tablas": [
    {
      "nombre": "usuarios",
      "descripcion": "...",
      "campos": [
        {
          "nombre": "id",
          "tipo": "uuid",
          "nullable": false,
          "unique": true,
          "default": null,
          "descripcion": "..."
        }
      ],
      "clave_primaria": ["id"],
      "indices": [["email"]]
    }
  ],
  "relaciones": [
    {
      "origen_tabla": "pedidos",
      "origen_campo": "usuario_id",
      "destino_tabla": "usuarios",
      "destino_campo": "id",
      "tipo": "muchos_a_uno",
      "on_delete": "restrict",
      "on_update": "cascade"
    }
  ],
  "decisiones": [],
  "estrategia_migraciones": "...",
  "estrategia_backup": "...",
  "estrategia_integridad": []
}
""".strip()

        entrada = {
            "analisis": {
                "nombre":
                    analisis.nombre_proyecto,

                "entidades":
                    analisis.entidades_negocio,

                "funcionales": [
                    req.descripcion
                    for req
                    in analisis
                    .requisitos_funcionales
                ],

                "no_funcionales": [
                    req.descripcion
                    for req
                    in analisis
                    .requisitos_no_funcionales
                ],
            },

            "arquitectura": {
                "estilo":
                    arquitectura.estilo,

                "base_datos":
                    arquitectura.base_datos,

                "tipo_solucion":
                    arquitectura.tipo_solucion,
            },
        }

        datos = self._extraer_json(
            self._preguntar([
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        entrada,
                        ensure_ascii=False,
                        indent=2,
                    ),
                },
            ])
        )

        tablas = []

        for item in datos.get(
            "tablas",
            [],
        ):

            campos = []

            for campo in item.get(
                "campos",
                [],
            ):

                campos.append(
                    CampoBD(
                        nombre=str(
                            campo.get(
                                "nombre",
                                "",
                            )
                        ),
                        tipo=str(
                            campo.get(
                                "tipo",
                                "",
                            )
                        ),
                        nullable=bool(
                            campo.get(
                                "nullable",
                                False,
                            )
                        ),
                        unique=bool(
                            campo.get(
                                "unique",
                                False,
                            )
                        ),
                        default=(
                            str(
                                campo[
                                    "default"
                                ]
                            )
                            if (
                                campo.get(
                                    "default"
                                )
                                is not None
                            )
                            else None
                        ),
                        descripcion=str(
                            campo.get(
                                "descripcion",
                                "",
                            )
                        ),
                    )
                )

            tablas.append(
                TablaBD(
                    nombre=str(
                        item.get(
                            "nombre",
                            "",
                        )
                    ),
                    descripcion=str(
                        item.get(
                            "descripcion",
                            "",
                        )
                    ),
                    campos=campos,
                    clave_primaria=[
                        str(campo)
                        for campo
                        in item.get(
                            "clave_primaria",
                            [],
                        )
                    ],
                    indices=[
                        [
                            str(campo)
                            for campo
                            in indice
                        ]
                        for indice
                        in item.get(
                            "indices",
                            [],
                        )
                    ],
                )
            )

        relaciones = [
            RelacionBD(
                origen_tabla=str(
                    rel.get(
                        "origen_tabla",
                        "",
                    )
                ),
                origen_campo=str(
                    rel.get(
                        "origen_campo",
                        "",
                    )
                ),
                destino_tabla=str(
                    rel.get(
                        "destino_tabla",
                        "",
                    )
                ),
                destino_campo=str(
                    rel.get(
                        "destino_campo",
                        "",
                    )
                ),
                tipo=str(
                    rel.get(
                        "tipo",
                        "",
                    )
                ),
                on_delete=str(
                    rel.get(
                        "on_delete",
                        "restrict",
                    )
                ),
                on_update=str(
                    rel.get(
                        "on_update",
                        "cascade",
                    )
                ),
            )
            for rel
            in datos.get(
                "relaciones",
                [],
            )
            if isinstance(
                rel,
                dict,
            )
        ]

        return ModeloBaseDatos(
            motor=str(
                datos.get(
                    "motor",
                    "postgresql",
                )
            ),
            nombre=str(
                datos.get(
                    "nombre",
                    "app_db",
                )
            ),
            tablas=tablas,
            relaciones=relaciones,
            decisiones=[
                str(item)
                for item
                in datos.get(
                    "decisiones",
                    [],
                )
            ],
            estrategia_migraciones=str(
                datos.get(
                    "estrategia_migraciones",
                    "",
                )
            ),
            estrategia_backup=str(
                datos.get(
                    "estrategia_backup",
                    "",
                )
            ),
            estrategia_integridad=[
                str(item)
                for item
                in datos.get(
                    "estrategia_integridad",
                    [],
                )
            ],
        )