from __future__ import annotations

import json
import re

from dataclasses import asdict, dataclass, field
from typing import Any

from .analista_requisitos import (
    AnalisisRequisitos,
    TipoSolucion,
)


@dataclass
class ComponenteArquitectura:
    nombre: str
    responsabilidad: str
    tecnologia: str
    lenguaje: str
    depende_de: list[str] = field(
        default_factory=list
    )


@dataclass
class ArquitecturaSoftware:
    estilo: str
    tipo_solucion: str

    frontend: dict | None = None
    backend: dict | None = None
    desktop: dict | None = None
    movil: dict | None = None
    embebido: dict | None = None

    api: dict | None = None
    base_datos: dict | None = None
    cache: dict | None = None
    colas: dict | None = None

    autenticacion: dict | None = None

    componentes: list[
        ComponenteArquitectura
    ] = field(
        default_factory=list
    )

    despliegue: dict = field(
        default_factory=dict
    )

    pruebas: dict = field(
        default_factory=dict
    )

    seguridad: list[str] = field(
        default_factory=list
    )

    decisiones: list[str] = field(
        default_factory=list
    )


class ArquitectoSoftware:
    """
    Decide la arquitectura y las tecnologías a partir de
    requisitos ya analizados.

    Debe elegir según:
    - tipo de solución;
    - complejidad;
    - mantenimiento;
    - rendimiento;
    - despliegue;
    - requisitos de datos;
    - tiempo real;
    - offline;
    - seguridad.
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
    ) -> ArquitecturaSoftware:

        system = """
Eres el arquitecto de software de ATENAS.

Debes elegir una arquitectura eficiente y mantenible a partir
de requisitos ya definidos.

Reglas:
- No uses microservicios por defecto.
- Para proyectos pequeños/medios prefiere monolito modular.
- Usa microservicios solo si existe una necesidad real.
- Elige tecnologías según el tipo de solución.
- Considera escalabilidad, seguridad, mantenimiento y costo.
- Si necesita datos relacionales complejos, prioriza PostgreSQL.
- Si es local/offline y pequeño, SQLite puede ser suficiente.
- Si es escritorio, decide entre tecnologías nativas,
  web embebida o multiplataforma según requisitos.
- Si es web, separa frontend/backend solo si aporta valor.
- Define estrategia de pruebas.

Devuelve SOLO JSON:

{
  "estilo": "monolito_modular",
  "tipo_solucion": "web",
  "frontend": null,
  "backend": null,
  "desktop": null,
  "movil": null,
  "embebido": null,
  "api": null,
  "base_datos": null,
  "cache": null,
  "colas": null,
  "autenticacion": null,
  "componentes": [
    {
      "nombre": "...",
      "responsabilidad": "...",
      "tecnologia": "...",
      "lenguaje": "...",
      "depende_de": []
    }
  ],
  "despliegue": {},
  "pruebas": {},
  "seguridad": [],
  "decisiones": []
}
""".strip()

        respuesta = self._preguntar([
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": json.dumps(
                    asdict(
                        analisis
                    ),
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                ),
            },
        ])

        datos = self._extraer_json(
            respuesta
        )

        componentes = []

        for item in datos.get(
            "componentes",
            [],
        ):

            if not isinstance(item, dict):
                continue

            componentes.append(
                ComponenteArquitectura(
                    nombre=str(
                        item.get(
                            "nombre",
                            "",
                        )
                    ),
                    responsabilidad=str(
                        item.get(
                            "responsabilidad",
                            "",
                        )
                    ),
                    tecnologia=str(
                        item.get(
                            "tecnologia",
                            "",
                        )
                    ),
                    lenguaje=str(
                        item.get(
                            "lenguaje",
                            "",
                        )
                    ),
                    depende_de=[
                        str(dep)
                        for dep
                        in item.get(
                            "depende_de",
                            [],
                        )
                    ],
                )
            )

        return ArquitecturaSoftware(
            estilo=str(
                datos.get(
                    "estilo",
                    "monolito_modular",
                )
            ),
            tipo_solucion=str(
                datos.get(
                    "tipo_solucion",
                    analisis.tipo_solucion.value,
                )
            ),
            frontend=datos.get(
                "frontend"
            ),
            backend=datos.get(
                "backend"
            ),
            desktop=datos.get(
                "desktop"
            ),
            movil=datos.get(
                "movil"
            ),
            embebido=datos.get(
                "embebido"
            ),
            api=datos.get(
                "api"
            ),
            base_datos=datos.get(
                "base_datos"
            ),
            cache=datos.get(
                "cache"
            ),
            colas=datos.get(
                "colas"
            ),
            autenticacion=datos.get(
                "autenticacion"
            ),
            componentes=componentes,
            despliegue=(
                datos.get(
                    "despliegue",
                    {},
                )
                or {}
            ),
            pruebas=(
                datos.get(
                    "pruebas",
                    {},
                )
                or {}
            ),
            seguridad=[
                str(item)
                for item
                in datos.get(
                    "seguridad",
                    [],
                )
            ],
            decisiones=[
                str(item)
                for item
                in datos.get(
                    "decisiones",
                    [],
                )
            ],
        )