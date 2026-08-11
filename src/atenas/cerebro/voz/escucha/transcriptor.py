from __future__ import annotations

import numpy as np
from faster_whisper import WhisperModel


class Transcriptor:

    def __init__(self,modelo: str = "small",dispositivo: str = "cpu",compute_type: str = "int8",idioma: str = "es",):
        self.idioma = idioma

        self.modelo = WhisperModel(
            modelo,
            device=dispositivo,
            compute_type=compute_type,
        )

    def transcribir(self,audio: np.ndarray) -> str:

        if audio is None:
            return ""

        if len(audio) == 0:
            return ""

        segments, info = self.modelo.transcribe(
            audio,
            language=self.idioma,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500,},
            beam_size=5,
        )
        textos = []

        for segmento in segments:
            texto = segmento.text.strip()
            if texto:
                textos.append(texto)
        return " ".join(textos).strip()