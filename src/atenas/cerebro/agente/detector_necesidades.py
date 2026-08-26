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
    Detector V4: software + sistema + ventanas + objetivos.
    """

    INDICADORES_CAMBIO = (
        "voy a",
        "quiero",
        "decidí",
        "decidi",
        "cambiaré",
        "cambiare",
        "usaré",
        "usare",
        "haré",
        "hare",
        "agregaré",
        "agregare",
        "estoy creando",
        "estoy desarrollando",
        "después",
        "despues",
    )

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
        "dashboard",
        "panel web",
        "sistema web",
        "sistema de escritorio",
    )

    EXCLUSIONES_DESARROLLO = (
        "qué es un sistema",
        "que es un sistema",
        "qué es software",
        "que es software",
        "definición de",
        "definicion de",
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

        dominio = getattr(
            clasificacion,
            "dominio",
            None,
        )

        categoria = getattr(
            clasificacion,
            "categoria",
            None,
        )

        necesidades = []

        desarrollo = (
            self._detectar_desarrollo(
                mensaje,
                dominio,
                categoria,
            )
        )

        if desarrollo:
            necesidades.append(
                desarrollo
            )

        sistema = (
            self._detectar_sistema(
                mensaje,
                dominio,
                categoria,
            )
        )

        if sistema:
            necesidades.append(
                sistema
            )

        for objetivo in (
            objetivos.activos()
        ):

            necesidad = (
                self._evaluar_objetivo(
                    mensaje=mensaje,
                    objetivo=objetivo,
                    dominio=dominio or "",
                    categoria=categoria or "",
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
    # SISTEMA
    # =========================================================

    @staticmethod
    def _detectar_sistema(
        mensaje: str,
        dominio: str | None,
        categoria: str | None,
    ) -> NecesidadDetectada | None:

        t = mensaje.lower()

        patrones = (

            (
                "crear_tarea_escritorio",
                (
                    "prepara este proyecto",
                    "preparar este proyecto",
                    "prepara el proyecto",
                    "preparar el proyecto",
                    "prepara para entregar",
                    "preparar para entregar",
                    "prepara la entrega",
                    "preparar entrega",
                    "organiza los archivos",
                    "organizar los archivos",
                    "organiza una carpeta",
                    "organizar carpeta",
                    "trabaja en el proyecto",
                    "revisa el proyecto",
                ),
            ),

            (
                "capturar_pantalla",
                (
                    "captura la pantalla",
                    "capturar pantalla",
                    "toma una captura",
                    "haz una captura de pantalla",
                    "screenshot de la pantalla",
                ),
            ),
            (
                "capturar_ventana",
                (
                    "captura la ventana",
                    "capturar la ventana",
                    "captura de la ventana",
                ),
            ),
            (
                "listar_capturas",
                (
                    "lista las capturas",
                    "listar capturas",
                    "muestra las capturas",
                    "últimas capturas",
                    "ultimas capturas",
                ),
            ),

            (
                "pulsar_tecla",
                (
                    "presiona enter",
                    "pulsa enter",
                    "presiona escape",
                    "pulsa escape",
                    "presiona tab",
                    "pulsa tab",
                ),
            ),
            (
                "combinacion_teclas",
                (
                    "ctrl+s",
                    "control+s",
                    "ctrl+c",
                    "ctrl+v",
                    "ctrl+x",
                    "ctrl+z",
                    "alt+tab",
                ),
            ),

            (
                "posicion_mouse",
                (
                    "posición del mouse",
                    "posicion del mouse",
                    "dónde está el mouse",
                    "donde esta el mouse",
                    "posición del cursor",
                    "posicion del cursor",
                ),
            ),
            (
                "mover_mouse",
                (
                    "mueve el mouse",
                    "mover el mouse",
                    "mueve el cursor",
                    "mover el cursor",
                ),
            ),
            (
                "scroll_mouse",
                (
                    "haz scroll",
                    "hacer scroll",
                    "scroll hacia",
                    "desplaza hacia arriba",
                    "desplaza hacia abajo",
                ),
            ),
            (
                "listar_ventanas",
                (
                    "lista las ventanas",
                    "listar ventanas",
                    "muestra las ventanas",
                    "ventanas abiertas",
                    "qué ventanas",
                    "que ventanas",
                ),
            ),
            (
                "ventana_activa",
                (
                    "ventana activa",
                    "qué ventana está activa",
                    "que ventana esta activa",
                    "cuál es la ventana activa",
                    "cual es la ventana activa",
                ),
            ),
            (
                "activar_ventana",
                (
                    "activa la ventana",
                    "activar la ventana",
                    "trae al frente la ventana",
                    "pon al frente la ventana",
                ),
            ),
            (
                "maximizar_ventana",
                (
                    "maximiza la ventana",
                    "maximizar la ventana",
                ),
            ),
            (
                "minimizar_ventana",
                (
                    "minimiza la ventana",
                    "minimizar la ventana",
                ),
            ),
            (
                "restaurar_ventana",
                (
                    "restaura la ventana",
                    "restaurar la ventana",
                ),
            ),
            (
                "crear_carpeta",
                (
                    "crea una carpeta",
                    "crear una carpeta",
                    "haz una carpeta",
                ),
            ),
            (
                "abrir_aplicacion",
                (
                    "abre el explorador",
                    "abre explorador",
                    "abre powershell",
                    "abre cmd",
                    "abre el bloc de notas",
                    "abre notepad",
                    "abre visual studio code",
                    "abre vs code",
                    "abre vscode",
                ),
            ),
            (
                "listar_procesos",
                (
                    "lista los procesos",
                    "muestra los procesos",
                    "programas abiertos",
                    "aplicaciones abiertas",
                ),
            ),
            (
                "listar_directorio",
                (
                    "qué hay en el escritorio",
                    "que hay en el escritorio",
                    "lista los archivos",
                    "muestra los archivos",
                ),
            ),
            (
                "leer_texto",
                (
                    "lee el archivo",
                    "leer el archivo",
                    "contenido del archivo",
                ),
            ),
        )

        for accion, frases in (
            patrones
        ):

            if any(
                frase in t
                for frase
                in frases
            ):

                return NecesidadDetectada(
                    descripcion=mensaje,
                    objetivo_id=None,
                    prioridad=0.82,
                    confianza=0.94,
                    tipo="sistema_computador",
                    dominio=dominio,
                    categoria=categoria,
                    accion_sugerida=(
                        "sistema_computador:"
                        + accion
                    ),
                )

        return None

    # =========================================================
    # DESARROLLO
    # =========================================================

    @classmethod
    def _detectar_desarrollo(
        cls,
        mensaje: str,
        dominio: str | None,
        categoria: str | None,
    ) -> NecesidadDetectada | None:

        texto = (
            mensaje.lower()
            .strip()
        )

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

        if (
            not tiene_verbo
            or not objetos
        ):
            return None

        score = (
            0.48
            + min(
                0.30,
                len(
                    objetos
                )
                * 0.15,
            )
        )

        return NecesidadDetectada(
            descripcion=mensaje,
            objetivo_id=None,
            prioridad=max(
                0.78,
                min(
                    1.0,
                    score,
                ),
            ),
            confianza=min(
                0.97,
                0.55
                + score
                * 0.45,
            ),
            tipo="desarrollo_software",
            dominio=dominio,
            categoria=categoria,
            accion_sugerida=(
                "desarrollo_software:"
                "crear_proyecto"
            ),
        )

    # =========================================================
    # OBJETIVOS
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

        if dominio in {
            "robotica",
            "informatica",
            "electronica",
            "vision",
            "audio",
        }:
            score += 0.25

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

                score += (
                    max(
                        float(
                            item.get(
                                "similitud_semantica",
                                0.0,
                            )
                        )
                        for item
                        in similares
                    )
                    * 0.30
                )

        except Exception:
            pass

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
                    len(
                        relaciones
                    )
                    * 0.03,
                    0.20,
                )

        except Exception:
            pass

        if "document" in objetivo_texto:

            if score < 0.40:
                return None

            return NecesidadDetectada(
                descripcion=(
                    "Documentar actualización: "
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
                confianza=min(
                    0.45 + score,
                    0.98,
                ),
                tipo="documentacion",
                dominio=dominio,
                categoria=categoria,
                accion_sugerida="crear_nota",
            )

        return None

    @staticmethod
    def _deduplicar(
        necesidades: list[
            NecesidadDetectada
        ],
    ) -> list[NecesidadDetectada]:

        resultado = []
        claves = set()

        for necesidad in (
            necesidades
        ):

            clave = (
                necesidad.tipo,
                necesidad.objetivo_id,
                necesidad.accion_sugerida,
                necesidad.descripcion.lower().strip(),
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