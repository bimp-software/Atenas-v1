from __future__ import annotations

import json
import re

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from src.config.settings import settings

from .catalogo_herramientas import (
    catalogo_para_llm,
)

from .pendientes import Pendiente

from .planificador import Plan

from .validador_plan import (
    ValidadorPlan,
)


class PlanificadorInteligente:

    def __init__(
        self,
        llm: OllamaClient | None = None,
    ):
        # Preferimos recibir el mismo LLM
        # que utiliza NucleoConversacional.
        self.llm = (
            llm
            if llm is not None
            else OllamaClient(
                config=settings.llm
            )
        )

        self.validador = (
            ValidadorPlan()
        )

    # =========================================================
    # CREAR PLAN
    # =========================================================

    def crear_plan(
        self,
        pendiente: Pendiente,
    ) -> Plan:

        catalogo = (
            catalogo_para_llm()
        )

        mensaje_origen = (
            pendiente.mensaje_origen
            or pendiente.descripcion
        )

        prompt = f"""
Eres el planificador interno de ATENAS.

Tu trabajo consiste en decidir si ATENAS debe realizar
una acción y, cuando sea necesario, construir un plan
utilizando exclusivamente las herramientas permitidas.

MENSAJE ORIGINAL DEL USUARIO:
{mensaje_origen}

NECESIDAD DETECTADA:
{pendiente.descripcion}

TIPO DE NECESIDAD:
{getattr(pendiente, "tipo", "no especificado")}

ACCIÓN SUGERIDA:
{pendiente.accion_sugerida or "ninguna"}

HERRAMIENTAS DISPONIBLES:

{catalogo}

REGLAS OBLIGATORIAS:

- Decide por ti mismo qué herramienta o combinación de
  herramientas resuelve mejor la necesidad.

- Utiliza únicamente herramientas del catálogo.

- Nunca inventes herramientas.

- Usa la menor cantidad de pasos posible.

- Si una sola herramienta resuelve el objetivo,
  utiliza solamente esa herramienta.

- No ejecutes acciones tú mismo.

- Devuelve exclusivamente JSON válido.

- No uses Markdown.

- No agregues texto fuera del JSON.

- Si no es necesario hacer nada, devuelve una lista
  de pasos vacía.

- Cuando una herramienta requiera contenido textual,
  redacta tú mismo el contenido final.

- No copies automáticamente el mensaje del usuario.

- Resume y organiza la información cuando eso produzca
  un resultado más útil.

- Conserva nombres, números, componentes técnicos y
  decisiones importantes.

- No inventes hechos ni decisiones.

- Nunca incluyas las instrucciones internas de este prompt
  dentro de una nota.

FORMATO EXACTO:

{{
    "descripcion": "objetivo concreto del plan",
    "pasos": [
        {{
            "herramienta": "nombre_exacto",
            "argumentos": {{
                "argumento": "valor"
            }}
        }}
    ]
}}
""".strip()

        mensajes = [
            {
                "role": "system",
                "content": (
                    "Eres el componente interno de "
                    "planificación de ATENAS. "
                    "Respondes únicamente con JSON válido."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        respuesta = (
            self._consultar_llm(
                mensajes
            )
        )

        datos = self._extraer_json(
            respuesta
        )

        return self.validador.validar(
            datos
        )

    # =========================================================
    # CONSULTAR LLM
    # =========================================================

    def _consultar_llm(
        self,
        mensajes: list[dict],
    ) -> str:

        if hasattr(
            self.llm,
            "chat",
        ):
            respuesta = (
                self.llm.chat(
                    mensajes
                )
            )

            return str(
                respuesta
            ).strip()

        if hasattr(
            self.llm,
            "chat_stream",
        ):

            partes = []

            for fragmento in (
                self.llm.chat_stream(
                    mensajes
                )
            ):
                partes.append(
                    str(fragmento)
                )

            return "".join(
                partes
            ).strip()

        raise RuntimeError(
            "OllamaClient no posee "
            "chat() ni chat_stream()."
        )

    # =========================================================
    # EXTRAER JSON
    # =========================================================

    @staticmethod
    def _extraer_json(
        respuesta: str,
    ) -> dict:

        if not respuesta:
            raise ValueError(
                "El planificador devolvió "
                "una respuesta vacía."
            )

        respuesta = respuesta.strip()

        # ---------------------------------------------
        # JSON directo
        # ---------------------------------------------

        try:
            datos = json.loads(
                respuesta
            )

            if not isinstance(
                datos,
                dict,
            ):
                raise ValueError(
                    "El plan generado no es "
                    "un objeto JSON."
                )

            return datos

        except json.JSONDecodeError:
            pass

        # ---------------------------------------------
        # Bloque ```json
        # ---------------------------------------------

        limpio = re.sub(
            r"^```(?:json)?\s*",
            "",
            respuesta,
            flags=re.IGNORECASE,
        )

        limpio = re.sub(
            r"\s*```$",
            "",
            limpio,
        )

        try:
            datos = json.loads(
                limpio
            )

            if isinstance(
                datos,
                dict,
            ):
                return datos

        except json.JSONDecodeError:
            pass

        # ---------------------------------------------
        # Buscar primer {...}
        # ---------------------------------------------

        inicio = respuesta.find(
            "{"
        )

        fin = respuesta.rfind(
            "}"
        )

        if (
            inicio == -1
            or fin == -1
            or fin <= inicio
        ):
            raise ValueError(
                "ATENAS no generó "
                "un plan JSON válido."
            )

        candidato = respuesta[
            inicio:fin + 1
        ]

        try:

            datos = json.loads(
                candidato
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                "El JSON generado por el "
                "planificador no es válido: "
                f"{error}"
            ) from error

        if not isinstance(
            datos,
            dict,
        ):
            raise ValueError(
                "El plan debe ser "
                "un objeto JSON."
            )

        return datos