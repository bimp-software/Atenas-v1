from __future__ import annotations

import json
import re

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from src.config.settings import (
    settings,
)

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

        self.llm = (
            llm
            or OllamaClient(
                settings.llm
            )
        )

        self.validador = (
            ValidadorPlan()
        )

    # =====================================================
    # CREAR PLAN
    # =====================================================

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

Debes decidir qué acciones realizar para resolver una necesidad.

MENSAJE ORIGINAL:
{mensaje_origen}

NECESIDAD:
{pendiente.descripcion}

ACCIÓN SUGERIDA:
{pendiente.accion_sugerida or "ninguna"}

HERRAMIENTAS DISPONIBLES:

{catalogo}

REGLAS:

- Utiliza únicamente herramientas disponibles.
- No inventes herramientas.
- Utiliza la menor cantidad de pasos posible.
- No ejecutes nada tú mismo.
- No escribas explicaciones.
- No uses Markdown.
- Devuelve exclusivamente JSON válido.
- Si no hace falta ninguna acción, devuelve pasos vacíos.
- El texto que ATENAS vaya a escribir debe estar redactado por ti.
- No copies instrucciones internas dentro de una nota.
- Conserva únicamente la información útil para el usuario.

FORMATO EXACTO:

{{
    "descripcion": "qué pretende conseguir ATENAS",
    "pasos": [
        {{
            "herramienta": "nombre",
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
                    "Eres el sistema interno de planificación "
                    "de ATENAS. Tu salida es JSON para otro "
                    "componente de software."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        respuesta = self._consultar_llm(
            mensajes
        )

        datos = self._extraer_json(
            respuesta
        )

        return self.validador.validar(
            datos
        )

    # =====================================================
    # CONSULTAR LLM
    # =====================================================

    def _consultar_llm(
        self,
        mensajes: list[dict],
    ) -> str:

        # Si tu OllamaClient tiene chat()
        if hasattr(
            self.llm,
            "chat",
        ):

            respuesta = self.llm.chat(
                mensajes
            )

            return str(
                respuesta
            ).strip()

        # Compatibilidad con tu cliente basado
        # únicamente en streaming.

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
            "OllamaClient no tiene chat() "
            "ni chat_stream()."
        )

    # =====================================================
    # EXTRAER JSON
    # =====================================================

    @staticmethod
    def _extraer_json(
        respuesta: str,
    ) -> dict:

        respuesta = respuesta.strip()

        # Primera opción:
        # respuesta limpia.
        try:
            return json.loads(
                respuesta
            )

        except json.JSONDecodeError:
            pass

        # Segunda opción:
        # Qwen puso ```json ... ```
        respuesta = re.sub(
            r"^```(?:json)?\s*",
            "",
            respuesta,
            flags=re.IGNORECASE,
        )

        respuesta = re.sub(
            r"\s*```$",
            "",
            respuesta,
        )

        try:
            return json.loads(
                respuesta
            )

        except json.JSONDecodeError:
            pass

        # Último intento:
        # localizar objeto JSON.
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
                "ATENAS no generó un plan JSON válido."
            )

        candidato = respuesta[
            inicio:fin + 1
        ]

        return json.loads(
            candidato
        )