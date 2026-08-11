from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

_FIN_ORACION = re.compile(
    r"""([.!?…][\"'»”)]*)(?=\s|$)""",
    re.VERBOSE,
)

def limpiar_para_voz(texto: str) -> str:
    texto = texto.strip()
    texto = texto.replace("**", "")
    texto = texto.replace("__", "")

    texto = re.sub(r"(?m)^\s*#{1,6}\s*","",texto,)
    texto = re.sub(r"(?m)^\s*[-*•]\s+","",texto,)
    texto = re.sub(r"[ \t]+"," ",texto,)
    texto = re.sub(r"\n+"," ",texto,)

    return texto.strip()

def extraer_oraciones(buffer: str) -> tuple[list[str], str]:
    oraciones: list[str] = []
    inicio = 0

    for match in _FIN_ORACION.finditer(buffer):
        fin = match.end()
        frase = buffer[inicio:fin].strip()
        if frase:
            oraciones.append(frase)
        inicio = fin

    resto = buffer[inicio:].lstrip()
    return oraciones, resto

def hablar_stream(fragmentos: Iterable[str],hablante,) -> Iterator[str]:
    buffer = ""
    for fragmento in fragmentos:
        yield fragmento
        buffer += fragmento
        oraciones, buffer = extraer_oraciones(buffer)

        for oracion in oraciones:
            texto_voz = limpiar_para_voz(oracion)

            if texto_voz:
                hablante.decir(texto_voz)

    if buffer.strip():
        texto_voz = limpiar_para_voz(buffer)

        if texto_voz:
            hablante.decir(texto_voz)