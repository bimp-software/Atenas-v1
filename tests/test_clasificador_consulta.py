from src.atenas.cerebro.investigacion.clasificador_consulta import (
    ClasificadorConsulta,
)


def main():

    clasificador = ClasificadorConsulta()

    pruebas = [
        "Hola Atenas",
        "Que cuentas",
        "no",
        "como te llamas",
        "sabes ingles",
        "cuanto es 2 + 2",
        "¿Qué es Matter?",
        "Necesito información de la seguridad de datos en Chile",
        "Busca la última versión de Python",
        "¿Qué equipo de fútbol es mejor?",
    ]

    for consulta in pruebas:

        resultado = (
            clasificador.clasificar(
                consulta
            )
        )

        print()
        print("=" * 60)
        print(consulta)
        print("=" * 60)

        print(
            "Tipo:",
            resultado.tipo
        )

        print(
            "Requiere conocimiento:",
            resultado.requiere_conocimiento
        )

        print(
            "Permite Internet:",
            resultado.permite_internet
        )

        print(
            "Motivo:",
            resultado.motivo
        )


if __name__ == "__main__":
    main()