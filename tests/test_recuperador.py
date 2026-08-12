from src.atenas.memoria.store_manager import StorageManager

from src.atenas.cerebro.memoria.recuperador import (
    RecuperadorMemoria,
)


def main():
    print("\n===================================")
    print(" TEST RECUPERADOR HÍBRIDO - ATENAS")
    print("===================================\n")

    storage = StorageManager()

    recuperador = RecuperadorMemoria(
        storage=storage
    )

    consultas = [
        "¿Cómo serán las extremidades de tu cuerpo?",
        "¿Con qué tecnología estoy haciendo tu interfaz?",
        "¿Cómo se moverá tu cuerpo robótico?",
        "¿Qué recuerdas sobre tu locomoción?",
        "¿Qué tecnologías estoy usando para crear Atenas?",
    ]

    for consulta in consultas:

        print("\n===================================")
        print("CONSULTA")
        print("===================================")

        print(consulta)

        resultados = recuperador.buscar(
            consulta,
            limite=8,
        )

        print("\nRESULTADOS:")

        if not resultados:
            print("No se encontraron memorias.")
            continue

        for i, memoria in enumerate(
            resultados,
            start=1,
        ):

            contenido = (
                memoria.get("contenido")
                or memoria.get("descripcion")
            )

            print()
            print(f"{i}. {contenido}")

            print(
                "   Tipo:",
                memoria.get(
                    "_tipo_memoria"
                )
            )

            print(
                "   Recuperación:",
                memoria.get(
                    "_tipo_recuperacion"
                )
            )

            print(
                "   Dominio:",
                memoria.get("dominio")
            )

            print(
                "   Similitud:",
                round(
                    memoria.get(
                        "similitud_semantica",
                        0.0,
                    ),
                    3,
                )
            )

            print(
                "   Score:",
                round(
                    recuperador._score_memoria(
                        memoria
                    ),
                    3,
                )
            )

        print("\n-----------------------------------")
        print("CONTEXTO QUE RECIBIRÍA QWEN")
        print("-----------------------------------\n")

        contexto = (
            recuperador.contexto_para_llm(
                consulta,
                limite=6,
            )
        )

        print(
            contexto
            or "Sin contexto."
        )


if __name__ == "__main__":
    main()