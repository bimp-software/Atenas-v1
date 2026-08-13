from src.atenas.memoria.database import Database


CONSULTAS_BASURA = (
    "que cuentas",
    "qué cuentas",
    "no",
    "como te llamas",
    "cómo te llamas",
    "sabes ingles",
    "sabes inglés",
)


def main():

    db = Database()

    print()
    print("=" * 70)
    print(" LIMPIEZA DE INVESTIGACIONES BASURA - ATENAS")
    print("=" * 70)

    eliminadas = 0

    with db.conexion() as conn:

        rows = conn.execute("""
            SELECT
                id,
                consulta,
                memoria_id
            FROM investigaciones_web
        """).fetchall()

        for row in rows:

            consulta = (
                row["consulta"]
                or ""
            ).lower().strip()

            es_basura = any(
                frase == consulta
                or frase in consulta
                for frase in CONSULTAS_BASURA
            )

            if not es_basura:
                continue

            print()
            print(
                "Eliminando investigación:",
                row["consulta"]
            )

            memoria_id = (
                row["memoria_id"]
            )

            # =============================================
            # DESACTIVAR MEMORIA GENERADA
            # =============================================

            if memoria_id is not None:

                conn.execute("""
                    UPDATE memoria_semantica
                    SET activa = 0
                    WHERE id = ?
                """, (
                    memoria_id,
                ))

                conn.execute("""
                    DELETE FROM vector_memories
                    WHERE memoria_tipo = 'semantica'
                      AND memoria_id = ?
                """, (
                    memoria_id,
                ))

                conn.execute("""
                    DELETE FROM memory_concepts
                    WHERE memoria_tipo = 'semantica'
                      AND memoria_id = ?
                """, (
                    memoria_id,
                ))

            # =============================================
            # ELIMINAR REGISTRO DE INVESTIGACIÓN
            # =============================================

            conn.execute("""
                DELETE FROM investigaciones_web
                WHERE id = ?
            """, (
                row["id"],
            ))

            eliminadas += 1

        conn.commit()

    print()
    print("=" * 70)
    print(
        "Investigaciones basura eliminadas:",
        eliminadas
    )
    print("=" * 70)


if __name__ == "__main__":
    main()