from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)

class MotorVoz:
    def __init__(self, velocidad: int = 0, volumen: int = 100):
        self.velocidad = velocidad
        self.volumen = max(0, min(100, volumen))

        self.backend: str | None = None
        self._voz_sapi = None
        self._pythoncom = None

        self._thread_id: int | None = None
        self._inicializado = False

    def inicializar(self) -> bool:
        if self._inicializado: return True
        self._thread_id = threading.get_ident()

        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()

            voz = win32com.client.Dispatch("SAPI.SpVoice")

            voz.Rate = self.velocidad
            voz.Volume = self.volumen

            self._pythoncom = pythoncom
            self._voz_sapi = voz

            self.backend = "sapi5"
            self._inicializado = True

            logger.info("Motor de voz inicializado con SAPI5.")

            return True

        except Exception as error:
            logger.warning("No se pudo iniciar SAPI5: %s",error)
            self._cerrar_com()

        try:
            import pyttsx3

            engine = pyttsx3.init()
            del engine

            self.backend = "pyttsx3"
            self._inicializado = True

            logger.info("Motor de voz inicializado con pyttsx3.")

            return True

        except Exception as error:
            logger.error("No hay ningún motor de voz disponible: %s",error,)

        self.backend = None
        self._inicializado = False

        return False


    def hablar(self, texto: str) -> bool:
        texto = texto.strip()

        if not texto:
            return True

        if not self._inicializado:
            if not self.inicializar():
                return False

        if self.backend == "sapi5":
            return self._hablar_sapi(texto)

        if self.backend == "pyttsx3":
            return self._hablar_pyttsx3(texto)

        return False 

    def _hablar_sapi(self, texto: str) -> bool:
        try:
            self._voz_sapi.Speak(texto)
            return True

        except Exception as error:
            logger.exception("Error hablando mediante SAPI5: %s",error,)
            return False

    def _hablar_pyttsx3(self, texto: str) -> bool:
        """
        Se crea un engine nuevo por fragmento.

        No reutilizamos indefinidamente una misma instancia
        de pyttsx3.
        """

        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("volume",self.volumen / 100,)

            # pyttsx3 usa palabras/minuto,
            # por eso este valor no equivale directamente
            # al Rate de SAPI.
            engine.setProperty("rate",180 + (self.velocidad * 10),)

            engine.say(texto)
            engine.runAndWait()

            del engine

            return True

        except Exception as error:
            logger.exception("Error hablando mediante pyttsx3: %s",error,)
            return False

    def cerrar(self) -> None:
        self._voz_sapi = None

        self._cerrar_com()

        self._inicializado = False

    def _cerrar_com(self) -> None:
        if self._pythoncom is not None:
            try:
                self._pythoncom.CoUninitialize()
            except Exception:
                pass

        self._pythoncom = None

    @property
    def disponible(self) -> bool:
        return self._inicializado

    @property
    def nombre_backend(self) -> str:
        return self.backend or "no_disponible"