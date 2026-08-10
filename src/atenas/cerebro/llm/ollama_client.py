from collections.abc import Generator

import ollama

from src.config.settings import LLMSettings


class OllamaClient:

    def __init__(self,config: LLMSettings):
        self.config = config

    def chat_stream(self,mensajes: list[dict[str, str]]) -> Generator[str, None, None]:
        try:
            stream = ollama.chat(
                model=self.config.modelo,
                messages=mensajes,
                stream=True,
                think=self.config.pensar,
                options={
                    "temperature": self.config.temperatura,
                    "num_ctx": self.config.contexto,
                    "num_predict": self.config.max_tokens,
                },
            )

            for chunk in stream:
                contenido = self._extraer_contenido(chunk)

                if contenido:
                    yield contenido

        except Exception as error:

            raise RuntimeError(f"No fue posible comunicarse con Ollama: {error}") from error

    def chat(self,mensajes: list[dict[str, str]]) -> str:
        return "".join(self.chat_stream(mensajes)).strip()

    @staticmethod
    def _extraer_contenido(chunk) -> str:
        if isinstance(chunk, dict):
            return (chunk.get("message", {}).get("content", ""))

        message = getattr(chunk,"message",None)
        if message is None: return ""
        contenido = getattr(message,"content","")
        return contenido or ""