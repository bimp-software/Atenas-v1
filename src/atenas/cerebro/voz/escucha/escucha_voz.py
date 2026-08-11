from __future__ import annotations

from .microfono import Microfono
from .transcriptor import Transcriptor


class EscuchaVoz:

    def __init__(self,microfono: Microfono | None = None,transcriptor: Transcriptor | None = None,):
        self.microfono = (microfono or Microfono())
        self.transcriptor = (transcriptor or Transcriptor())
        self._escuchando = False

    def escuchar(self,duracion: float = 5.0,) -> str:
        if self._escuchando: return ""
        self._escuchando = True
        try:
            audio = self.microfono.grabar( duracion=duracion)
            texto = self.transcriptor.transcribir(audio)
            return texto.strip()
        finally:
            self._escuchando = False

    @property
    def escuchando(self) -> bool:
        return self._escuchando