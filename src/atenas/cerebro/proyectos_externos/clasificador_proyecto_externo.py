from __future__ import annotations

import json
import re

from dataclasses import dataclass
from typing import Any

from .espacios_trabajo import (
    TipoProyectoExterno,
)


@dataclass
class ClasificacionProyectoExterno:
    tipo: TipoProyectoExterno
    nombre: str
    cliente: str | None
    lenguaje_sugerido: str | None
    necesita_pdf: bool
    confianza: float
    motivo: str


class ClasificadorProyectoExterno:
    """
    Permite que ATENAS infiera:
    - si es un proyecto personal o de cliente;
    - el nombre;
    - cliente;
    - lenguaje probable;
    - si conviene documentación PDF.

    Así el usuario no necesita indicar una ruta manualmente.
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

        if hasattr(
            self.llm,
            "chat",
        ):

            respuesta = self.llm.chat(
                mensajes
            )

            if isinstance(
                respuesta,
                str,
            ):
                return respuesta

            if isinstance(
                respuesta,
                dict,
            ):

                message = (
                    respuesta.get(
                        "message"
                    )
                    or {}
                )

                if isinstance(
                    message,
                    dict,
                ):

                    content = (
                        message.get(
                            "content"
                        )
                    )

                    if content:
                        return str(
                            content
                        )

                content = respuesta.get(
                    "content"
                )

                if content:
                    return str(
                        content
                    )

        raise RuntimeError(
            "LLM incompatible."
        )

    @staticmethod
    def _extraer_json(
        texto: str,
    ) -> dict:

        texto = (
            texto
            or ""
        ).strip()

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

            if (
                inicio < 0
                or fin <= inicio
            ):

                raise ValueError(
                    "No se encontró JSON."
                )

            texto = texto[
                inicio:
                fin + 1
            ]

        return json.loads(
            texto
        )

    def clasificar(
        self,
        descripcion: str,
    ) -> ClasificacionProyectoExterno:

        system = """
Clasifica una solicitud de proyecto para ATENAS.

ATENAS debe decidir sola dónde organizar el proyecto.

Devuelve SOLO JSON:

{
  "tipo": "personal|cliente|experimento|documentacion|otro",
  "nombre": "nombre breve del proyecto",
  "cliente": null,
  "lenguaje_sugerido": "python",
  "necesita_pdf": true,
  "confianza": 0.95,
  "motivo": "..."
}

Usa "cliente" cuando la solicitud hable de un trabajo para un
cliente, empresa, organización o tercero identificable.

Los proyectos de cliente deben quedar separados de los personales.
""".strip()

        try:

            texto = self._preguntar([
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
                texto
            )

            tipo = TipoProyectoExterno(
                str(
                    datos.get(
                        "tipo",
                        "otro",
                    )
                ).strip().lower()
            )

            return ClasificacionProyectoExterno(
                tipo=tipo,
                nombre=str(
                    datos.get(
                        "nombre",
                        "Proyecto"
                    )
                ).strip(),
                cliente=(
                    str(
                        datos[
                            "cliente"
                        ]
                    ).strip()
                    if datos.get(
                        "cliente"
                    )
                    else None
                ),
                lenguaje_sugerido=(
                    str(
                        datos[
                            "lenguaje_sugerido"
                        ]
                    ).strip()
                    if datos.get(
                        "lenguaje_sugerido"
                    )
                    else None
                ),
                necesita_pdf=bool(
                    datos.get(
                        "necesita_pdf",
                        True,
                    )
                ),
                confianza=float(
                    datos.get(
                        "confianza",
                        0.7,
                    )
                    or 0.7
                ),
                motivo=str(
                    datos.get(
                        "motivo",
                        "",
                    )
                ),
            )

        except Exception:

            texto = (
                descripcion
                .lower()
            )

            if (
                "cliente"
                in texto
            ):

                tipo = (
                    TipoProyectoExterno
                    .CLIENTE
                )

            else:

                tipo = (
                    TipoProyectoExterno
                    .PERSONAL
                )

            return ClasificacionProyectoExterno(
                tipo=tipo,
                nombre="Proyecto",
                cliente=None,
                lenguaje_sugerido=None,
                necesita_pdf=True,
                confianza=0.4,
                motivo=(
                    "Clasificación heurística "
                    "de respaldo."
                ),
            )