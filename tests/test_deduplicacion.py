from __future__ import annotations

from src.atenas.memoria.store_manager import (
    StorageManager,
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
    Experiencia,
)


def mostrar_resultado(
    numero: int,
    texto: str,
    resultado: dict,
) -> None:

    print()
    print("=" * 80)
    print(f" EXPERIENCIA {numero}")
    print("=" * 80)

    print()
    print("Texto:")
    print(texto)

    print()
    print("Resultado general:")
    print(resultado)

    print()
    print("-" * 80)
    print("DIAGNÓSTICO")
    print("-" * 80)

    print(
        "Guardada:",
        resultado.get(
            "guardada"
        )
    )

    print(
        "Duplicada:",
        resultado.get(
            "duplicada"
        )
    )

    print(
        "Acción:",
        resultado.get(
            "accion"
        )
    )

    print(
        "Memoria ID:",
        (
            resultado.get("memoria_id")
            or resultado.get("id")
        )
    )

    print(
        "Similitud:",
        round(
            float(
                resultado.get(
                    "similitud",
                    resultado.get(
                        "mejor_similitud_previa",
                        0.0,
                    ),
                )
                or 0.0
            ),
            4,
        )
    )

    print(
        "Coincidencia palabras:",
        round(
            float(
                resultado.get(
                    "coincidencia_palabras",
                    0.0,
                )
                or 0.0
            ),
            4,
        )
    )

    print(
        "Score deduplicación:",
        round(
            float(
                resultado.get(
                    "score_final",
                    resultado.get(
                        "score_deduplicacion",
                        0.0,
                    ),
                )
                or 0.0
            ),
            4,
        )
    )

    print(
        "Filtro:",
        resultado.get(
            "filtro_tipo"
        )
    )

    print(
        "Motivo filtro:",
        resultado.get(
            "filtro_motivo"
        )
    )


def main():

    print()
    print("=" * 80)
    print(" TEST DE DEDUPLICACIÓN DE MEMORIA - ATENAS")
    print("=" * 80)

    # =====================================================
    # COMPONENTES
    # =====================================================

    storage = StorageManager()

    clasificador = (
        ClasificadorMemoria()
    )

    consolidador = (
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
            consolidador=consolidador,
            recuperador=recuperador,
            storage=storage,
        )
    )

    # =====================================================
    # EXPERIENCIAS DE PRUEBA
    # =====================================================

    experiencias = [
        {
            "texto": (
                "Las patas de Atenas tendrán "
                "cuatro articulaciones."
            ),
            "esperado": "nueva",
        },

        {
            "texto": (
                "Cada pata de Atenas tendrá "
                "4 articulaciones."
            ),
            "esperado": "duplicada",
        },

        {
            "texto": (
                "El diseño de las patas de Atenas "
                "usa cuatro articulaciones."
            ),
            "esperado": "duplicada",
        },

        {
            "texto": (
                "Atenas utilizará una cámara frontal "
                "para su sistema de visión."
            ),
            "esperado": "nueva",
        },
    ]

    resultados = []

    # =====================================================
    # PROCESAR
    # =====================================================

    for numero, prueba in enumerate(
        experiencias,
        start=1,
    ):

        texto = prueba["texto"]

        experiencia = Experiencia(
            contenido=texto,
            fuente="usuario",
            importancia=0.8,
            confianza=0.9,
            contexto="test_deduplicacion",
        )

        resultado = (
            hipocampo.procesar(
                experiencia
            )
        )

        resultados.append({
            "numero": numero,
            "texto": texto,
            "esperado": prueba["esperado"],
            "resultado": resultado,
        })

        mostrar_resultado(
            numero=numero,
            texto=texto,
            resultado=resultado,
        )

    # =====================================================
    # RESUMEN
    # =====================================================

    print()
    print("=" * 80)
    print(" RESUMEN")
    print("=" * 80)

    correctos = 0

    for item in resultados:

        resultado = item["resultado"]
        esperado = item["esperado"]

        if esperado == "duplicada":

            cumple = bool(
                resultado.get(
                    "duplicada"
                )
            )

        else:

            cumple = (
                resultado.get(
                    "guardada"
                )
                is True
                and not resultado.get(
                    "duplicada",
                    False,
                )
            )

        if cumple:
            correctos += 1

        print()
        print(
            f"Experiencia {item['numero']}:"
        )

        print(
            "Esperado:",
            esperado
        )

        print(
            "Resultado:",
            (
                "duplicada"
                if resultado.get(
                    "duplicada"
                )
                else "nueva"
            )
        )

        print(
            "Correcto:",
            cumple
        )

    print()
    print("-" * 80)

    print(
        f"Correctas: {correctos}/{len(resultados)}"
    )

    # =====================================================
    # RECUPERACIÓN FINAL
    # =====================================================

    consulta = (
        "¿Qué sabes sobre las articulaciones "
        "de las patas de Atenas?"
    )

    print()
    print("=" * 80)
    print(" RECUPERACIÓN FINAL")
    print("=" * 80)

    print()
    print(
        "Consulta:",
        consulta
    )

    memorias = (
        recuperador.buscar(
            consulta,
            limite=10,
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
            or ""
        )

        print()
        print(
            f"{numero}. {contenido}"
        )

        print(
            "   ID:",
            memoria.get("id")
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
            "   Similitud:",
            round(
                float(
                    memoria.get(
                        "similitud_semantica",
                        0.0,
                    )
                    or 0.0
                ),
                4,
            )
        )

    print()
    print("=" * 80)
    print(" TEST FINALIZADO")
    print("=" * 80)


if __name__ == "__main__":
    main()