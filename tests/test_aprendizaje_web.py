from src.atenas.memoria.store_manager import (
    StorageManager,
)

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from src.atenas.cerebro.memoria.clasificador import (
    ClasificadorMemoria,
)

from src.atenas.cerebro.memoria.consolidador import (
    ConsolidadorMemoria,
)

from src.atenas.cerebro.memoria.recuperador import (
    RecuperadorMemoria,
)

from src.atenas.cerebro.memoria.hipocampo import (
    HipocampoDigital,
)

from src.atenas.cerebro.investigacion import (
    Investigador,
    SintetizadorInvestigacion,
    ConsolidadorInvestigacion,
)

from src.config.settings import settings


def main():

    print()
    print("=" * 70)
    print(" APRENDIZAJE WEB DE ATENAS")
    print("=" * 70)

    # =====================================================
    # COMPONENTES COMPARTIDOS
    # =====================================================

    storage = StorageManager()

    llm = OllamaClient(
        config=settings.llm
    )

    clasificador = (
        ClasificadorMemoria()
    )

    consolidador_memoria = (
        ConsolidadorMemoria(
            storage=storage
        )
    )

    recuperador = (
        RecuperadorMemoria(
            storage=storage
        )
    )

    hipocampo = (
        HipocampoDigital(
            clasificador=clasificador,
            consolidador=consolidador_memoria,
            recuperador=recuperador,
        )
    )

    investigador = (
        Investigador(
            storage=storage
        )
    )

    sintetizador = (
        SintetizadorInvestigacion(
            llm=llm
        )
    )

    consolidador_web = (
        ConsolidadorInvestigacion(
            storage=storage,
            hipocampo=hipocampo,
        )
    )

    # =====================================================
    # CONSULTA
    # =====================================================

    consulta = (
        "¿Qué es Matter en dispositivos IoT "
        "y para qué podría servir?"
    )

    print()
    print("CONSULTA:")
    print(consulta)

    # =====================================================
    # 1. VER QUÉ SABE ANTES
    # =====================================================

    evaluacion_antes = (
        investigador.evaluar_consulta(
            consulta
        )
    )

    print()
    print("-" * 70)
    print("CONOCIMIENTO ANTES DE INVESTIGAR")
    print("-" * 70)

    print(
        "Necesita investigar:",
        evaluacion_antes.get(
            "necesita_investigar"
        )
    )

    print(
        "Incertidumbre:",
        evaluacion_antes.get(
            "incertidumbre"
        )
    )

    print(
        "Mejor similitud:",
        evaluacion_antes.get(
            "mejor_similitud"
        )
    )

    print(
        "Cobertura:",
        evaluacion_antes.get(
            "cobertura_conceptual"
        )
    )

    print(
        "Términos conocidos:",
        evaluacion_antes.get(
            "terminos_encontrados"
        )
    )

    print(
        "Términos desconocidos:",
        evaluacion_antes.get(
            "terminos_desconocidos"
        )
    )

    # =====================================================
    # 2. FORZAR INVESTIGACIÓN
    #
    # Solamente lo hacemos porque esto es un TEST.
    # =====================================================

    print()
    print("-" * 70)
    print("INVESTIGANDO EN INTERNET")
    print("-" * 70)

    investigacion = (
        investigador.investigar(
            consulta=consulta,
            limite=5,
            forzar=True,
        )
    )

    resultados = (
        investigacion.get(
            "resultados",
            []
        )
    )

    print()
    print(
        "Investigó:",
        investigacion.get(
            "investigo"
        )
    )

    print(
        "Resultados:",
        len(resultados)
    )

    if not resultados:

        print()
        print(
            "No se obtuvieron resultados web."
        )

        if investigacion.get("error"):

            print(
                "Error:",
                investigacion.get(
                    "error"
                )
            )

        if investigacion.get("mensaje"):

            print(
                "Mensaje:",
                investigacion.get(
                    "mensaje"
                )
            )

        return

    for numero, fuente in enumerate(
        resultados,
        start=1,
    ):

        print()
        print(
            f"{numero}.",
            fuente.get("titulo")
        )

        print(
            "   ",
            fuente.get("url")
        )

    # =====================================================
    # 3. SINTETIZAR
    # =====================================================

    sintesis = (
        sintetizador.sintetizar(
            consulta=consulta,
            resultados=resultados,
        )
    )

    print()
    print("-" * 70)
    print("SÍNTESIS GENERADA POR ATENAS")
    print("-" * 70)
    print()
    print(sintesis)

    if not sintesis:

        print(
            "No fue posible generar síntesis."
        )

        return

    # =====================================================
    # 4. APRENDER
    # =====================================================

    aprendizaje = (
        consolidador_web.consolidar(
            consulta=consulta,
            sintesis=sintesis,
            fuentes=resultados,
            confianza=0.80,
        )
    )

    print()
    print("-" * 70)
    print("RESULTADO DEL APRENDIZAJE")
    print("-" * 70)
    print()
    print(aprendizaje)

    # =====================================================
    # 5. RECUPERAR CON OTRAS PALABRAS
    # =====================================================

    pregunta_nueva = (
        "¿Qué recuerdas acerca del protocolo "
        "Matter para dispositivos conectados?"
    )

    print()
    print("=" * 70)
    print(" RECUPERACIÓN LOCAL POSTERIOR")
    print("=" * 70)

    print()
    print("Pregunta nueva:")
    print(pregunta_nueva)

    memorias = (
        recuperador.buscar(
            pregunta_nueva,
            limite=5,
        )
    )

    print()
    print(
        "Memorias recuperadas:",
        len(memorias)
    )

    for numero, memoria in enumerate(
        memorias,
        start=1,
    ):

        contenido = (
            memoria.get("contenido")
            or memoria.get("descripcion")
        )

        print()
        print(
            f"{numero}. {contenido}"
        )

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
            memoria.get(
                "dominio"
            )
        )

        print(
            "   Similitud:",
            round(
                float(
                    memoria.get(
                        "similitud_semantica",
                        0.0,
                    )
                    or 0.0
                ),
                3,
            )
        )

    # =====================================================
    # 6. ¿ATENAS NECESITA INTERNET DESPUÉS DE APRENDER?
    # =====================================================

    evaluacion_despues = (
        investigador.evaluar_consulta(
            pregunta_nueva
        )
    )

    print()
    print("=" * 70)
    print(" CONOCIMIENTO DESPUÉS DE APRENDER")
    print("=" * 70)

    print()
    print(
        "Necesita investigar:",
        evaluacion_despues.get(
            "necesita_investigar"
        )
    )

    print(
        "Incertidumbre:",
        evaluacion_despues.get(
            "incertidumbre"
        )
    )

    print(
        "Mejor similitud:",
        evaluacion_despues.get(
            "mejor_similitud"
        )
    )

    print(
        "Cobertura:",
        evaluacion_despues.get(
            "cobertura_conceptual"
        )
    )

    print()
    print("=" * 70)
    print(" TEST FINALIZADO")
    print("=" * 70)


if __name__ == "__main__":
    main()