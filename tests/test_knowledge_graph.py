from src.atenas.memoria.database import Database
from src.atenas.memoria.knowledge_graph import KnowledgeGraph


def mostrar_relaciones(
    grafo: KnowledgeGraph,
    concepto: str,
):
    print(f"\nRELACIONES DE: {concepto}")
    print("-" * 50)

    relaciones = grafo.vecinos(
        concepto,
        limite=20,
    )

    if not relaciones:
        print("No existen relaciones.")
        return

    for relacion in relaciones:
        print(
            f"{concepto} "
            f"--{relacion['relacion']}--> "
            f"{relacion['nombre']} "
            f"(peso={relacion['peso']:.2f})"
        )


def main():
    print("\n===================================")
    print(" TEST KNOWLEDGE GRAPH - ATENAS")
    print("===================================\n")

    db = Database()
    grafo = KnowledgeGraph(db)

    # ----------------------------------------
    # Memoria robótica
    # ----------------------------------------

    grafo.procesar_memoria(
        memoria_tipo="test",
        memoria_id=9001,
        contenido=(
            "Estoy desarrollando el cuerpo de Atenas "
            "como un robot araña y quiero que sus patas "
            "tengan cuatro articulaciones."
        ),
        dominio="robotica",
        categoria="locomocion",
        importancia=0.9,
        confianza=0.95,
    )

    # ----------------------------------------
    # Memoria informática
    # ----------------------------------------

    grafo.procesar_memoria(
        memoria_tipo="test",
        memoria_id=9002,
        contenido=(
            "Estoy utilizando Python y Flask "
            "para crear la interfaz de Atenas."
        ),
        dominio="informatica",
        categoria="programacion",
        importancia=0.85,
        confianza=0.95,
    )

    mostrar_relaciones(
        grafo,
        "patas"
    )

    mostrar_relaciones(
        grafo,
        "interfaz"
    )

    mostrar_relaciones(
        grafo,
        "flask"
    )

    mostrar_relaciones(
        grafo,
        "atenas"
    )

    print("\n===================================")
    print(" CONTEXTO PARA LLM")
    print("===================================\n")

    contexto = grafo.contexto_para_llm(
        "¿Qué sabes de las patas y "
        "articulaciones del cuerpo de Atenas?"
    )

    print(contexto)

    print("\n===================================")
    print(" ESTADÍSTICAS DEL GRAFO")
    print("===================================\n")

    datos = grafo.exportar()

    print(
        "Nodos:",
        len(datos["nodes"])
    )

    print(
        "Relaciones:",
        len(datos["edges"])
    )


if __name__ == "__main__":
    main()