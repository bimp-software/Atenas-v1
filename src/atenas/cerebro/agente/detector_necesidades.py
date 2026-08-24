from __future__ import annotations

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
    objetivo_id: str

    prioridad: float
    confianza: float

    tipo: str

    dominio: str | None = None
    categoria: str | None = None

    accion_sugerida: str | None = None


class DetectorNecesidades:
    """
    Detector híbrido de iniciativa de ATENAS.

    Detecta información que realmente representa
    una decisión, cambio, intención o actualización.

    NO debe convertir preguntas normales en tareas.
    """

    # =========================================================
    # INDICADORES REALES DE CAMBIO
    # =========================================================

    INDICADORES_CAMBIO = (
        "voy a ",
        "quiero usar ",
        "quiero utilizar ",
        "quiero agregar ",
        "quiero cambiar ",
        "quiero hacer ",
        "decidí ",
        "decidi ",
        "he decidido ",
        "mejor voy a ",
        "cambiaré ",
        "cambiare ",
        "usaré ",
        "usare ",
        "utilizaré ",
        "utilizare ",
        "tendrá ",
        "tendra ",
        "tendrán ",
        "tendran ",
        "haré ",
        "hare ",
        "agregaré ",
        "agregare ",
        "eliminaré ",
        "eliminare ",
        "estoy usando ",
        "estoy utilizando ",
        "estoy creando ",
        "estoy desarrollando ",
        "voy a cambiar ",
        "voy a usar ",
        "voy a utilizar ",
        "voy a agregar ",
        "voy a eliminar ",
        "ahora usaré ",
        "ahora usare ",
        "finalmente usaré ",
        "finalmente usare ",
    )

    # =========================================================
    # PREGUNTAS QUE NO REPRESENTAN UNA ACCIÓN
    # =========================================================

    INICIOS_PREGUNTA = (
        "qué ",
        "que ",
        "cómo ",
        "como ",
        "cuál ",
        "cual ",
        "cuáles ",
        "cuales ",
        "dónde ",
        "donde ",
        "cuándo ",
        "cuando ",
        "quién ",
        "quien ",
        "por qué ",
        "por que ",
        "puedes ",
        "podrías ",
        "podrias ",
        "sabes ",
        "recuerdas ",
        "tienes ",
        "eres ",
        "estás ",
        "estas ",
        "funciona ",
    )

    # =========================================================
    # CONSULTAS SOBRE ATENAS
    # =========================================================

    CONSULTAS_CAPACIDAD = (
        "puedes modificar",
        "puedes cambiar",
        "puedes reparar",
        "puedes programar",
        "puedes corregir",
        "qué puedes hacer",
        "que puedes hacer",
        "qué capacidades",
        "que capacidades",
        "qué herramientas",
        "que herramientas",
        "puedes usar internet",
        "tienes internet",
        "puedes acceder",
        "puedes recordar",
        "tienes memoria",
        "puedes aprender",
        "puedes investigar",
        "puedes modificar tu propio código",
        "puedes modificar tu propio codigo",
        "puedes corregir tu código",
        "puedes corregir tu codigo",
    )

    CONSULTAS_IDENTIDAD = (
        "cómo te llamas",
        "como te llamas",
        "quién eres",
        "quien eres",
        "qué eres",
        "que eres",
        "quién te creó",
        "quien te creo",
        "quién te hizo",
        "quien te hizo",
    )

    # =========================================================
    # CONVERSACIÓN CASUAL
    # =========================================================

    CONVERSACION_CASUAL = (
        "hola",
        "hola atenas",
        "buenas",
        "buenos días",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "qué cuentas",
        "que cuentas",
        "cómo estás",
        "como estas",
        "gracias",
        "muchas gracias",
        "ok",
        "okay",
        "dale",
        "perfecto",
        "bien",
        "sí",
        "si",
        "no",
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
    # NORMALIZAR
    # =========================================================

    @staticmethod
    def _normalizar(
        mensaje: str,
    ) -> str:

        return " ".join(
            (
                mensaje
                or ""
            )
            .strip()
            .lower()
            .split()
        )

    # =========================================================
    # ¿ES PREGUNTA?
    # =========================================================

    def _es_pregunta(
        self,
        mensaje: str,
    ) -> bool:

        texto = self._normalizar(
            mensaje
        )

        if not texto:
            return False

        # Pregunta explícita
        if "?" in mensaje:
            return True

        if "¿" in mensaje:
            return True

        # Pregunta sin signos
        if any(
            texto.startswith(
                inicio
            )
            for inicio
            in self.INICIOS_PREGUNTA
        ):
            return True

        return False

    # =========================================================
    # ¿ES CONSULTA DE CAPACIDAD?
    # =========================================================

    def _es_consulta_capacidad(
        self,
        mensaje: str,
    ) -> bool:

        texto = self._normalizar(
            mensaje
        )

        return any(
            consulta in texto
            for consulta
            in self.CONSULTAS_CAPACIDAD
        )

    # =========================================================
    # ¿ES CONSULTA DE IDENTIDAD?
    # =========================================================

    def _es_consulta_identidad(
        self,
        mensaje: str,
    ) -> bool:

        texto = self._normalizar(
            mensaje
        )

        return any(
            consulta in texto
            for consulta
            in self.CONSULTAS_IDENTIDAD
        )

    # =========================================================
    # ¿ES CONVERSACIÓN CASUAL?
    # =========================================================

    def _es_conversacion_casual(
        self,
        mensaje: str,
    ) -> bool:

        texto = self._normalizar(
            mensaje
        )

        return (
            texto
            in self.CONVERSACION_CASUAL
        )

    # =========================================================
    # ¿TIENE INTENCIÓN EXPLÍCITA?
    # =========================================================

    def _tiene_indicador_cambio(
        self,
        mensaje: str,
    ) -> bool:

        texto = (
            self._normalizar(
                mensaje
            )
            + " "
        )

        return any(
            indicador in texto
            for indicador
            in self.INDICADORES_CAMBIO
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

        # =====================================================
        # 1. DESCARTAR CONVERSACIÓN CASUAL
        # =====================================================

        if self._es_conversacion_casual(
            mensaje
        ):
            return []

        # =====================================================
        # 2. DESCARTAR IDENTIDAD
        # =====================================================

        if self._es_consulta_identidad(
            mensaje
        ):
            return []

        # =====================================================
        # 3. DESCARTAR CAPACIDADES
        # =====================================================

        if self._es_consulta_capacidad(
            mensaje
        ):
            return []

        # =====================================================
        # 4. LAS PREGUNTAS NORMALES NO SON TAREAS
        # =====================================================

        if self._es_pregunta(
            mensaje
        ):

            return []

        # =====================================================
        # 5. CLASIFICAR
        # =====================================================

        clasificacion = (
            self.clasificador
            .clasificar(
                mensaje
            )
        )

        necesidades = []

        # =====================================================
        # 6. EVALUAR OBJETIVOS ACTIVOS
        # =====================================================

        for objetivo in (
            objetivos.activos()
        ):

            necesidad = (
                self._evaluar_objetivo(
                    mensaje=mensaje,
                    objetivo=objetivo,

                    dominio=getattr(
                        clasificacion,
                        "dominio",
                        "general",
                    ),

                    categoria=(
                        getattr(
                            clasificacion,
                            "categoria",
                            None,
                        )
                        or getattr(
                            clasificacion,
                            "subcategoria",
                            None,
                        )
                    ),
                )
            )

            if necesidad:

                necesidades.append(
                    necesidad
                )

        return necesidades

    # =========================================================
    # EVALUAR OBJETIVO
    # =========================================================

    def _evaluar_objetivo(
        self,
        mensaje: str,
        objetivo: Objetivo,
        dominio: str,
        categoria: str | None,
    ) -> NecesidadDetectada | None:

        texto = (
            self._normalizar(
                mensaje
            )
        )

        objetivo_texto = (
            f"{objetivo.nombre} "
            f"{objetivo.descripcion}"
        ).lower()

        score = 0.0

        motivos = []

        # =====================================================
        # 1. INDICADOR EXPLÍCITO
        # =====================================================

        cambio_explicito = (
            self._tiene_indicador_cambio(
                mensaje
            )
        )

        if cambio_explicito:

            score += 0.40

            motivos.append(
                "indicio_explicito_de_cambio"
            )

        # =====================================================
        # 2. DOMINIO DEL PROYECTO
        # =====================================================

        dominios_proyecto = {
            "robotica",
            "informatica",
            "electronica",
            "vision",
            "audio",
        }

        if dominio in dominios_proyecto:

            score += 0.20

            motivos.append(
                f"dominio:{dominio}"
            )

        # =====================================================
        # 3. SIMILITUD VECTORIAL
        # =====================================================

        similitud_maxima = 0.0

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
                        or 0.0
                    )
                    for item in similares
                )

                score += (
                    similitud_maxima
                    * 0.20
                )

                motivos.append(
                    "memoria_semanticamente_relacionada"
                )

        except Exception as error:

            print(
                "[ATENAS][NECESIDADES][VECTOR] "
                f"{error}"
            )

        # =====================================================
        # 4. GRAFO
        # =====================================================

        relaciones = []

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
                    * 0.02,
                    0.10,
                )

                motivos.append(
                    "conceptos_del_grafo"
                )

        except Exception as error:

            print(
                "[ATENAS][NECESIDADES][GRAFO] "
                f"{error}"
            )

        # =====================================================
        # 5. OBJETIVO DE DOCUMENTACIÓN
        # =====================================================

        if "document" in objetivo_texto:

            # Una similitud alta NO basta.
            #
            # Para crear una nota automáticamente necesitamos
            # que el mensaje represente una afirmación/intención
            # real de cambio.

            if not cambio_explicito:

                return None

            if score < 0.45:

                return None

            confianza = min(
                0.40 + score,
                0.98,
            )

            return NecesidadDetectada(
                descripcion=(
                    "Documentar una actualización "
                    "relevante del proyecto: "
                    f"{mensaje}"
                ),

                objetivo_id=(
                    objetivo.id
                ),

                prioridad=max(
                    objetivo.prioridad,
                    min(
                        score + 0.25,
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