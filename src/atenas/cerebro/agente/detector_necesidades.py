from __future__ import annotations

import re
from dataclasses import dataclass

from src.atenas.cerebro.memoria.clasificador import (
    ClasificadorMemoria,
)
from src.atenas.memoria.store_manager import (
    StorageManager,
)

from .objetivos import (
    GestorObjetivos,
    Objetivo,
)


@dataclass
class NecesidadDetectada:
    descripcion: str
    objetivo_id: str | None
    prioridad: float
    confianza: float
    tipo: str

    dominio: str | None = None
    categoria: str | None = None

    accion_sugerida: str | None = None


class DetectorNecesidades:
    """
    Detector híbrido de iniciativa de ATENAS.

    Detecta dos grandes clases de necesidades:

    1. Necesidades relacionadas con objetivos activos.
    2. Necesidades explícitas de desarrollo de software, incluso si
       todavía no existe un objetivo formal asociado.

    Una necesidad de software se transforma posteriormente en un
    pendiente especial con:
        accion_sugerida = "desarrollo_software:crear_proyecto"

    Esto permite persistir la intención antes de que DecisionEngine
    decida ejecutarla.
    """

    INDICADORES_CAMBIO = (
        "voy a",
        "quiero",
        "decidí",
        "decidi",
        "mejor",
        "cambiaré",
        "cambiare",
        "usaré",
        "usare",
        "tendrá",
        "tendra",
        "tendrán",
        "tendran",
        "haré",
        "hare",
        "agregaré",
        "agregare",
        "eliminaré",
        "eliminare",
        "utilizaré",
        "utilizare",
        "estoy usando",
        "estoy utilizando",
        "estoy creando",
        "estoy desarrollando",
        "primero",
        "después",
        "despues",
    )

    # =========================================================
    # DESARROLLO
    # =========================================================

    VERBOS_DESARROLLO = (
        "crear",
        "crea",
        "creame",
        "créame",
        "hacer",
        "haz",
        "desarrollar",
        "desarrolla",
        "programar",
        "programa",
        "construir",
        "construye",
        "implementar",
        "implementa",
        "necesito",
        "quiero",
        "requiero",
    )

    OBJETOS_SOFTWARE = (
        "sistema",
        "software",
        "aplicacion",
        "aplicación",
        "app",
        "pagina web",
        "página web",
        "sitio web",
        "portal",
        "plataforma",
        "api",
        "backend",
        "frontend",
        "base de datos",
        "programa",
        "aplicativo",
        "dashboard",
        "panel web",
        "sistema web",
        "sistema de escritorio",
        "aplicacion de escritorio",
        "aplicación de escritorio",
    )

    INDICADORES_PROYECTO_CLIENTE = (
        "para un cliente",
        "para mi cliente",
        "proyecto de cliente",
        "sistema para",
        "software para",
        "aplicacion para",
        "aplicación para",
        "plataforma para",
        "portal para",
    )

    EXCLUSIONES_DESARROLLO = (
        "qué es un sistema",
        "que es un sistema",
        "qué es software",
        "que es software",
        "explica qué",
        "explica que",
        "definición de",
        "definicion de",
        "qué opinas",
        "que opinas",
    )

    def __init__(
        self,
        storage: StorageManager | None = None,
    ):
        self.storage = (
            storage
            or StorageManager()
        )

        self.clasificador = (
            ClasificadorMemoria()
        )

    # =========================================================
    # DETECTAR
    # =========================================================

    def detectar(
        self,
        mensaje: str,
        objetivos: GestorObjetivos,
    ) -> list[NecesidadDetectada]:

        mensaje = (
            mensaje
            or ""
        ).strip()

        if not mensaje:
            return []

        clasificacion = (
            self.clasificador
            .clasificar(
                mensaje
            )
        )

        necesidades: list[
            NecesidadDetectada
        ] = []

        # =====================================================
        # 1. NECESIDAD DE DESARROLLO INDEPENDIENTE
        # =====================================================

        necesidad_desarrollo = (
            self._detectar_desarrollo(
                mensaje=mensaje,
                dominio=getattr(
                    clasificacion,
                    "dominio",
                    None,
                ),
                categoria=getattr(
                    clasificacion,
                    "categoria",
                    None,
                ),
            )
        )

        if necesidad_desarrollo is not None:

            necesidades.append(
                necesidad_desarrollo
            )

        # =====================================================
        # 2. NECESIDADES RELACIONADAS A OBJETIVOS
        # =====================================================

        for objetivo in objetivos.activos():

            necesidad = (
                self._evaluar_objetivo(
                    mensaje=mensaje,
                    objetivo=objetivo,
                    dominio=getattr(
                        clasificacion,
                        "dominio",
                        "",
                    ),
                    categoria=getattr(
                        clasificacion,
                        "categoria",
                        "",
                    ),
                )
            )

            if necesidad:
                necesidades.append(
                    necesidad
                )

        return self._deduplicar(
            necesidades
        )

    # =========================================================
    # DETECCIÓN DE DESARROLLO
    # =========================================================

    @classmethod
    def _detectar_desarrollo(
        cls,
        mensaje: str,
        dominio: str | None,
        categoria: str | None,
    ) -> NecesidadDetectada | None:

        texto = (
            mensaje
            .strip()
            .lower()
        )

        if not texto:
            return None

        if any(
            exclusion in texto
            for exclusion
            in cls.EXCLUSIONES_DESARROLLO
        ):
            return None

        tiene_verbo = any(
            re.search(
                rf"\b{re.escape(verbo)}\b",
                texto,
            )
            for verbo
            in cls.VERBOS_DESARROLLO
        )

        objetos = [
            objeto
            for objeto
            in cls.OBJETOS_SOFTWARE
            if objeto in texto
        ]

        if not objetos:
            return None

        score = 0.0

        if tiene_verbo:
            score += 0.48

        # Un objeto software explícito es una señal fuerte.
        score += min(
            0.30,
            len(
                objetos
            )
            * 0.15,
        )

        if any(
            patron in texto
            for patron
            in cls.INDICADORES_PROYECTO_CLIENTE
        ):
            score += 0.12

        if dominio in {
            "informatica",
            "programacion",
            "software",
            "web",
        }:
            score += 0.08

        # Debe existir intención de construcción, no solo mención.
        if not tiene_verbo:
            return None

        if score < 0.60:
            return None

        confianza = min(
            0.97,
            0.55 + score * 0.45,
        )

        prioridad = min(
            1.0,
            max(
                0.78,
                score,
            ),
        )

        return NecesidadDetectada(
            descripcion=mensaje,
            objetivo_id=None,
            prioridad=prioridad,
            confianza=confianza,
            tipo="desarrollo_software",
            dominio=dominio,
            categoria=categoria,
            accion_sugerida=(
                "desarrollo_software:crear_proyecto"
            ),
        )

    # =========================================================
    # EVALUAR OBJETIVO
    # =========================================================

    def _evaluar_objetivo(
        self,
        mensaje: str,
        objetivo: Objetivo,
        dominio: str,
        categoria: str,
    ) -> NecesidadDetectada | None:

        texto = mensaje.lower()

        objetivo_texto = (
            f"{objetivo.nombre} "
            f"{objetivo.descripcion}"
        ).lower()

        score = 0.0

        if any(
            indicador in texto
            for indicador
            in self.INDICADORES_CAMBIO
        ):
            score += 0.25

        dominios_proyecto = {
            "robotica",
            "informatica",
            "electronica",
            "vision",
            "audio",
        }

        if dominio in dominios_proyecto:
            score += 0.25

        # =====================================================
        # MEMORIA VECTORIAL
        # =====================================================

        try:

            similares = (
                self.storage.vectores
                .buscar(
                    consulta=mensaje,
                    limite=3,
                    similitud_minima=0.30,
                )
            )

            if similares:

                similitud_maxima = max(
                    float(
                        item.get(
                            "similitud_semantica",
                            0.0,
                        )
                    )
                    for item
                    in similares
                )

                score += (
                    similitud_maxima
                    * 0.30
                )

        except Exception as error:

            print(
                "[ATENAS][NECESIDADES][VECTOR] "
                f"{error}"
            )

        # =====================================================
        # GRAFO
        # =====================================================

        try:

            relaciones = (
                self.storage.grafo
                .buscar_relacionado(
                    mensaje,
                    limite=10,
                )
            )

            if relaciones:

                score += min(
                    len(relaciones)
                    * 0.03,
                    0.20,
                )

        except Exception as error:

            print(
                "[ATENAS][NECESIDADES][GRAFO] "
                f"{error}"
            )

        # =====================================================
        # DOCUMENTACIÓN
        # =====================================================

        if "document" in objetivo_texto:

            if score < 0.40:
                return None

            confianza = min(
                0.45 + score,
                0.98,
            )

            return NecesidadDetectada(
                descripcion=(
                    "Documentar una actualización "
                    "relevante del proyecto: "
                    f"{mensaje}"
                ),
                objetivo_id=objetivo.id,
                prioridad=max(
                    objetivo.prioridad,
                    min(
                        score + 0.30,
                        1.0,
                    ),
                ),
                confianza=confianza,
                tipo="documentacion",
                dominio=dominio,
                categoria=categoria,
                accion_sugerida=(
                    "crear_nota"
                ),
            )

        return None

    # =========================================================
    # DEDUPLICAR
    # =========================================================

    @staticmethod
    def _deduplicar(
        necesidades: list[
            NecesidadDetectada
        ],
    ) -> list[NecesidadDetectada]:

        resultado = []
        claves = set()

        for necesidad in necesidades:

            clave = (
                necesidad.tipo,
                necesidad.objetivo_id,
                (
                    necesidad.accion_sugerida
                    or ""
                ),
                necesidad.descripcion
                .strip()
                .lower(),
            )

            if clave in claves:
                continue

            claves.add(
                clave
            )

            resultado.append(
                necesidad
            )

        resultado.sort(
            key=lambda item: (
                item.prioridad,
                item.confianza,
            ),
            reverse=True,
        )

        return resultado