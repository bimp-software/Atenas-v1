from __future__ import annotations

import re
import unicodedata

from .database import Database


class KnowledgeGraph:
    PALABRAS_VACIAS = {
        "a", "al", "algo", "como", "con", "contra",
        "de", "del", "desde", "donde", "el", "ella",
        "en", "entre", "era", "es", "esa", "ese",
        "esta", "este", "esto", "estos", "fue",
        "ha", "hay", "la", "las", "le", "lo",
        "los", "me", "mi", "mis", "muy", "no",
        "nos", "o", "para", "pero", "por", "porque",
        "que", "qué", "se", "si", "sin", "sobre",
        "su", "sus", "te", "tu", "tus", "un",
        "una", "uno", "unos", "unas", "y", "ya",
        "yo",
    }

    CONCEPTOS_CONOCIDOS = {
        # IA / software
        "python": ("tecnologia", "informatica"),
        "flask": ("framework", "informatica"),
        "ollama": ("software", "inteligencia_artificial"),
        "qwen": ("modelo_llm", "inteligencia_artificial"),
        "qwen3": ("modelo_llm", "inteligencia_artificial"),
        "llm": ("concepto", "inteligencia_artificial"),
        "inteligencia artificial": (
            "disciplina",
            "informatica",
        ),
        "base de datos": (
            "tecnologia",
            "informatica",
        ),
        "sqlite": (
            "base_de_datos",
            "informatica",
        ),

        # Robótica
        "robot": ("concepto", "robotica"),
        "robot araña": ("robot", "robotica"),
        "spider-bot": ("robot", "robotica"),
        "spiderbot": ("robot", "robotica"),
        "pata": ("componente", "robotica"),
        "patas": ("componente", "robotica"),
        "articulación": ("componente", "robotica"),
        "articulaciones": ("componente", "robotica"),
        "servomotor": ("actuador", "robotica"),
        "servomotores": ("actuador", "robotica"),
        "servo": ("actuador", "robotica"),
        "cámara": ("sensor", "vision"),
        "camara": ("sensor", "vision"),
        "micrófono": ("sensor", "audio"),
        "microfono": ("sensor", "audio"),
        "parlante": ("actuador", "audio"),
        "sensor": ("sensor", "robotica"),
        "sensores": ("sensor", "robotica"),
        "esp32": ("microcontrolador", "electronica"),
        "arduino": ("microcontrolador", "electronica"),
        "pwm": ("señal", "electronica"),

        # Atenas
        "atenas": ("entidad", "sistema"),
        "interfaz": ("componente", "software"),
        "memoria": ("componente", "sistema"),
        "voz": ("capacidad", "sistema"),
        "visión": ("capacidad", "sistema"),
        "vision": ("capacidad", "sistema"),
    }

    FRASES_CONOCIDAS = tuple(
        sorted(
            CONCEPTOS_CONOCIDOS.keys(),
            key=len,
            reverse=True,
        )
    )

    def __init__(
        self,
        db: Database | None = None,
    ):
        self.db = db or Database()

        self._crear_nucleo()

    # =========================================================
    # NORMALIZACIÓN
    # =========================================================

    @staticmethod
    def _normalizar(texto: str) -> str:
        texto = texto.strip().lower()

        texto = unicodedata.normalize(
            "NFKC",
            texto,
        )

        texto = re.sub(
            r"\s+",
            " ",
            texto,
        )

        return texto

    # =========================================================
    # CREAR / OBTENER NODO
    # =========================================================

    def obtener_o_crear_nodo(
        self,
        nombre: str,
        tipo: str = "concepto",
        dominio: str | None = None,
        categoria: str | None = None,
        importancia: float = 0.5,
        confianza: float = 0.7,
    ) -> int:

        nombre = self._normalizar(nombre)

        if not nombre:
            raise ValueError(
                "El nombre del concepto está vacío."
            )

        with self.db.conexion() as conn:

            existente = conn.execute("""
                SELECT id
                FROM knowledge_nodes

                WHERE LOWER(nombre) = LOWER(?)
                  AND tipo = ?

                LIMIT 1
            """, (
                nombre,
                tipo,
            )).fetchone()

            if existente:

                node_id = int(
                    existente["id"]
                )

                conn.execute("""
                    UPDATE knowledge_nodes

                    SET
                        veces_usado = veces_usado + 1,
                        importancia = MAX(
                            importancia,
                            ?
                        ),
                        confianza = MAX(
                            confianza,
                            ?
                        ),
                        actualizado_en =
                            CURRENT_TIMESTAMP

                    WHERE id = ?
                """, (
                    importancia,
                    confianza,
                    node_id,
                ))

                return node_id

            cursor = conn.execute("""
                INSERT INTO knowledge_nodes (
                    nombre,
                    tipo,
                    dominio,
                    categoria,
                    importancia,
                    confianza
                )

                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                nombre,
                tipo,
                dominio,
                categoria,
                importancia,
                confianza,
            ))

            return int(
                cursor.lastrowid
            )

    # =========================================================
    # RELACIONES
    # =========================================================

    def relacionar(
        self,
        origen_id: int,
        destino_id: int,
        relacion: str,
        peso: float = 1.0,
        confianza: float = 0.7,
    ) -> int | None:

        if origen_id == destino_id:
            return None

        relacion = self._normalizar(
            relacion
        )

        with self.db.conexion() as conn:

            existente = conn.execute("""
                SELECT id
                FROM knowledge_edges

                WHERE origen_id = ?
                  AND destino_id = ?
                  AND relacion = ?

                LIMIT 1
            """, (
                origen_id,
                destino_id,
                relacion,
            )).fetchone()

            if existente:

                edge_id = int(
                    existente["id"]
                )

                conn.execute("""
                    UPDATE knowledge_edges

                    SET
                        peso = MIN(
                            peso + 0.1,
                            10.0
                        ),
                        confianza = MAX(
                            confianza,
                            ?
                        ),
                        actualizado_en =
                            CURRENT_TIMESTAMP

                    WHERE id = ?
                """, (
                    confianza,
                    edge_id,
                ))

                return edge_id

            cursor = conn.execute("""
                INSERT INTO knowledge_edges (
                    origen_id,
                    destino_id,
                    relacion,
                    peso,
                    confianza
                )

                VALUES (?, ?, ?, ?, ?)
            """, (
                origen_id,
                destino_id,
                relacion,
                peso,
                confianza,
            ))

            return int(
                cursor.lastrowid
            )

    # =========================================================
    # NÚCLEO BASE
    # =========================================================

    def _crear_nucleo(self) -> None:

        atenas = self.obtener_o_crear_nodo(
            "atenas",
            tipo="entidad",
            dominio="sistema",
            importancia=1.0,
            confianza=1.0,
        )

        dominios = (
            "informatica",
            "robotica",
            "electronica",
            "vision",
            "audio",
            "personas",
            "experiencias",
            "educacion",
            "ciencia",
            "general",
        )

        for dominio in dominios:

            nodo = self.obtener_o_crear_nodo(
                dominio,
                tipo="dominio",
                dominio=dominio,
                importancia=0.7,
                confianza=1.0,
            )

            self.relacionar(
                atenas,
                nodo,
                "conocimiento_en",
                confianza=1.0,
            )

    # =========================================================
    # EXTRAER CONCEPTOS
    # =========================================================

    def extraer_conceptos(
        self,
        texto: str,
        dominio: str = "general",
        categoria: str = "general",
    ) -> list[dict]:

        texto_normalizado = (
            self._normalizar(texto)
        )

        conceptos: dict[str, dict] = {}

        # -----------------------------------------------------
        # CONCEPTOS / FRASES QUE YA CONOCEMOS
        # -----------------------------------------------------

        for concepto in self.FRASES_CONOCIDAS:

            if concepto in texto_normalizado:

                tipo, dominio_concepto = (
                    self.CONCEPTOS_CONOCIDOS[
                        concepto
                    ]
                )

                conceptos[concepto] = {
                    "nombre": concepto,
                    "tipo": tipo,
                    "dominio": dominio_concepto,
                    "categoria": categoria,
                    "confianza": 0.9,
                }

        # -----------------------------------------------------
        # CANTIDAD DE ARTICULACIONES
        # -----------------------------------------------------

        patrones_articulaciones = [
            r"(\d+)\s+articulaciones",
            r"(una|dos|tres|cuatro|cinco|seis)\s+articulaciones",
        ]

        numeros_texto = {
            "una": 1,
            "dos": 2,
            "tres": 3,
            "cuatro": 4,
            "cinco": 5,
            "seis": 6,
        }

        for patron in patrones_articulaciones:

            match = re.search(
                patron,
                texto_normalizado,
            )

            if not match:
                continue

            valor = match.group(1)

            if valor in numeros_texto:
                valor = numeros_texto[valor]

            nombre = (
                f"{valor} articulaciones"
            )

            conceptos[nombre] = {
                "nombre": nombre,
                "tipo": "caracteristica",
                "dominio": "robotica",
                "categoria": "locomocion",
                "confianza": 0.95,
            }

            break

        # -----------------------------------------------------
        # PALABRAS RELEVANTES DESCONOCIDAS
        # -----------------------------------------------------

        palabras = re.findall(
            r"\b[a-záéíóúñü0-9_-]{4,}\b",
            texto_normalizado,
        )

        for palabra in palabras:

            if palabra in self.PALABRAS_VACIAS:
                continue

            if palabra in conceptos:
                continue

            # Evitamos convertir cada palabra de una oración
            # en un nodo. Solo incorporamos automáticamente
            # algunas palabras técnicas por ahora.

            if dominio in {
                "informatica",
                "robotica",
                "electronica",
            }:

                if (
                    len(palabra) >= 6
                    and palabra not in {
                        "quiero",
                        "tambien",
                        "también",
                        "tienes",
                        "estando",
                        "utilizando",
                        "desarrollando",
                    }
                ):

                    conceptos.setdefault(
                        palabra,
                        {
                            "nombre": palabra,
                            "tipo": "concepto",
                            "dominio": dominio,
                            "categoria": categoria,
                            "confianza": 0.55,
                        },
                    )

        return list(
            conceptos.values()
        )

    # =========================================================
    # PROCESAR MEMORIA
    # =========================================================

    def procesar_memoria(
        self,
        memoria_tipo: str,
        memoria_id: int,
        contenido: str,
        dominio: str = "general",
        categoria: str = "general",
        importancia: float = 0.5,
        confianza: float = 0.7,
    ) -> list[int]:

        conceptos = self.extraer_conceptos(
            contenido,
            dominio=dominio,
            categoria=categoria,
        )

        if not conceptos:
            return []

        dominio_id = (
            self.obtener_o_crear_nodo(
                dominio,
                tipo="dominio",
                dominio=dominio,
                importancia=0.7,
                confianza=1.0,
            )
        )

        nodos_creados = []

        for concepto in conceptos:

            concepto_id = (
                self.obtener_o_crear_nodo(
                    nombre=concepto["nombre"],
                    tipo=concepto["tipo"],
                    dominio=concepto["dominio"],
                    categoria=concepto["categoria"],
                    importancia=importancia,
                    confianza=concepto[
                        "confianza"
                    ],
                )
            )

            nodos_creados.append(
                concepto_id
            )

            # Concepto pertenece al dominio

            if concepto_id != dominio_id:

                self.relacionar(
                    dominio_id,
                    concepto_id,
                    "contiene",
                    confianza=0.85,
                )

            # Vincular memoria original al concepto

            self._vincular_memoria(
                memoria_tipo,
                memoria_id,
                concepto_id,
            )

        # -----------------------------------------------------
        # RELACIONAR CONCEPTOS QUE APARECIERON JUNTOS
        # -----------------------------------------------------

        for i, origen in enumerate(
            nodos_creados
        ):

            for destino in (
                nodos_creados[i + 1:]
            ):

                self.relacionar(
                    origen,
                    destino,
                    "relacionado_con",
                    peso=0.5,
                    confianza=0.65,
                )

                self.relacionar(
                    destino,
                    origen,
                    "relacionado_con",
                    peso=0.5,
                    confianza=0.65,
                )

        # -----------------------------------------------------
        # RELACIONES ESPECIALES
        # -----------------------------------------------------

        self._inferir_relaciones_basicas(
            contenido,
            conceptos,
        )

        return nodos_creados

    # =========================================================
    # MEMORIA ↔ CONCEPTO
    # =========================================================

    def _vincular_memoria(
        self,
        memoria_tipo: str,
        memoria_id: int,
        concepto_id: int,
    ) -> None:

        with self.db.conexion() as conn:

            conn.execute("""
                INSERT OR IGNORE
                INTO memory_concepts (
                    memoria_tipo,
                    memoria_id,
                    concepto_id
                )

                VALUES (?, ?, ?)
            """, (
                memoria_tipo,
                memoria_id,
                concepto_id,
            ))

    # =========================================================
    # RELACIONES SEMÁNTICAS BÁSICAS
    # =========================================================

    def _inferir_relaciones_basicas(
        self,
        texto: str,
        conceptos: list[dict],
    ) -> None:

        texto = self._normalizar(
            texto
        )

        ids = {}

        for concepto in conceptos:

            nodo = self.buscar_nodo(
                concepto["nombre"]
            )

            if nodo:
                ids[
                    concepto["nombre"]
                ] = nodo["id"]

        # -----------------------------------------------------
        # Flask usa Python
        # -----------------------------------------------------

        if (
            "flask" in ids
            and "python" in ids
        ):

            self.relacionar(
                ids["flask"],
                ids["python"],
                "usa",
                confianza=0.95,
            )

        # -----------------------------------------------------
        # Interfaz usa Flask/Python
        # -----------------------------------------------------

        if "interfaz" in ids:

            if "flask" in ids:

                self.relacionar(
                    ids["interfaz"],
                    ids["flask"],
                    "usa",
                    confianza=0.90,
                )

            if "python" in ids:

                self.relacionar(
                    ids["interfaz"],
                    ids["python"],
                    "usa",
                    confianza=0.90,
                )

        # -----------------------------------------------------
        # Robot araña tiene patas
        # -----------------------------------------------------

        robot_key = None

        for candidato in (
            "robot araña",
            "spider-bot",
            "spiderbot",
            "robot",
        ):

            if candidato in ids:
                robot_key = candidato
                break

        pata_key = None

        for candidato in (
            "patas",
            "pata",
        ):

            if candidato in ids:
                pata_key = candidato
                break

        if (
            robot_key
            and pata_key
        ):

            self.relacionar(
                ids[robot_key],
                ids[pata_key],
                "tiene",
                confianza=0.95,
            )

        # -----------------------------------------------------
        # Patas tienen N articulaciones
        # -----------------------------------------------------

        if pata_key:

            for nombre, node_id in ids.items():

                if re.fullmatch(
                    r"\d+\s+articulaciones",
                    nombre,
                ):

                    self.relacionar(
                        ids[pata_key],
                        node_id,
                        "tiene",
                        confianza=0.98,
                    )

        # -----------------------------------------------------
        # Atenas tiene cuerpo robot
        # -----------------------------------------------------

        if (
            "atenas" in texto
            and robot_key
        ):

            atenas = self.buscar_nodo(
                "atenas"
            )

            if atenas:

                self.relacionar(
                    atenas["id"],
                    ids[robot_key],
                    "tendra_cuerpo",
                    confianza=0.90,
                )

    # =========================================================
    # CONSULTAR NODO
    # =========================================================

    def buscar_nodo(
        self,
        nombre: str,
    ) -> dict | None:

        nombre = self._normalizar(
            nombre
        )

        with self.db.conexion() as conn:

            row = conn.execute("""
                SELECT *
                FROM knowledge_nodes

                WHERE LOWER(nombre) = LOWER(?)

                ORDER BY
                    importancia DESC,
                    veces_usado DESC

                LIMIT 1
            """, (
                nombre,
            )).fetchone()

        return (
            dict(row)
            if row
            else None
        )

    # =========================================================
    # VECINOS / RELACIONES
    # =========================================================

    def vecinos(
        self,
        nombre: str,
        limite: int = 20,
    ) -> list[dict]:

        nodo = self.buscar_nodo(
            nombre
        )

        if not nodo:
            return []

        with self.db.conexion() as conn:

            rows = conn.execute("""
                SELECT
                    e.relacion,
                    e.peso,
                    e.confianza,

                    n.id,
                    n.nombre,
                    n.tipo,
                    n.dominio,
                    n.categoria

                FROM knowledge_edges e

                JOIN knowledge_nodes n
                  ON n.id = e.destino_id

                WHERE e.origen_id = ?

                ORDER BY
                    e.peso DESC,
                    e.confianza DESC

                LIMIT ?
            """, (
                nodo["id"],
                limite,
            )).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # =========================================================
    # BUSCAR CONCEPTOS DE UNA CONSULTA
    # =========================================================

    def buscar_relacionado(
        self,
        consulta: str,
        limite: int = 20,
    ) -> list[dict]:

        texto = self._normalizar(
            consulta
        )

        encontrados = []

        with self.db.conexion() as conn:

            nodos = conn.execute("""
                SELECT *
                FROM knowledge_nodes

                ORDER BY
                    importancia DESC,
                    veces_usado DESC
            """).fetchall()

        for nodo in nodos:

            nombre = nodo["nombre"]

            if nombre in texto:

                encontrados.append(
                    dict(nodo)
                )

        resultados = []
        ids_resultados = set()

        for nodo in encontrados:

            if nodo["id"] not in ids_resultados:

                resultados.append(
                    nodo
                )

                ids_resultados.add(
                    nodo["id"]
                )

            for vecino in self.vecinos(
                nodo["nombre"],
                limite=8,
            ):

                if vecino["id"] not in ids_resultados:

                    resultados.append(
                        vecino
                    )

                    ids_resultados.add(
                        vecino["id"]
                    )

                if len(resultados) >= limite:
                    return resultados

        return resultados

    # =========================================================
    # CONTEXTO PARA QWEN
    # =========================================================

    def contexto_para_llm(
        self,
        consulta: str,
        limite: int = 12,
    ) -> str:

        nodos = self.buscar_relacionado(
            consulta,
            limite=limite,
        )

        if not nodos:
            return ""

        lineas = []

        for nodo in nodos:

            relaciones = self.vecinos(
                nodo["nombre"],
                limite=5,
            )

            if relaciones:

                for relacion in relaciones:

                    lineas.append(
                        f"- {nodo['nombre']} "
                        f"{relacion['relacion']} "
                        f"{relacion['nombre']}"
                    )

            else:

                lineas.append(
                    f"- Concepto conocido: "
                    f"{nodo['nombre']}"
                )

        # Quitar duplicados manteniendo orden

        lineas = list(
            dict.fromkeys(lineas)
        )

        return (
            "RELACIONES DEL GRAFO DE "
            "CONOCIMIENTO DE ATENAS:\n"
            + "\n".join(
                lineas[:limite]
            )
        )

    # =========================================================
    # EXPORTAR PARA FUTURO FRONTEND
    # =========================================================

    def exportar(
        self,
        limite_nodos: int = 500,
    ) -> dict:

        with self.db.conexion() as conn:

            nodes = conn.execute("""
                SELECT *
                FROM knowledge_nodes

                ORDER BY
                    importancia DESC,
                    veces_usado DESC

                LIMIT ?
            """, (
                limite_nodos,
            )).fetchall()

            ids = [
                int(n["id"])
                for n in nodes
            ]

            if not ids:

                return {
                    "nodes": [],
                    "edges": [],
                }

            placeholders = ",".join(
                "?"
                for _ in ids
            )

            edges = conn.execute(
                f"""
                SELECT *
                FROM knowledge_edges

                WHERE origen_id IN (
                    {placeholders}
                )
                AND destino_id IN (
                    {placeholders}
                )
                """,
                ids + ids,
            ).fetchall()

        return {
            "nodes": [
                dict(n)
                for n in nodes
            ],
            "edges": [
                dict(e)
                for e in edges
            ],
        }