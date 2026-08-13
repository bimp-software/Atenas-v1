from __future__ import annotations

import sqlite3
from pathlib import Path
from contextlib import contextmanager

class Database:
    def __init__(self, ruta: str = "src/data/atenas.db"):
        self.ruta = ruta
        Path(self.ruta).parent.mkdir(parents=True, exist_ok=True)
        self._crear_tablas()

    @contextmanager
    def conexion(self):
        conn = sqlite3.connect(self.ruta, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _asegurar_columna(
        self,
        conn,
        tabla: str,
        columna: str,
        definicion: str,
    ) -> None:
        """
        Añade una columna a una tabla existente si todavía
        no está presente.

        Permite migraciones pequeñas sin borrar la memoria
        existente de ATENAS.
        """

        columnas = conn.execute(
            f"PRAGMA table_info({tabla})"
        ).fetchall()

        nombres = {
            fila["name"]
            for fila in columnas
        }

        if columna not in nombres:
            conn.execute(
                f"""
                ALTER TABLE {tabla}
                ADD COLUMN {columna} {definicion}
                """
            )
        

    def _crear_tablas(self):
        with self.conexion() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memoria_semantica (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contenido TEXT NOT NULL,
                    dominio TEXT NOT NULL DEFAULT 'general',
                    categoria TEXT NOT NULL DEFAULT 'general',
                    subcategoria TEXT,
                    fuente TEXT DEFAULT 'usuario',
                    importancia REAL DEFAULT 0.5,
                    confianza REAL DEFAULT 0.5,
                    relevancia REAL DEFAULT 0.5,
                    veces_usado INTEGER DEFAULT 0,
                    protegida INTEGER DEFAULT 0,
                    activa INTEGER DEFAULT 1,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memoria_episodica (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    descripcion TEXT NOT NULL,
                    lugar TEXT,
                    personas TEXT,
                    contexto TEXT,
                    importancia REAL DEFAULT 0.5,
                    confianza REAL DEFAULT 0.5,
                    fuente TEXT DEFAULT 'experiencia',
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS personas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    relacion TEXT,
                    descripcion TEXT,
                    importancia REAL DEFAULT 0.5,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS persona_datos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    persona_id INTEGER NOT NULL,
                    clave TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    confianza REAL DEFAULT 0.5,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(persona_id) REFERENCES personas(id),
                    UNIQUE(persona_id, clave, valor)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS categorias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    padre TEXT,
                    veces_usada INTEGER DEFAULT 0,
                    creada_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(nombre, padre)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS eventos_memoria (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    memoria_tipo TEXT,
                    memoria_id INTEGER,
                    descripcion TEXT,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS curiosidades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tema TEXT NOT NULL UNIQUE,
                    motivo TEXT,
                    novedad REAL DEFAULT 0.5,
                    incertidumbre REAL DEFAULT 0.5,
                    frecuencia INTEGER DEFAULT 1,
                    puntuacion REAL DEFAULT 0.5,
                    resuelta INTEGER DEFAULT 0,
                    creada_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    actualizada_en DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_semantica_dominio ON memoria_semantica(dominio)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_semantica_categoria ON memoria_semantica(categoria)
            """)
            
            ##GRAFO
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    tipo TEXT NOT NULL DEFAULT 'concepto',
                    dominio TEXT,
                    categoria TEXT,
                    importancia REAL DEFAULT 0.5,
                    confianza REAL DEFAULT 0.5,
                    veces_usado INTEGER DEFAULT 1,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(nombre, tipo)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    origen_id INTEGER NOT NULL,
                    destino_id INTEGER NOT NULL,
                    relacion TEXT NOT NULL,
                    peso REAL DEFAULT 1.0,
                    confianza REAL DEFAULT 0.7,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(origen_id) REFERENCES knowledge_nodes(id),
                    FOREIGN KEY(destino_id) REFERENCES knowledge_nodes(id),
                    UNIQUE(origen_id,destino_id,relacion)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_concepts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memoria_tipo TEXT NOT NULL,
                    memoria_id INTEGER NOT NULL,
                    concepto_id INTEGER NOT NULL,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(concepto_id) REFERENCES knowledge_nodes(id),
                    UNIQUE(memoria_tipo,memoria_id,concepto_id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_knowledge_nombre
                ON knowledge_nodes(nombre)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_edges_origen
                ON knowledge_edges(origen_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_edges_destino
                ON knowledge_edges(destino_id)
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS vector_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memoria_tipo TEXT NOT NULL,
                    memoria_id INTEGER NOT NULL,
                    contenido TEXT NOT NULL,
                    dominio TEXT,
                    categoria TEXT,
                    vector_path TEXT NOT NULL,
                    modelo TEXT NOT NULL,
                    dimensiones INTEGER NOT NULL,
                    importancia REAL DEFAULT 0.5,
                    confianza REAL DEFAULT 0.7,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(memoria_tipo,memoria_id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_memoria
                ON vector_memories(memoria_tipo,memoria_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_vector_dominio
                ON vector_memories(dominio)
            """)

            ##AGENTE

            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_objectives (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    prioridad REAL DEFAULT 0.5,
                    estado TEXT DEFAULT 'activo',
                    autonomia INTEGER DEFAULT 1,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    id TEXT PRIMARY KEY,
                    descripcion TEXT NOT NULL,
                    objetivo_id TEXT,
                    prioridad REAL DEFAULT 0.5,
                    estado TEXT DEFAULT 'pendiente',
                    requiere_confirmacion INTEGER DEFAULT 0,
                    resultado TEXT,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    actualizado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(objetivo_id)
                        REFERENCES agent_objectives(id)
                )
            """)

            self._asegurar_columna(
                conn,
                "agent_tasks",
                "accion_sugerida",
                "TEXT",
            )

            self._asegurar_columna(
                conn,
                "agent_tasks",
                "mensaje_origen",
                "TEXT",
            )

            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pendiente_id TEXT,
                    herramienta TEXT NOT NULL,
                    argumentos TEXT,
                    exito INTEGER DEFAULT 0,
                    resultado TEXT,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(pendiente_id)
                        REFERENCES agent_tasks(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS investigaciones_web (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    consulta TEXT NOT NULL,
                    sintesis TEXT NOT NULL,
                    fuentes_json TEXT NOT NULL,
                    confianza REAL DEFAULT 0.75,
                    memoria_id INTEGER,
                    creado_en DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_investigaciones_consulta
                ON investigaciones_web(consulta)
            """)

            self._asegurar_columna(
                conn,
                "investigaciones_web",
                "tipo_vigencia",
                "TEXT DEFAULT 'media'",
            )

            self._asegurar_columna(
                conn,
                "investigaciones_web",
                "revisar_despues_dias",
                "INTEGER DEFAULT 30",
            )

            self._asegurar_columna(
                conn,
                "investigaciones_web",
                "ultima_verificacion",
                "DATETIME",
            )
