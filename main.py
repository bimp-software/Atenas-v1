from src.atenas.cerebro.nucleo_conversacional import NucleoConversacional

def main():

    atenas = NucleoConversacional()

    print()
    print("ATENAS V2")
    print(f"Modelo: {atenas.modelo}")
    print("Escribe 'salir' para terminar.")
    print()

    while True:

        try:

            mensaje = input("Tú: ").strip()

            if not mensaje: continue

            if mensaje.lower() in {"salir","exit","quit",}:
                print("\nATENAS: Hasta luego.")
                break

            if mensaje.lower() == "/limpiar":
                atenas.limpiar_conversacion()
                print("\nATENAS: ""He limpiado la conversación.")
                continue

            print("\nATENAS: ", end="", flush=True)

            for fragmento in atenas.responder_stream(mensaje):
                print(fragmento,end="",flush=True)

            print("\n")

        except KeyboardInterrupt:
            print("\n\nATENAS: Hasta luego.")
            break

        except Exception as error:
            print(f"\n[ERROR] {error}\n")


if __name__ == "__main__":
    main()