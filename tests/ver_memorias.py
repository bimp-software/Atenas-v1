# tests/ver_memorias.py

from src.atenas.memoria.database import Database


db = Database()

with db.conexion() as conn:
    rows = conn.execute("""
        SELECT id, contenido, dominio
        FROM memoria_semantica
        ORDER BY id
    """).fetchall()

for row in rows:
    print(
        row["id"],
        "|",
        row["dominio"],
        "|",
        row["contenido"]
    )