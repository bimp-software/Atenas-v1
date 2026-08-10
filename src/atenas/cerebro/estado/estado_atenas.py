from dataclasses import dataclass, field

from .capacidades import CapacidadesAtenas


@dataclass
class EstadoAtenas:
    nombre: str = "ATENAS"
    creador: str = "Benjamín"
    version: str = "2.0"

    estado: str = "en_linea"

    capacidades: CapacidadesAtenas = field(
        default_factory=CapacidadesAtenas
    )

    def descripcion_para_llm(self) -> str:
        return f"""
            ESTADO ACTUAL DE ATENAS:

            Nombre: {self.nombre}
            Creador: {self.creador}
            Versión: {self.version}
            Estado: {self.estado}

            {self.capacidades.como_texto()}

            REGLAS SOBRE TUS CAPACIDADES:
            - Nunca afirmes poder hacer algo que actualmente figure como no disponible.
            - Puedes explicar que una capacidad está planificada o en desarrollo.
            - No confundas una capacidad futura con una capacidad actual.
            - Si el usuario pregunta si puedes realizar una acción física o digital, revisa primero este estado.
            - Si una capacidad no está disponible, dilo claramente y explica qué falta para habilitarla.
            """.strip()


estado_atenas = EstadoAtenas()