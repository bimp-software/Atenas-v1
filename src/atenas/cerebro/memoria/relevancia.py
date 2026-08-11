from __future__ import annotations
import re

class EvaluadorRelevancia:
    PALABRAS_TRIVIALES = {
        "hola",
        "holi",
        "gracias",
        "adios",
        "adiós",
        "ok",
        "okay",
        "si",
        "sí",
        "no",
        "dale",
        "bueno",
    }

    INDICADORES_IMPORTANTES = (
        "recuerda",
        "acuérdate",
        "acuerdate",
        "mi nombre",
        "se llama",
        "prefiero",
        "me gusta",
        "no me gusta",
        "estoy creando",
        "estoy trabajando",
        "mi proyecto",
        "mi hermana",
        "mi hermano",
        "mi mamá",
        "mi mama",
        "mi papá",
        "mi papa",
        "trabaja en",
        "vivo en",
        "uso ",
        "utilizo ",
        "quiero que",
    )

    def calcular(self, texto: str) -> float:
        texto = texto.strip()
        if not texto: return 0.0
        texto_lower = texto.lower()

        if texto_lower in self.PALABRAS_TRIVIALES: return 0.05

        puntuacion = 0.25

        # Longitud moderada suele contener
        # más información semántica.
        palabras = texto.split()

        if len(palabras) >= 5: puntuacion += 0.10
        if len(palabras) >= 12: puntuacion += 0.10

        # Indicadores explícitos
        for indicador in self.INDICADORES_IMPORTANTES:
            if indicador in texto_lower:
                puntuacion += 0.20
                break

        # Números / fechas pueden ser datos concretos
        if re.search(r"\b\d{2,4}\b", texto): puntuacion += 0.10

        # Primera persona: potencial preferencia,
        # información personal o proyecto.
        if any(expresion in texto_lower for expresion in ("yo ","mi ","mis ","quiero ","prefiero ","tengo ", )): puntuacion += 0.10
        return min( round(puntuacion, 3), 1.0, )

    def merece_memoria(self,texto: str,umbral: float = 0.45,) -> bool:
        return (self.calcular(texto) >= umbral)