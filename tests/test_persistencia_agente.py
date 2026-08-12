from src.atenas.cerebro.agente import (
    AgenteAtenas,
    Objetivo,
)


def main():

    print("\nPRIMERA INSTANCIA\n")

    agente1 = AgenteAtenas()

    agente1.agregar_objetivo(
        Objetivo(
            id="documentar_atenas",
            nombre="Documentar desarrollo de Atenas",
            descripcion=(
                "Mantener registro de cambios "
                "importantes del proyecto."
            ),
            prioridad=0.8,
        )
    )

    agente1.observar(
        "Voy a utilizar una cámara nueva "
        "para la visión de Atenas."
    )

    print(
        "Pendientes primera instancia:",
        len(
            agente1.pendientes.pendientes()
        )
    )

    print("\nSEGUNDA INSTANCIA\n")

    agente2 = AgenteAtenas()

    print(
        "Objetivos recuperados:",
        len(
            agente2.objetivos.activos()
        )
    )

    print(
        "Pendientes recuperados:",
        len(
            agente2.pendientes.pendientes()
        )
    )

    for pendiente in (
        agente2.pendientes.pendientes()
    ):
        print(
            "-",
            pendiente.descripcion
        )


if __name__ == "__main__":
    main()