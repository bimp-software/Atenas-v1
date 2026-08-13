from __future__ import annotations


CATALOGO_HERRAMIENTAS = {
    "crear_nota": {
        "descripcion": (
            "Guarda información en una nota persistente "
            "del sistema de ATENAS."
        ),
        "argumentos": {
            "contenido": "str",
        },
        "riesgo": "bajo",
    },

    "abrir_programa": {
        "descripcion": (
            "Abre una aplicación permitida en Windows."
        ),
        "argumentos": {
            "programa": "str",
        },
        "riesgo": "bajo",
    },

    "escribir_texto": {
        "descripcion": (
            "Escribe texto en la aplicación que tenga "
            "el foco actualmente."
        ),
        "argumentos": {
            "texto": "str",
            "espera_antes": "float opcional",
        },
        "riesgo": "bajo",
    },

    "buscar_web": {
        "descripcion": (
            "Busca información pública actual "
            "en Internet y devuelve resultados "
            "estructurados."
        ),
        "argumentos": {
            "consulta": "str",
            "limite": "int opcional",
        },
        "riesgo": "bajo",
    },
}


def catalogo_para_llm() -> str:

    bloques = []

    for nombre, datos in CATALOGO_HERRAMIENTAS.items():

        argumentos = ", ".join(
            f"{clave}: {tipo}"
            for clave, tipo
            in datos["argumentos"].items()
        )

        bloques.append(
            f"{nombre}\n"
            f"Descripción: {datos['descripcion']}\n"
            f"Argumentos: {argumentos}\n"
            f"Riesgo: {datos['riesgo']}"
        )

    return "\n\n".join(bloques)