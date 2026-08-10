from collections.abc import Generator

from src.atenas.cerebro.historial import HistorialConversacion
from src.atenas.cerebro.llm.ollama_client import OllamaClient
from src.atenas.cerebro.prompts import SYSTEM_PROMPT_BASE
from src.config.settings import settings

class NucleoConversacional: 

    def __init__(self):
        self.historial = HistorialConversacion(max_turnos=settings.llm.max_turnos_historial)
        self.llm = OllamaClient(config=settings.llm)

    def _crear_mensajes(self, mensaje_usuarios: str) -> list[dict[str,str]]:
        mensajes = [{"role": "system","content": SYSTEM_PROMPT_BASE,}]
        mensajes.extend(self.historial.obtener())
        mensajes.append({"role": "user","content": mensaje_usuarios.strip(),})
        return mensajes

    def responder_stream(self, mensaje_usuario: str) -> Generator[str, None, None]:
        mensaje_usuario = mensaje_usuario.strip()
        if not mensaje_usuario: return
        mensajes = self._crear_mensajes( mensaje_usuario)
        respuesta_completa = ""
        for fragmento in self.llm.chat_stream(mensajes):
            respuesta_completa += fragmento
            yield fragmento
        respuesta_completa = (respuesta_completa.strip())
        self.historial.agregar_usuario( mensaje_usuario)
        self.historial.agregar_asistente(respuesta_completa)

    def responder(self,mensaje_usuario: str) -> str:
        return "".join(self.responder_stream(mensaje_usuario))

    def limpiar_conversacion(self) -> None:

        self.historial.limpiar()

    @property
    def modelo(self) -> str:
        return settings.llm.modelo