from __future__ import annotations

import numpy as np
import sounddevice as sd

class Microfono:

    def __init__(self, sample_rate: int = 16000, canales: int = 1, dispositivo: int | None = None):
        self.sample_rate = sample_rate
        self.canales = canales
        self.dispositivo = dispositivo

    def grabar(self,duracion: float = 5.0,) -> np.ndarray:
        frames = int(self.sample_rate * duracion)
        audio = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.canales,
            dtype="float32",
            device=self.dispositivo,
        )

        sd.wait()
        if audio.ndim > 1: audio = audio[:, 0]

        return np.asarray(audio,dtype=np.float32,)

    @staticmethod
    def listar_dispositivos():

        return sd.query_devices()