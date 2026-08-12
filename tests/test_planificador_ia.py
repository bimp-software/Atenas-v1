from src.atenas.cerebro.agente import (
    AgenteAtenas,
    Objetivo,
)


def main():

    agente = AgenteAtenas()

    agente.agregar_objetivo(
        Objetivo(
            id="documentar_atenas",
            nombre="Documentar desarrollo de Atenas",
            descripcion=(
                "Mantener registro actualizado "
                "de las decisiones importantes "
                "del proyecto Atenas."
            ),
            prioridad=0.8,
        )
    )

    mensaje = (
        "Quiero utilizar un ESP32 "
        "para controlar los servomotores "
        "de tus patas."
    )

    print()
    print("USUARIO:")
    print(mensaje)

    creados = agente.observar(
        mensaje
    )

    if not creados:

        print()
        print(
            "ATENAS no detectó "
            "ninguna necesidad."
        )

        return

    print()
    print("NECESIDAD:")
    print(
        creados[0]
    )

    resultado = agente.pensar()

    print()
    print("DECISIÓN:")
    print(
        resultado["decision"]
    )

    print()
    print("PLAN GENERADO POR ATENAS:")
    print(
        resultado["plan"]
    )


if __name__ == "__main__":
    main()