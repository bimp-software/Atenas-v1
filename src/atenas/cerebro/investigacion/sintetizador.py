from __future__ import annotations

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)


class SintetizadorInvestigacion:

    def __init__(
        self,
        llm: OllamaClient,
    ):
        self.llm = llm

    def sintetizar(
        self,
        consulta: str,
        resultados: list[dict],
    ) -> str:

        if not resultados:
            return ""

        fuentes = []

        for numero, resultado in enumerate(
            resultados,
            start=1,
        ):

            fuentes.append(
                f"""
FUENTE {numero}

Título:
{resultado.get("titulo", "")}

URL:
{resultado.get("url", "")}

Información:
{resultado.get("fragmento", "")}
""".strip()
            )

        contexto = "\n\n".join(
            fuentes
        )

        mensajes = [
            {
                "role": "system",
                "content": (
                    "Eres el módulo de investigación "
                    "de ATENAS. Analiza información "
                    "obtenida de Internet. "
                    "No inventes datos. "
                    "Distingue claramente información "
                    "respaldada de inferencias. "
                    "Resume de forma natural y útil."
                ),
            },
            {
                "role": "user",
                "content": f"""
CONSULTA:

{consulta}

RESULTADOS DE INVESTIGACIÓN:

{contexto}

Genera una respuesta útil para el usuario.

No copies fragmentos completos.
Integra la información.
Si los resultados son insuficientes,
indícalo claramente.
""".strip(),
            },
        ]

        if hasattr(
            self.llm,
            "chat",
        ):

            return str(
                self.llm.chat(
                    mensajes
                )
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
            "El cliente LLM no puede "
            "realizar síntesis."
        )