from src.atenas.cerebro.agente import (
    AgenteAtenas,
    Objetivo,
)


def main():

    agente = AgenteAtenas()

    agente.agregar_objetivo(
        Objetivo(
            id="documentar_atenas",
            nombre=(
                "Documentar desarrollo "
                "de Atenas"
            ),
            descripcion=(
                "Mantener registro de "
                "cambios importantes "
                "del proyecto Atenas."
            ),
            prioridad=0.8,
        )
    )

    # =====================================================
    # INFORMACIÓN NUEVA
    # =====================================================

    mensaje = (
        "Quiero utilizar un ESP32 "
        "para controlar los servomotores."
    )

    print()
    print("USUARIO:")
    print(mensaje)

    # El usuario NO dice:
    # "crea una nota".
    #
    # Atenas debe decidirlo sola.

    creados = agente.observar(
        mensaje
    )

    print()
    print("PENDIENTES CREADOS:")

    for pendiente in creados:
        print(
            pendiente.descripcion
        )

    # =====================================================
    # ATENAS DECIDE Y ACTÚA
    # =====================================================

    resultado = agente.actuar()

    print()
    print("RESULTADO DE LA ACCIÓN:")
    print(resultado)

    # =====================================================
    # VER PENDIENTES RESTANTES
    # =====================================================

    print()
    print("PENDIENTES RESTANTES:")

    pendientes = (
        agente.pendientes
        .pendientes()
    )

    if not pendientes:
        print("Ninguno.")

    for pendiente in pendientes:
        print(
            pendiente.descripcion
        )

    # =====================================================
    # MENSAJE NORMAL
    # =====================================================

    print()
    print("-----------------------------------")
    print()

    mensaje_normal = (
        "Hola Atenas, ¿cómo estás?"
    )

    print("USUARIO:")
    print(mensaje_normal)

    nuevos = agente.observar(
        mensaje_normal
    )

    print()
    print(
        "NUEVOS PENDIENTES:",
        len(nuevos),
    )

    segunda_accion = (
        agente.actuar()
    )

    print()
    print("SEGUNDA DECISIÓN:")
    print(
        segunda_accion
    )


if __name__ == "__main__":
    main()