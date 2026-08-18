from __future__ import annotations

from src.atenas.memoria.database import Database


IDS_PRUEBA = (
    25,
    26,
    27,
    28,
)


def main():

    print()
    print("=" * 70)
    print(" LIMPIEZA TEST DEDUPLICACIÓN - ATENAS")
    print("=" * 70)

    db = Database()

    with db.conexion() as conn:

        for memoria_id in IDS_PRUEBA:

            # =============================================
            # DESACTIVAR MEMORIA SEMÁNTICA
            # =============================================

            conn.execute(
                """
                UPDATE memoria_semantica
                SET activa = 0
                WHERE id = ?
                """,
                (
                    memoria_id,
                ),
            )

            # =============================================
            # ELIMINAR VECTOR
            # =============================================

            conn.execute(
                """
                DELETE FROM vector_memories
                WHERE memoria_tipo = 'semantica'
                  AND memoria_id = ?
                """,
                (
                    memoria_id,
                ),
            )

            # =============================================
            # ELIMINAR RELACIONES MEMORIA-CONCEPTO
            # =============================================

            conn.execute(
                """
                DELETE FROM memory_concepts
                WHERE memoria_tipo = 'semantica'
                  AND memoria_id = ?
                """,
                (
                    memoria_id,
                ),
            )

            print(
                f"Memoria {memoria_id} limpiada."
            )

        conn.commit()

    print()
    print("Limpieza terminada.")


if __name__ == "__main__":
    main()