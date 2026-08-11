from __future__ import annotations
from dataclasses import dataclass

@dataclass 
class ClasificacionMemoria:
    tipo: str
    dominio: str
    categoria: str
    subcategoria: str | None = None
    confianza: float = 0.5


class ClasificadorMemoria:

    DOMINIOS = {
        "informatica": (
            "python",
            "programación",
            "programacion",
            "software",
            "código",
            "codigo",
            "flask",
            "api",
            "github",
            "base de datos",
            "sql",
            "ollama",
            "llm",
            "inteligencia artificial",
            "computador",
            "servidor",
        ),

        "robotica": (
            "robot",
            "servo",
            "servomotor",
            "sensor",
            "esp32",
            "arduino",
            "motor",
            "pata",
            "articulación",
            "articulacion",
            "spider-bot",
            "spiderbot",
            "imu",
            "lidar",
        ),

        "electronica": (
            "voltaje",
            "corriente",
            "resistencia",
            "batería",
            "bateria",
            "circuito",
            "pcb",
            "led",
            "pwm",
        ),

        "educacion": (
            "colegio",
            "escuela",
            "estudiante",
            "profesor",
            "profesora",
            "curso",
            "clase",
            "evaluación",
            "evaluacion",
        ),

        "ciencia": (
            "física",
            "fisica",
            "química",
            "quimica",
            "biología",
            "biologia",
            "experimento",
        ),
    }

    def clasificar(self, texto: str,) -> ClasificacionMemoria:
        texto_lower = texto.lower()

        if any(x in texto_lower for x in ("mi hermana","mi hermano","mi mamá","mi mama","mi papá","mi papa","mi amigo","mi amiga", ) ): return ClasificacionMemoria(tipo="personal",dominio="personas",categoria="relaciones",confianza=0.85,)
        if any(x in texto_lower for x in ("me gusta","no me gusta","prefiero","mi favorito","mi favorita",)): return ClasificacionMemoria(tipo="semantica",dominio="personal",categoria="preferencias",confianza=0.85,)
        if any(x in texto_lower for x in ("hoy ","ayer ","fuimos","fui ","estuve ","pasó ","paso ","ocurrió","ocurrio",)): return ClasificacionMemoria(tipo="episodica",dominio="experiencias",categoria="eventos",confianza=0.75,)

        mejor_dominio = "general"
        mejor_score = 0

        for dominio, palabras in self.DOMINIOS.items():
            score = sum(1 for palabra in palabras if palabra in texto_lower)
            if score > mejor_score:
                mejor_score = score
                mejor_dominio = dominio

        if mejor_score > 0:
            return ClasificacionMemoria(tipo="semantica",dominio=mejor_dominio,categoria=self._categoria(mejor_dominio,texto_lower,),confianza=min( 0.60 + (0.08 * mejor_score),0.95,),)
        return ClasificacionMemoria(tipo="semantica",dominio="general",categoria="conocimiento",confianza=0.50,)

    def _categoria(self,dominio: str,texto: str,) -> str:

        if dominio == "robotica":

            if any(x in texto for x in ("pata","articulación","articulacion","servo","servomotor",)): return "locomocion"
            if "sensor" in texto: return "sensores"

        if dominio == "informatica":
            if any( x in texto for x in ("python","código","codigo","programación",)):
                return "programacion"

            if any( x in texto for x in ("ollama", "llm", "inteligencia artificial",)):
                return "inteligencia_artificial"

            if any(x in texto for x in ("sql","base de datos",)):
                return "bases_de_datos"

        return "general"