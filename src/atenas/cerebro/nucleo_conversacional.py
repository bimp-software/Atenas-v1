from collections.abc import Generator

from src.atenas.cerebro.estado import estado_atenas
from src.atenas.cerebro.historial import HistorialConversacion
from src.atenas.cerebro.llm.ollama_client import OllamaClient
from src.atenas.cerebro.prompts import SYSTEM_PROMPT_BASE
from src.atenas.cerebro.voz import (Hablante, hablar_stream, EscuchaVoz)

from src.atenas.cerebro.memoria.hipocampo import HipocampoDigital, Experiencia
from src.atenas.cerebro.memoria.clasificador import ClasificadorMemoria
from src.atenas.cerebro.memoria.consolidador import ConsolidadorMemoria
from src.atenas.cerebro.memoria.recuperador import RecuperadorMemoria

from src.config.settings import settings

class NucleoConversacional: 

    def __init__(self):
        self.historial = HistorialConversacion(max_turnos=settings.llm.max_turnos_historial)
        self.llm = OllamaClient(config=settings.llm)

        self.hablante = Hablante()

        estado_atenas.capacidades.voz_salida = (self.hablante.disponible)

        try:
            self.escucha = EscuchaVoz()
            estado_atenas.capacidades.voz_entrada = True

        except Exception as error:
            print(f"[ATENAS] No fue posible iniciar el reconocimiento de voz: {error}")
            self.escucha = None
            estado_atenas.capacidades.voz_entrada = False

        self.clasificador_memoria = ClasificadorMemoria()
        self.consolidador_memoria = ConsolidadorMemoria()
        self.recuperador_memoria = RecuperadorMemoria()

        self.hipocampo = HipocampoDigital(
            clasificador=self.clasificador_memoria,
            consolidador=self.consolidador_memoria,
            recuperador=self.recuperador_memoria,
        )

        estado_atenas.capacidades.memoria_persistente = True

    def escuchar(self, duracion: float = 5.0) -> str:
        if self.escucha is None: return ""
        self.hablante.esperar()
        return self.escucha.escuchar(duracion=duracion)

    def _crear_mensajes(self,mensaje_usuario: str) -> list[dict[str, str]]:
        memoria_contexto = (self.recuperador_memoria.contexto_para_llm(mensaje_usuario))
        system_prompt = (SYSTEM_PROMPT_BASE)

        if memoria_contexto:
            system_prompt += ("\n\n" + memoria_contexto)

        mensajes = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        mensajes.extend(self.historial.obtener())

        mensajes.append({"role": "user","content": mensaje_usuario.strip(),})

        return mensajes

    def responder_stream(self, mensaje_usuario: str,usar_voz: bool = True) -> Generator[str, None, None]:
        mensaje_usuario = mensaje_usuario.strip()
        if not mensaje_usuario: return
        mensajes = self._crear_mensajes( mensaje_usuario)
        respuesta_completa = ""
        stream_llm = self.llm.chat_stream(mensajes)
        if (usar_voz and self.hablante.disponible):
            stream_salida = hablar_stream(stream_llm,self.hablante,)
        else:
            stream_salida = stream_llm

        for fragmento in stream_salida:
            respuesta_completa += fragmento
            yield fragmento

        self.historial.agregar_usuario( mensaje_usuario)
        self.historial.agregar_asistente(respuesta_completa)

        try:
            experiencia = Experiencia(
                contenido=mensaje_usuario,
                fuente="usuario",
                importancia=0.5,
                confianza=0.85,
                contexto="conversacion",
            )

            resultado_memoria = (self.hipocampo.procesar(experiencia))
        except Exception as error:
            print("[ATENAS][MEMORIA] " f"No fue posible procesar memoria: {error}")


    def responder(self,mensaje_usuario: str, usar_voz: bool) -> str:
        return "".join(self.responder_stream(mensaje_usuario, usar_voz))

    def limpiar_conversacion(self) -> None:
        self.historial.limpiar()

    def decir(self, texto: str) -> bool:
        if not texto: return False
        if not self.hablante.disponible: return False
        return self.hablante.decir(texto=texto)

    def cerrar(self) -> None:
        if self.hablante is not None:
            self.hablante.esperar()
            self.hablante.cerrar()

    @property
    def modelo(self) -> str:
        return settings.llm.modelo

    @property
    def voz_disponible(self) -> bool:
        return self.hablante.disponible

    @property
    def motor_voz(self) -> str:
        return self.hablante.backend