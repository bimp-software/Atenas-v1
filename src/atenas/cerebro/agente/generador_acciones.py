from __future__ import annotations

import json

from src.atenas.cerebro.llm.ollama_client import OllamaClient
from src.config.settings import settings


class GeneradorAcciones:
    """
    Usa el LLM para transformar una necesidad
    en argumentos concretos para una herramienta.
    """

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

    def generar_texto_nota(
        self,
        mensaje_usuario: str,
        descripcion_necesidad: str,
    ) -> str:

        mensajes = [
            {
                "role": "system",
                "content": (
                    "Eres el módulo de planificación de ATENAS. "
                    "Debes redactar únicamente el contenido final "
                    "que ATENAS debería escribir en una nota. "
                    "No expliques lo que haces. "
                    "No uses JSON. "
                    "No agregues saludos. "
                    "Sé claro, natural y breve."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Mensaje original del usuario:\n"
                    f"{mensaje_usuario}\n\n"
                    f"Necesidad detectada:\n"
                    f"{descripcion_necesidad}\n\n"
                    "Redacta la nota."
                ),
            },
        ]

        return self.llm.chat(
            mensajes
        ).strip()