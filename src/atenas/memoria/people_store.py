from __future__ import annotations
from .database import Database

class PeopleStore:
    def __init__(self,db: Database | None = None,):
        self.db = db or Database()

    def obtener_o_crear(self,nombre: str,relacion: str | None = None,descripcion: str | None = None,importancia: float = 0.5,) -> int:
        nombre = nombre.strip()
        existente = self.buscar( nombre)

        if existente: return existente["id"]

        with self.db.conexion() as conn:
            cursor = conn.execute("""INSERT INTO personas (nombre,relacion,descripcion,importancia) VALUES (?, ?, ?, ?)""", ( nombre, relacion, descripcion,importancia,))
            return int(cursor.lastrowid)

    def buscar(self, nombre: str,) -> dict | None:
        with self.db.conexion() as conn:
            row = conn.execute("""SELECT * FROM personas WHERE LOWER(nombre) = LOWER(?) LIMIT 1""", ( nombre.strip())).fetchone()
        return dict(row) if row else None

    def agregar_dato(self,nombre: str,clave: str,valor: str,confianza: float = 0.7,) -> int:
        persona_id = self.obtener_o_crear(nombre)

        with self.db.conexion() as conn:
            cursor = conn.execute("""INSERT OR IGNORE INTO persona_datos (persona_id,clave,valor,confianza) VALUES (?, ?, ?, ?)""", (persona_id,clave.lower(),valor,confianza,))
            return int(cursor.lastrowid or persona_id)

    def obtener_datos( self, nombre: str,) -> list[dict]:
        persona = self.buscar( nombre)
        if not persona: return []

        with self.db.conexion() as conn:
            rows = conn.execute("""SELECT * FROM persona_datos WHERE persona_id = ? ORDER BY actualizado_en DESC""", (persona["id"],)).fetchall()

        return [ dict(row) for row in rows ]