from src.atenas.cerebro.memoria.filtro_memoria import (
    FiltroMemoria,
)


def main():

    filtro = FiltroMemoria()

    pruebas = [
        "Hola Atenas",
        "¿Qué recuerdas sobre tus patas?",
        "Gracias",
        "Quiero utilizar un ESP32 para controlar los servomotores.",
        "Las patas tendrán cuatro articulaciones.",
        "Estoy utilizando Python y Flask para la interfaz.",
    ]

    for texto in pruebas:

        resultado = filtro.evaluar(
            texto=texto,
            fuente="usuario",
        )

        print()
        print("=" * 60)
        print(texto)
        print("=" * 60)

        print(
            "Guardar:",
            resultado.guardar
        )

        print(
            "Tipo:",
            resultado.tipo
        )

        print(
            "Motivo:",
            resultado.motivo
        )

        print(
            "Score:",
            resultado.score
        )


if __name__ == "__main__":
    main()