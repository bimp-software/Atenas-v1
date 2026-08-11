from __future__ import annotations
from .database import Database

class EpisodicStore:
    def __init__( self,db: Database | None = None,):
        self.db = db or Database()

    def guardar(self,descripcion: str,lugar: str | None = None,personas: str | None = None,contexto: str | None = None,importancia: float = 0.5,confianza: float = 0.7,fuente: str = "experiencia",) -> int:
        with self.db.conexion() as conn:
            cursor = conn.execute("""INSERT INTO memoria_episodica (descripcion,lugar,personas,contexto,importancia,confianza,fuente) VALUES (?, ?, ?, ?, ?, ?, ?)""", (descripcion.strip(),lugar,personas,contexto,importancia,confianza,fuente,))
            return int(cursor.lastrowid)

    def buscar(self,consulta: str,limite: int = 10) -> list[dict]:
        palabras = [ p.lower().strip(".,;:¿?¡!") for p in consulta.split() if len(p.strip(".,;:¿?¡!")) >= 3]
        if not palabras: return []

        condiciones = []
        parametros = []

        for palabra in palabras:
            condiciones.append("""( LOWER(descripcion) LIKE ? OR LOWER(contexto) LIKE ? OR LOWER(personas) LIKE ? OR LOWER(lugar) LIKE ?)""")
            patron = f"%{palabra}%"
            parametros.extend([ patron, patron, patron, patron,])

        parametros.append(limite)
        sql = f""" SELECT *FROM memoria_episodica WHERE {" OR ".join(condiciones)} ORDER BY importancia DESC, creado_en DESC LIMIT ?"""

        with self.db.conexion() as conn:
            rows = conn.execute( sql, parametros,).fetchall()

        return [ dict(row) for row in rows ]