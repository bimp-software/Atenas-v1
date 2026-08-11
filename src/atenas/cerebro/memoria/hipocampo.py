from dataclasses import dataclass
from typing import Optional

@dataclass
class Experiencia:
    contenido: str

    tipo: str | None = None
    dominio: str | None = None
    subcategoria: str | None = None

    fuente: str = "usuario"

    importancia: float = 0.5
    confianza: float = 0.7
    novedad: float = 0.5

    contexto: str | None = None

class HipocampoDigital:

    def __init__(self,clasificador,consolidador,recuperador,):
        self.clasificador = clasificador
        self.consolidador = consolidador
        self.recuperador = recuperador

    def procesar(self,experiencia: Experiencia):
        clasificacion = (self.clasificador.clasificar(experiencia.contenido))
        experiencia.tipo = (clasificacion.tipo)
        experiencia.dominio = (clasificacion.dominio)
        experiencia.subcategoria = (clasificacion.subcategoria)

        return self.consolidador.consolidar(experiencia)

    def recordar(self,consulta: str):
        return self.recuperador.buscar(consulta)