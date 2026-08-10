from typing import Literal


Role = Literal[
    "system",
    "user",
    "assistant",
]


class HistorialConversacion:

    def __init__(self,max_turnos: int = 10):
        self.max_turnos = max_turnos
        self._mensajes: list[dict[str, str]] = []

    def agregar(self,role: Role,content: str) -> None:
        content = content.strip()
        if not content: return
        self._mensajes.append({"role": role,"content": content,})
        self._recortar()

    def agregar_usuario(self,mensaje: str) -> None:
        self.agregar("user",mensaje)

    def agregar_asistente(self,mensaje: str) -> None:
        self.agregar("assistant",mensaje)

    def _recortar(self) -> None:
        limite = self.max_turnos * 2
        if len(self._mensajes) > limite:
            self._mensajes = self._mensajes[-limite:]

    def obtener(self) -> list[dict[str, str]]:
        return list(self._mensajes)

    def limpiar(self) -> None:
        self._mensajes.clear()

    @property
    def cantidad_mensajes(self) -> int:
        return len(self._mensajes)

    @property
    def cantidad_turnos(self) -> int:
        return len(self._mensajes) // 2