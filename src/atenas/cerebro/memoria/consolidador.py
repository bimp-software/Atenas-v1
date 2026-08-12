from __future__ import annotations

from src.atenas.memoria.store_manager import StorageManager
from .relevancia import EvaluadorRelevancia

class ConsolidadorMemoria:
    def __init__(self,storage: StorageManager | None = None,):
        self.storage = (storage or StorageManager())
        self.relevancia = (EvaluadorRelevancia())

    def consolidar( self,experiencia,) -> dict:
        score = self.relevancia.calcular(experiencia.contenido)

        if score < 0.35: return {"guardada": False,"motivo": "baja_relevancia","relevancia": score,}

        if experiencia.tipo == "episodica":
            memoria_id = (
                self.storage.episodica.guardar(
                    descripcion=experiencia.contenido,
                    contexto=experiencia.contexto,
                    importancia=max(
                        experiencia.importancia,
                        score,
                    ),
                    confianza=experiencia.confianza,
                    fuente=experiencia.fuente,
                )
            )

            tipo = "episodica"

        else:

            memoria_id = (
                self.storage.semantica.guardar(
                    contenido=experiencia.contenido,
                    dominio=(experiencia.dominio or "general"),
                    categoria=(experiencia.subcategoria or experiencia.tipo or "general"),
                    fuente=experiencia.fuente,
                    importancia=max(experiencia.importancia,score),
                    confianza=experiencia.confianza,
                    relevancia=score,
                )
            )

            tipo = "semantica"


        self.storage.registrar_evento(
            tipo="memory.created",
            memoria_tipo=tipo,
            memoria_id=memoria_id,
            descripcion=experiencia.contenido,
        )

        try:
            self.storage.grafo.procesar_memoria(
                memoria_tipo=tipo,
                memoria_id=memoria_id,
                contenido=experiencia.contenido,
                dominio=(experiencia.dominio or "general"),
                categoria=(experiencia.subcategoria or experiencia.tipo or "general"),
                importancia=max(experiencia.importancia,score,),
                confianza=(experiencia.confianza),
            )

        except Exception as error:
            print(f"[ATENAS][GRAFO] No fue posible actualizar el grafo: {error}")

        try:
            self.storage.vectores.guardar(
                memoria_tipo=tipo,
                memoria_id=memoria_id,
                contenido=experiencia.contenido,
                dominio=(experiencia.dominio or "general"),
                categoria=(experiencia.subcategoria or experiencia.tipo or "general"),
                importancia=max(experiencia.importancia,score,),
                confianza=(experiencia.confianza),
            )

        except Exception as error:
            print(f"[ATENAS][VECTOR] No fue posible generar la memoria vectorial: {error}")

        return {"guardada": True,"id": memoria_id,"tipo": tipo,"relevancia": score,}
