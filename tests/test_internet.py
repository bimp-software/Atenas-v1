from src.atenas.memoria.store_manager import (
    StorageManager,
)

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from src.config.settings import settings

from src.atenas.cerebro.investigacion import (
    Investigador,
    SintetizadorInvestigacion,
)


def main():

    storage = StorageManager()

    llm = OllamaClient(
        config=settings.llm
    )

    investigador = Investigador(
        storage=storage
    )

    sintetizador = (
        SintetizadorInvestigacion(
            llm=llm
        )
    )

    consulta = (
        "¿Qué es Matter en dispositivos IoT "
        "y podría ser útil para un robot?"
    )

    print()
    print("=" * 60)
    print(" INVESTIGACIÓN DE ATENAS")
    print("=" * 60)

    print()
    print("CONSULTA:")
    print(consulta)

    evaluacion = (
        investigador.evaluar_consulta(
            consulta
        )
    )

    print()
    print("EVALUACIÓN DEL CONOCIMIENTO:")

    print(
        "Incertidumbre:",
        evaluacion.get(
            "incertidumbre"
        )
    )

    print(
        "Mejor similitud:",
        evaluacion.get(
            "mejor_similitud"
        )
    )

    print(
        "Cobertura:",
        evaluacion.get(
            "cobertura_conceptual"
        )
    )

    print(
        "Términos conocidos:",
        evaluacion.get(
            "terminos_encontrados"
        )
    )

    print(
        "Términos desconocidos:",
        evaluacion.get(
            "terminos_desconocidos"
        )
    )

    print(
        "Motivos:",
        evaluacion.get(
            "motivos"
        )
    )

    print()
    print(
        "¿NECESITA INVESTIGAR?:",
        evaluacion.get(
            "necesita_investigar"
        )
    )

    # =====================================================
    # INVESTIGACIÓN
    # =====================================================

    resultado = (
        investigador.investigar(
            consulta
        )
    )

    print()
    print(
        "¿INVESTIGÓ?:",
        resultado.get(
            "investigo"
        )
    )

    resultados_web = (
        resultado.get(
            "resultados",
            []
        )
    )

    print(
        "Resultados web:",
        len(resultados_web)
    )

    for numero, fuente in enumerate(
        resultados_web,
        start=1,
    ):

        print()
        print(
            f"{numero}.",
            fuente.get("titulo")
        )

        print(
            fuente.get("url")
        )

    # =====================================================
    # SÍNTESIS
    # =====================================================

    if resultados_web:

        respuesta = (
            sintetizador.sintetizar(
                consulta,
                resultados_web,
            )
        )

        print()
        print("=" * 60)
        print(" ATENAS RESPONDE")
        print("=" * 60)
        print()
        print(respuesta)


if __name__ == "__main__":
    main()