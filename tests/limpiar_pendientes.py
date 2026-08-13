from src.atenas.memoria.database import Database


def main():

    db = Database()

    with db.conexion() as conn:

        cursor = conn.execute(
            """
            UPDATE agent_tasks

            SET
                estado = ?,
                resultado = ?,
                actualizado_en = CURRENT_TIMESTAMP

            WHERE estado IN (?, ?)
            """,
            (
                "completado",
                "Pendiente cerrado durante la limpieza del entorno de pruebas.",
                "pendiente",
                "en_proceso",
            ),
        )

        cantidad = cursor.rowcount

        conn.commit()

    print()
    print("=" * 50)
    print(" LIMPIEZA DE PENDIENTES - ATENAS")
    print("=" * 50)
    print()
    print(f"Pendientes cerrados: {cantidad}")
    print()
    print("Limpieza completada correctamente.")


if __name__ == "__main__":
    main()