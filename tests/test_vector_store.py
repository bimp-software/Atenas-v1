from src.atenas.memoria.database import Database
from src.atenas.memoria.vector_store import VectorStore

def main():
    print("\n===================================")
    print(" TEST VECTOR STORE - ATENAS")
    print("===================================\n")

    db = Database()
    vectores = VectorStore(db)

    print("Indexando memorias existentes...\n")

    resultado = vectores.indexar_existentes()

    print("Creadas:", resultado["creadas"])
    print("Ya existentes:", resultado["existentes"])
    print("Errores:", resultado["errores"])

    consultas = [
        "¿Cómo serán las extremidades de tu cuerpo?",
        "¿Qué tecnologías estoy usando para tu interfaz?",
        "¿Cómo se moverá tu robot?",
        "¿Con qué estoy desarrollando tu página?",
        "¿Qué sabes sobre las articulaciones de tu cuerpo?",
    ]

    for consulta in consultas:
        print("\n-----------------------------------")
        print("CONSULTA:")
        print(consulta)
        print("-----------------------------------")

        resultados = vectores.buscar(
            consulta,
            limite=5,
            similitud_minima=0.25,
        )

        if not resultados:
            print("Sin resultados.")
            continue

        for i, memoria in enumerate(resultados, start=1):
            print(
                f"\n{i}. Similitud: "
                f"{memoria['similitud_semantica']:.3f}"
            )

            print(
                "Dominio:",
                memoria.get("dominio")
            )

            print(
                "Contenido:",
                memoria.get("contenido")
            )


if __name__ == "__main__":
    main()