import time

from src.atenas.herramientas import ToolExecutor


def main():

    executor = ToolExecutor()

    # Abrir Bloc de notas
    resultado = executor.ejecutar(
        "abrir_programa",
        {
            "programa": "notepad"
        }
    )

    print(
        "Abrir:",
        resultado
    )

    time.sleep(1.5)

    # Escribir
    resultado = executor.ejecutar(
        "escribir_texto",
        {
            "texto": (
                "Hola Benjamín. "
                "Esta nota fue escrita por ATENAS."
            )
        }
    )

    print(
        "Escribir:",
        resultado
    )


if __name__ == "__main__":
    main()