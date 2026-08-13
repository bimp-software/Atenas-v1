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

    def __init__(
        self,
        storage: StorageManager,
    ):
        # Ya no creamos otro StorageManager.
        self.storage = storage

        self.clasificador = (
            ClasificadorMemoria()
        )

    def detectar(
        self,
        mensaje: str,
        objetivos: GestorObjetivos,
    ) -> list[NecesidadDetectada]:

        mensaje = mensaje.strip()

        if not mensaje:
            return []

        clasificacion = (
            self.clasificador.clasificar(
                mensaje
            )
        )

        necesidades = []

        for objetivo in objetivos.activos():

            if not objetivo.autonomia:
                continue

            necesidad = (
                self._evaluar_objetivo(
                    mensaje=mensaje,
                    objetivo=objetivo,
                    dominio=(
                        clasificacion.dominio
                    ),
                    categoria=(
                        clasificacion.categoria
                    ),
                )
            )

            if necesidad is not None:
                necesidades.append(
                    necesidad
                )

        return necesidades

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

        # =====================================================
        # 1. INDICIO DE CAMBIO / DECISIÓN
        # =====================================================

        if any(
            indicador in texto
            for indicador
            in self.INDICADORES_CAMBIO
        ):
            score += 0.25

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
            score += 0.25

        # =====================================================
        # 3. MEMORIA VECTORIAL
        # =====================================================

        try:

            similares = (
                self.storage.vectores.buscar(
                    consulta=mensaje,
                    limite=3,
                    similitud_minima=0.30,
                )
            )

            if similares:

                similitud = max(
                    float(
                        item.get(
                            "similitud_semantica",
                            0.0,
                        )
                    )
                    for item in similares
                )

                score += (
                    similitud * 0.30
                )

        except Exception as error:

            print(
                "[ATENAS][NECESIDADES][VECTOR] "
                f"{error}"
            )

        # =====================================================
        # 4. GRAFO
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
        # 5. DOCUMENTACIÓN
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
                    "Registrar una actualización "
                    "relevante del proyecto Atenas: "
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

                # Importante:
                # el detector NO decide la herramienta.
                accion_sugerida=None,
            )

        return None