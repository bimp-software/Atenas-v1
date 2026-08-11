from src.atenas.cerebro.nucleo_conversacional import (
    NucleoConversacional,
)


def main():

    atenas = NucleoConversacional()

    print()
    print("ATENAS V2")
    print()

    print(f"Modelo: {atenas.modelo}")
    print("Voz salida:",("ACTIVA" if atenas.voz_disponible else "NO DISPONIBLE"))
    print()

    print("Comandos:")
    print("/voz     Hablar con ATENAS")
    print("/limpiar Limpiar conversación")
    print("salir     Cerrar ATENAS")
    print()

    try:

        while True:
            entrada = input("Tú: ").strip()

            if entrada.lower() in {"salir","exit","quit",}:
                atenas.decir("Hasta luego.")
                break

            if entrada.lower() == "/limpiar":
                atenas.limpiar_conversacion()
                print("ATENAS: Conversación limpiada.")
                continue

            if entrada.lower() == "/voz":
                print()
                print("ATENAS está escuchando...")
                mensaje = atenas.escuchar(duracion=6)

                if not mensaje:
                    print("No pude entender lo que dijiste.")
                    continue

                print(f"Tú: {mensaje}")

            else:
                mensaje = entrada
            if not mensaje:
                continue

            print()
            print("ATENAS: ",end="",flush=True,)

            for fragmento in (
                atenas.responder_stream(mensaje)
            ):

                print(fragmento,end="",flush=True,)

            print()
            print()

    except KeyboardInterrupt:
        print("\nATENAS detenida.")
    finally:
        atenas.cerrar()


if __name__ == "__main__":
    main()