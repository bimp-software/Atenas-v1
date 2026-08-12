from src.atenas.herramientas import ToolExecutor


def main():

    executor = ToolExecutor()

    resultado = executor.ejecutar(
        "abrir_programa",
        {
            "programa": "notepad"
        }
    )

    print(resultado)


if __name__ == "__main__":
    main()