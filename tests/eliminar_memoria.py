# tests/eliminar_memoria.py

from pathlib import Path

from src.atenas.memoria.database import Database


MEMORIA_ID = 3
TIPO = "semantica"

db = Database()

with db.conexion() as conn:

    conn.execute("""
        DELETE FROM memory_concepts
        WHERE memoria_tipo = ?
          AND memoria_id = ?
    """, (
        TIPO,
        MEMORIA_ID,
    ))

    row = conn.execute("""
        SELECT vector_path
        FROM vector_memories
        WHERE memoria_tipo = ?
          AND memoria_id = ?
    """, (
        TIPO,
        MEMORIA_ID,
    )).fetchone()

    if row:
        ruta = Path(row["vector_path"])

        if ruta.exists():
            ruta.unlink()

    conn.execute("""
        DELETE FROM vector_memories
        WHERE memoria_tipo = ?
          AND memoria_id = ?
    """, (
        TIPO,
        MEMORIA_ID,
    ))

    conn.execute("""
        DELETE FROM memoria_semantica
        WHERE id = ?
    """, (
        MEMORIA_ID,
    ))

print("Memoria eliminada.")