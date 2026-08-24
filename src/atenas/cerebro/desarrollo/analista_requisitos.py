from __future__ import annotations

import json
import re

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TipoSolucion(str, Enum):
    WEB = "web"
    ESCRITORIO = "escritorio"
    MOVIL = "movil"
    API = "api"
    CLI = "cli"
    EMBEBIDO = "embebido"
    IOT = "iot"
    HIBRIDO = "hibrido"
    DESCONOCIDO = "desconocido"


@dataclass
class Requisito:
    id: str
    descripcion: str
    prioridad: str = "media"
    obligatorio: bool = True


@dataclass
class AnalisisRequisitos:
    nombre_proyecto: str
    tipo_solucion: TipoSolucion
    resumen: str

    actores: list[str] = field(default_factory=list)
    requisitos_funcionales: list[Requisito] = field(default_factory=list)
    requisitos_no_funcionales: list[Requisito] = field(default_factory=list)

    entidades_negocio: list[str] = field(default_factory=list)
    integraciones: list[str] = field(default_factory=list)
    restricciones: list[str] = field(default_factory=list)

    necesita_base_datos: bool = False
    necesita_autenticacion: bool = False
    necesita_roles: bool = False
    necesita_api: bool = False
    necesita_archivos: bool = False
    necesita_tiempo_real: bool = False
    necesita_offline: bool = False

    complejidad: str = "media"
    riesgos_iniciales: list[str] = field(default_factory=list)
    preguntas_abiertas: list[str] = field(default_factory=list)


class AnalistaRequisitos:
    """
    Convierte una necesidad general en requisitos estructurados.

    El analista NO elige todavía tecnologías concretas.
    Esa responsabilidad corresponde al ArquitectoSoftware.
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

        if hasattr(self.llm, "chat"):

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

        datos = json.loads(texto)

        if not isinstance(datos, dict):

            raise ValueError(
                "Respuesta JSON inválida."
            )

        return datos

    @staticmethod
    def _requisitos(
        items: list[dict] | None,
        prefijo: str,
    ) -> list[Requisito]:

        resultado = []

        for indice, item in enumerate(
            items or [],
            start=1,
        ):

            if not isinstance(item, dict):
                continue

            descripcion = str(
                item.get("descripcion", "")
                or ""
            ).strip()

            if not descripcion:
                continue

            resultado.append(
                Requisito(
                    id=str(
                        item.get(
                            "id",
                            f"{prefijo}-{indice:03d}",
                        )
                    ),
                    descripcion=descripcion,
                    prioridad=str(
                        item.get(
                            "prioridad",
                            "media",
                        )
                    ),
                    obligatorio=bool(
                        item.get(
                            "obligatorio",
                            True,
                        )
                    ),
                )
            )

        return resultado

    def analizar(
        self,
        descripcion: str,
    ) -> AnalisisRequisitos:

        system = """
Eres el analista de requisitos de ATENAS.

Tu trabajo es transformar una necesidad de software en una
especificación estructurada antes de elegir tecnologías.

Debes determinar el tipo de solución:
- web
- escritorio
- movil
- api
- cli
- embebido
- iot
- hibrido
- desconocido

Devuelve SOLO JSON válido con esta forma:

{
  "nombre_proyecto": "...",
  "tipo_solucion": "web",
  "resumen": "...",
  "actores": [],
  "requisitos_funcionales": [
    {
      "id": "RF-001",
      "descripcion": "...",
      "prioridad": "alta",
      "obligatorio": true
    }
  ],
  "requisitos_no_funcionales": [],
  "entidades_negocio": [],
  "integraciones": [],
  "restricciones": [],
  "necesita_base_datos": true,
  "necesita_autenticacion": true,
  "necesita_roles": true,
  "necesita_api": true,
  "necesita_archivos": false,
  "necesita_tiempo_real": false,
  "necesita_offline": false,
  "complejidad": "baja|media|alta|muy_alta",
  "riesgos_iniciales": [],
  "preguntas_abiertas": []
}

No elijas frameworks.
No inventes requisitos que contradigan la solicitud.
""".strip()

        respuesta = self._preguntar([
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": descripcion,
            },
        ])

        datos = self._extraer_json(
            respuesta
        )

        try:

            tipo = TipoSolucion(
                str(
                    datos.get(
                        "tipo_solucion",
                        "desconocido",
                    )
                ).strip().lower()
            )

        except ValueError:

            tipo = TipoSolucion.DESCONOCIDO

        return AnalisisRequisitos(
            nombre_proyecto=str(
                datos.get(
                    "nombre_proyecto",
                    "Proyecto",
                )
            ),
            tipo_solucion=tipo,
            resumen=str(
                datos.get(
                    "resumen",
                    "",
                )
            ),
            actores=[
                str(item)
                for item
                in datos.get(
                    "actores",
                    [],
                )
            ],
            requisitos_funcionales=(
                self._requisitos(
                    datos.get(
                        "requisitos_funcionales"
                    ),
                    "RF",
                )
            ),
            requisitos_no_funcionales=(
                self._requisitos(
                    datos.get(
                        "requisitos_no_funcionales"
                    ),
                    "RNF",
                )
            ),
            entidades_negocio=[
                str(item)
                for item
                in datos.get(
                    "entidades_negocio",
                    [],
                )
            ],
            integraciones=[
                str(item)
                for item
                in datos.get(
                    "integraciones",
                    [],
                )
            ],
            restricciones=[
                str(item)
                for item
                in datos.get(
                    "restricciones",
                    [],
                )
            ],
            necesita_base_datos=bool(
                datos.get(
                    "necesita_base_datos",
                    False,
                )
            ),
            necesita_autenticacion=bool(
                datos.get(
                    "necesita_autenticacion",
                    False,
                )
            ),
            necesita_roles=bool(
                datos.get(
                    "necesita_roles",
                    False,
                )
            ),
            necesita_api=bool(
                datos.get(
                    "necesita_api",
                    False,
                )
            ),
            necesita_archivos=bool(
                datos.get(
                    "necesita_archivos",
                    False,
                )
            ),
            necesita_tiempo_real=bool(
                datos.get(
                    "necesita_tiempo_real",
                    False,
                )
            ),
            necesita_offline=bool(
                datos.get(
                    "necesita_offline",
                    False,
                )
            ),
            complejidad=str(
                datos.get(
                    "complejidad",
                    "media",
                )
            ),
            riesgos_iniciales=[
                str(item)
                for item
                in datos.get(
                    "riesgos_iniciales",
                    [],
                )
            ],
            preguntas_abiertas=[
                str(item)
                for item
                in datos.get(
                    "preguntas_abiertas",
                    [],
                )
            ],
        )