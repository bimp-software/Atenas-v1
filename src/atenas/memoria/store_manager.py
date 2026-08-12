from __future__ import annotations

from .database import Database
from .semantic_store import SemanticStore
from .episodic_store import EpisodicStore
from .people_store import PeopleStore
from .knowledge_graph import KnowledgeGraph
from .vector_store import VectorStore

class StorageManager:

    def __init__(self):
        self.db = Database()
        self.semantica = SemanticStore(self.db)
        self.episodica = EpisodicStore(self.db)
        self.personas = PeopleStore(self.db)
        self.grafo = KnowledgeGraph(self.db)
        self.vectores = VectorStore(self.db)

    def registrar_evento(self,tipo: str,memoria_tipo: str | None = None,memoria_id: int | None = None,descripcion: str | None = None,) -> None:
        with self.db.conexion() as conn:
            conn.execute("""INSERT INTO eventos_memoria (tipo,memoria_tipo,memoria_id,descripcion) VALUES (?, ?, ?, ?)""", (tipo,memoria_tipo,memoria_id,descripcion))