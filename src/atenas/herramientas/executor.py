from src.atenas.herramientas.notas.crear_nota import crear_nota
from src.atenas.herramientas.sistema.abrir_programa import abrir_programa
from src.atenas.herramientas.teclado.escribir_texto import escribir_texto


class ToolExecutor:

    def __init__(self):

        self.herramientas = {
            "crear_nota": crear_nota,
            "abrir_programa": abrir_programa,
            "escribir_texto": escribir_texto,
        }

    def ejecutar(
        self,
        nombre: str,
        argumentos: dict | None = None,
    ) -> dict:

        argumentos = argumentos or {}

        herramienta = self.herramientas.get(
            nombre
        )

        if herramienta is None:

            return {
                "ok": False,
                "error": "herramienta_no_permitida",
                "mensaje": (
                    f"La herramienta '{nombre}' "
                    "no está registrada."
                ),
            }

        try:

            resultado = herramienta(
                **argumentos
            )

            if isinstance(
                resultado,
                dict,
            ):
                return resultado

            return {
                "ok": True,
                "resultado": resultado,
            }

        except Exception as error:

            return {
                "ok": False,
                "error": type(error).__name__,
                "mensaje": str(error),
            }