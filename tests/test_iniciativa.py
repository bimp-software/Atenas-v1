from src.atenas.cerebro.agente import (
    AgenteAtenas,
    Objetivo,
)


def probar(
    agente: AgenteAtenas,
    mensaje: str,
):

    print()
    print("=" * 70)
    print("OBSERVACIÓN")
    print("=" * 70)

    print(mensaje)

    pendientes = agente.observar(
        mensaje
    )

    print()
    print("PENDIENTES:")

    if not pendientes:
        print("Ninguno.")

    for pendiente in pendientes:
        print(
            "-",
            pendiente.descripcion
        )

    resultado = agente.pensar()

    print()
    print("DECISIÓN:")
    print(
        resultado["decision"]
    )

    print()
    print("PLAN:")
    print(
        resultado["plan"]
    )


def main():

    agente = AgenteAtenas()

    agente.agregar_objetivo(
        Objetivo(
            id="documentar_atenas",
            nombre=(
                "Documentar desarrollo de Atenas"
            ),
            descripcion=(
                "Mantener actualizado el registro "
                "de decisiones importantes sobre "
                "software, robótica y hardware "
                "del proyecto Atenas."
            ),
            prioridad=0.8,
        )
    )

    mensajes = [
        (
            "Mejor voy a fabricar primero "
            "las extremidades en cartón."
        ),

        (
            "Quiero utilizar un ESP32 "
            "para controlar los servomotores."
        ),

        (
            "Voy a cambiar Flask por otra "
            "tecnología para la interfaz."
        ),

        (
            "Hola Atenas, ¿cómo estás?"
        ),
    ]

    for mensaje in mensajes:

        probar(
            agente,
            mensaje
        )


if __name__ == "__main__":
    main()