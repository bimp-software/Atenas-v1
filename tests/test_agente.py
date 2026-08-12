from src.atenas.cerebro.agente import (
    AgenteAtenas,
    Objetivo,
)


def main():

    agente = AgenteAtenas()

    # =====================================================
    # OBJETIVO PERMANENTE
    # =====================================================

    agente.agregar_objetivo(
        Objetivo(
            id="documentar_atenas",
            nombre="Documentar desarrollo de Atenas",
            descripcion=(
                "Mantener registro de cambios importantes "
                "del proyecto Atenas."
            ),
            prioridad=0.8,
        )
    )

    # =====================================================
    # OBSERVACIÓN
    # =====================================================

    mensaje = (
        "Las patas de Atenas tendrán "
        "cuatro articulaciones."
    )

    print()
    print("OBSERVACIÓN:")
    print(mensaje)

    pendientes = agente.observar(
        mensaje
    )

    print()
    print("PENDIENTES CREADOS AUTOMÁTICAMENTE:")

    if not pendientes:
        print("Ninguno.")

    for pendiente in pendientes:
        print(
            "-",
            pendiente.descripcion
        )

    # =====================================================
    # PENSAR
    # =====================================================

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


if __name__ == "__main__":
    main()