from dataclasses import dataclass

@dataclass(frozen=True)
class LLMSettings:
    modelo: str = "qwen3:8b"
    temperatura: float = 0.6
    contexto: int = 4096
    max_tokens: int = 1024
    max_turnos_historial: int = 10
    pensar: bool = False

@dataclass(frozen=True)
class AtenasSettings:
    nombre: str = "ATENAS"
    creador: str = "Benjamín"

    llm: LLMSettings = LLMSettings()

settings = AtenasSettings()