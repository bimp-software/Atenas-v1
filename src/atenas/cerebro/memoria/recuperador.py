from __future__ import annotations

from src.atenas.memoria.store_manager import StorageManager
from .clasificador import ClasificadorMemoria


class RecuperadorMemoria:
    def __init__(self,storage: StorageManager | None = None):
        self.storage = (storage or StorageManager())
        self.clasificador = (ClasificadorMemoria())

    # =========================================================
    # RECORDAR
    # =========================================================

    def buscar(self,consulta: str,limite: int = 8,) -> list[dict]:

        clasificacion = (self.clasificador.clasificar(consulta))
        resultados = []

        if (clasificacion.dominio not in {"general","experiencias",}):
            resultados.extend(
                self.storage.semantica.buscar(
                    consulta=consulta,
                    dominio=clasificacion.dominio,
                    limite=limite,
                )
            )

        if len(resultados) < limite:

            generales = (
                self.storage.semantica.buscar(
                    consulta=consulta,
                    limite=limite,
                )
            )

            ids_existentes = {
                x["id"]
                for x in resultados
            }

            for memoria in generales:
                if memoria["id"] not in ids_existentes:
                    resultados.append(memoria)

                if len(resultados) >= limite:
                    break

        episodios = (self.storage.episodica.buscar(consulta,limite=3,))

        for episodio in episodios:
            resultados.append({**episodio,"_tipo_memoria": "episodica",})

        return resultados[:limite]

    def contexto_para_llm(self,consulta: str,limite: int = 6,) -> str:
        memorias = self.buscar(consulta,limite=limite,)
        if not memorias: return ""
        lineas = []
        for memoria in memorias:
            contenido = (memoria.get("contenido") or memoria.get("descripcion"))
            if contenido: lineas.append(f"- {contenido}")

        contexto_grafo = (self.storage.grafo.contexto_para_llm(consulta))

        bloques = []

        if not lineas: return ""
        if lineas: 
            bloques.append("MEMORIAS RELEVANTES DE ATENAS:\n\n".join(lineas))

        if contexto_grafo:
            bloques.append(contexto_grafo)

        if not bloques: return ""

        return (
            + "\n\n".join(bloques)
            + "\n\n"
            "Utiliza esta información solo cuando "
            "sea relevante para responder. "
            "No inventes relaciones que no aparezcan "
            "en la memoria o el grafo."
        )