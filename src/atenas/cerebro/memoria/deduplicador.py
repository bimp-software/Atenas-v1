from __future__ import annotations

from dataclasses import dataclass
import re

from src.atenas.memoria.store_manager import (
    StorageManager,
)


@dataclass
class ResultadoDeduplicacion:
    duplicada: bool
    memoria_id: int | None = None
    similitud: float = 0.0
    score_final: float = 0.0
    memoria_existente: dict | None = None
    coincidencia_palabras: float = 0.0

class DeduplicadorMemoria:
    PALABRAS_VACIAS = {
        "de",
        "la",
        "el",
        "los",
        "las",
        "un",
        "una",
        "unos",
        "unas",
        "y",
        "o",
        "en",
        "con",
        "para",
        "por",
        "del",
        "al",
        "que",
        "se",
        "su",
        "sus",
        "cada",
    }

    def __init__(
        self,
        storage: StorageManager,
        umbral_vectorial: float = 0.68,
        umbral_final: float = 0.72,
    ):
        self.storage = storage

        self.umbral_vectorial = (
            umbral_vectorial
        )

        self.umbral_final = (
            umbral_final
        )

    # =========================================================
    # EXTRAER PALABRAS IMPORTANTES
    # =========================================================

    def _palabras_importantes(
        self,
        texto: str,
    ) -> set[str]:

        palabras = re.findall(
            r"[a-záéíóúñü0-9]+",
            texto.lower(),
        )

        normalizadas = set()

        for palabra in palabras:

            if palabra in self.PALABRAS_VACIAS:
                continue

            if len(palabra) < 3:
                continue

            # Normalización pequeña para singular/plural
            if palabra.endswith("es") and len(palabra) > 5:
                palabra = palabra[:-2]

            elif palabra.endswith("s") and len(palabra) > 4:
                palabra = palabra[:-1]

            normalizadas.add(
                palabra
            )

        return normalizadas

    # =========================================================
    # COINCIDENCIA LÉXICA
    # =========================================================

    def _coincidencia_palabras(
        self,
        texto_a: str,
        texto_b: str,
    ) -> float:

        palabras_a = (
            self._palabras_importantes(
                texto_a
            )
        )

        palabras_b = (
            self._palabras_importantes(
                texto_b
            )
        )

        if not palabras_a or not palabras_b:
            return 0.0

        interseccion = (
            palabras_a
            & palabras_b
        )

        union = (
            palabras_a
            | palabras_b
        )

        if not union:
            return 0.0

        return (
            len(interseccion)
            / len(union)
        )

    # =========================================================
    # BUSCAR MEMORIA EQUIVALENTE
    # =========================================================

    def buscar_equivalente(
        self,
        contenido: str,
    ) -> ResultadoDeduplicacion:

        contenido = (
            contenido
            or ""
        ).strip()

        if not contenido:

            return ResultadoDeduplicacion(
                duplicada=False,
            )

        # =====================================================
        # BÚSQUEDA VECTORIAL
        # =====================================================

        try:

            resultados = (
                self.storage.vectores.buscar(
                    consulta=contenido,
                    limite=8,
                    similitud_minima=0.30,
                )
            )

        except Exception as error:

            print(
                "[ATENAS][DEDUPLICACION] "
                f"Error vectorial: {error}"
            )

            return ResultadoDeduplicacion(
                duplicada=False,
            )

        if not resultados:

            return ResultadoDeduplicacion(
                duplicada=False,
            )

        mejor_resultado = None
        mejor_score = 0.0
        mejor_similitud = 0.0
        mejor_lexico = 0.0

        # =====================================================
        # COMBINAR SEÑALES
        # =====================================================

        for memoria in resultados:

            similitud = float(
                memoria.get(
                    "similitud_semantica",
                    0.0,
                )
                or 0.0
            )

            memoria_contenido = (
                memoria.get("contenido")
                or memoria.get("descripcion")
                or ""
            )

            coincidencia = (
                self._coincidencia_palabras(
                    contenido,
                    memoria_contenido,
                )
            )

            # 75% significado
            # 25% palabras compartidas
            score = (
                similitud * 0.75
                + coincidencia * 0.25
            )

            if score > mejor_score:

                mejor_score = score
                mejor_resultado = memoria
                mejor_similitud = similitud
                mejor_lexico = coincidencia

        if mejor_resultado is None:

            return ResultadoDeduplicacion(
                duplicada=False,
            )

        # =====================================================
        # REGLA DE DUPLICACIÓN
        # =====================================================

        duplicada = (
            mejor_similitud
            >= self.umbral_vectorial
            and mejor_score
            >= self.umbral_final
        )

        memoria_id = (
            mejor_resultado.get(
                "memoria_id"
            )
            or mejor_resultado.get(
                "id"
            )
        )

        return ResultadoDeduplicacion(
            duplicada=duplicada,
            memoria_id=(
                int(memoria_id)
                if (
                    duplicada
                    and memoria_id is not None
                )
                else None
            ),
            similitud=mejor_similitud,
            score_final=mejor_score,
            memoria_existente=(
                mejor_resultado
            ),
            coincidencia_palabras=(
                mejor_lexico
            ),
        )