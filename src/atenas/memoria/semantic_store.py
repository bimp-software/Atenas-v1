from __future__ import annotations

from .database import Database

class SemanticStore:
    def __init__(self, db: Database | None = None):
        self.db = db or Database()

    def guardar(self,contenido: str,dominio: str = "general",categoria: str = "general",subcategoria: str | None = None,fuente: str = "usuario",importancia: float = 0.5,confianza: float = 0.5,relevancia: float = 0.5,protegida: bool = False,) -> int:
        contenido = contenido.strip()
        existente = self.buscar_exacta(contenido)
        if existente:
            self.reforzar(existente["id"])
            return existente["id"]

        with self.db.conexion() as conn:
            cursor = conn.execute("""INSERT INTO memoria_semantica (contenido,dominio,categoria,subcategoria,fuente,importancia,confianza,relevancia,protegida)VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (contenido,dominio.lower(),categoria.lower(),( subcategoria.lower() if subcategoria else None ), fuente,importancia,confianza,relevancia, 1 if protegida else 0,))
            return int(cursor.lastrowid)

    def buscar_exacta(self,contenido: str) -> dict | None:
        with self.db.conexion() as conn:
            row = conn.execute("""SELECT * FROM memoria_semantica WHERE LOWER(contenido) = LOWER(?) AND activa = 1 LIMIT 1""", ( contenido.strip(),)).fetchone()
        return dict(row) if row else None

    def buscar(self,consulta: str,dominio: str | None = None,limite: int = 10) -> list[dict]:
        palabras = [ p.lower().strip(".,;:¿?¡!") for p in consulta.split() if len(p.strip(".,;:¿?¡!")) >= 3]
        if not palabras: return []
        condiciones = []
        parametros = []

        for palabra in palabras:
            condiciones.append("LOWER(contenido) LIKE ?")
            parametros.append(f"%{palabra}%")

        where = ("(" + " OR ".join(condiciones) + ") AND activa = 1")

        if dominio:
            where += " AND LOWER(dominio) = LOWER(?)"
            parametros.append(dominio)

        parametros.append(limite)

        consulta_sql = f"""SELECT * FROM memoria_semantica WHERE {where} ORDER BY relevancia DESC,importancia DESC,veces_usado DESC,actualizado_en DESC LIMIT ?"""
        with self.db.conexion() as conn:
            rows = conn.execute(consulta_sql,parametros,).fetchall()
        return [dict(row) for row in rows]

    def por_dominio(self,dominio: str,limite: int = 50,) -> list[dict]:
        with self.db.conexion() as conn:
            rows = conn.execute("""SELECT * FROM memoria_semantica WHERE LOWER(dominio) = LOWER(?) AND activa = 1 ORDER BY importancia DESC, veces_usado DESC LIMIT ? """, (dominio,limite,)).fetchall()
        return [dict(row) for row in rows]

    def reforzar(self,memoria_id: int,) -> None:
        with self.db.conexion() as conn:
            conn.execute(""" UPDATE memoria_semantica SET veces_usado = veces_usado + 1, actualizado_en = CURRENT_TIMESTAMP, relevancia = MIN( relevancia + 0.02, 1.0 ) WHERE id = ?""", ( memoria_id,))