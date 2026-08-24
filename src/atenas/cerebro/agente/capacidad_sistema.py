from __future__ import annotations

import re

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ejecutor_sistema import (
    AccionSistema,
    EjecutorSistema,
    TipoAccionSistema,
)

from .gestor_presupuesto_autonomia import (
    GestorPresupuestoAutonomia,
)


@dataclass
class ResultadoCapacidadSistema:
    ok: bool
    accion: str

    mensaje: str = ""

    requiere_confirmacion: bool = False

    datos: dict[str, Any] = field(
        default_factory=dict
    )

    error: str | None = None


class CapacidadSistema:
    """
    Adaptador de lenguaje natural a acciones estructuradas del sistema.

    V2 incorpora administración de ventanas.
    """

    def __init__(
        self,
        ejecutor: EjecutorSistema | None = None,
        autonomia: GestorPresupuestoAutonomia | None = None,
    ):

        self.ejecutor = (
            ejecutor
            or EjecutorSistema()
        )

        self.autonomia = (
            autonomia
            or GestorPresupuestoAutonomia()
        )

    # =========================================================
    # RUTAS
    # =========================================================

    @staticmethod
    def _home(
    ) -> Path:

        return Path.home()

    @classmethod
    def _resolver_ubicacion_natural(
        cls,
        texto: str,
    ) -> Path | None:

        t = (
            texto
            or ""
        ).lower()

        home = cls._home()

        if (
            "escritorio" in t
            or "desktop" in t
        ):
            return (
                home
                / "Desktop"
            ).resolve()

        if (
            "documentos" in t
            or "documents" in t
        ):
            return (
                home
                / "Documents"
            ).resolve()

        return None

    @staticmethod
    def _extraer_nombre_carpeta(
        texto: str,
    ) -> str | None:

        patrones = [
            r"carpeta\s+(?:llamada|llamado|con nombre)\s+[\"']?([^\"']+?)[\"']?(?:\s+en\s+|$)",
            r"carpeta\s+[\"']([^\"']+)[\"']",
            r"carpeta\s+(.+?)(?:\s+en\s+el\s+escritorio|\s+en\s+escritorio|\s+en\s+documentos|$)",
        ]

        for patron in patrones:

            m = re.search(
                patron,
                texto,
                flags=re.IGNORECASE,
            )

            if not m:
                continue

            nombre = (
                m.group(1)
                .strip()
                .strip(" .")
            )

            nombre = re.sub(
                r"\s+(?:por favor|porfavor)$",
                "",
                nombre,
                flags=re.IGNORECASE,
            )

            if nombre:
                return nombre[:100]

        return None

    @staticmethod
    def _extraer_ruta_explicita(
        texto: str,
    ) -> str | None:

        patrones = [
            r'["\']([A-Za-z]:\\[^"\']+)["\']',
            r"\b([A-Za-z]:\\[^\r\n]+)$",
        ]

        for patron in patrones:

            m = re.search(
                patron,
                texto,
            )

            if m:

                return (
                    m.group(1)
                    .strip()
                )

        return None

    # =========================================================
    # VENTANA: EXTRAER TÍTULO
    # =========================================================

    @staticmethod
    def _extraer_titulo_ventana(
        texto: str,
    ) -> str | None:

        patrones = [
            r"ventana\s+(?:de\s+)?[\"']([^\"']+)[\"']",
            r"(?:activa|activar|maximiza|maximizar|minimiza|minimizar|restaura|restaurar)\s+(?:la\s+)?ventana\s+(?:de\s+)?(.+)$",
            r"(?:trae|poner|pon)\s+(?:al\s+frente\s+)?(?:la\s+)?ventana\s+(?:de\s+)?(.+)$",
        ]

        for patron in patrones:

            m = re.search(
                patron,
                texto,
                flags=re.IGNORECASE,
            )

            if not m:
                continue

            titulo = (
                m.group(1)
                .strip()
                .strip(" .")
            )

            titulo = re.sub(
                r"\s+(?:por favor|porfavor)$",
                "",
                titulo,
                flags=re.IGNORECASE,
            )

            if titulo:
                return titulo[:200]

        return None

    # =========================================================
    # PLANIFICAR
    # =========================================================

    def planificar_desde_texto(
        self,
        texto: str,
    ) -> AccionSistema | None:

        original = (
            texto
            or ""
        ).strip()

        t = original.lower()

        if not t:
            return None

        # -----------------------------------------------------
        # VENTANAS
        # -----------------------------------------------------

        if any(
            frase in t
            for frase in (
                "lista las ventanas",
                "listar ventanas",
                "muestra las ventanas",
                "qué ventanas",
                "que ventanas",
                "ventanas abiertas",
            )
        ):

            return AccionSistema(
                tipo=(
                    TipoAccionSistema
                    .LISTAR_VENTANAS
                )
            )

        if any(
            frase in t
            for frase in (
                "ventana activa",
                "qué ventana está activa",
                "que ventana esta activa",
                "cuál es la ventana activa",
                "cual es la ventana activa",
            )
        ):

            return AccionSistema(
                tipo=(
                    TipoAccionSistema
                    .VENTANA_ACTIVA
                )
            )

        if any(
            verbo in t
            for verbo in (
                "maximiza",
                "maximizar",
            )
        ) and "ventana" in t:

            titulo = (
                self._extraer_titulo_ventana(
                    original
                )
            )

            if titulo:

                return AccionSistema(
                    tipo=(
                        TipoAccionSistema
                        .MAXIMIZAR_VENTANA
                    ),
                    argumentos={
                        "titulo":
                            titulo
                    },
                )

        if any(
            verbo in t
            for verbo in (
                "minimiza",
                "minimizar",
            )
        ) and "ventana" in t:

            titulo = (
                self._extraer_titulo_ventana(
                    original
                )
            )

            if titulo:

                return AccionSistema(
                    tipo=(
                        TipoAccionSistema
                        .MINIMIZAR_VENTANA
                    ),
                    argumentos={
                        "titulo":
                            titulo
                    },
                )

        if any(
            verbo in t
            for verbo in (
                "restaura",
                "restaurar",
            )
        ) and "ventana" in t:

            titulo = (
                self._extraer_titulo_ventana(
                    original
                )
            )

            if titulo:

                return AccionSistema(
                    tipo=(
                        TipoAccionSistema
                        .RESTAURAR_VENTANA
                    ),
                    argumentos={
                        "titulo":
                            titulo
                    },
                )

        if (
            "ventana" in t
            and any(
                frase in t
                for frase in (
                    "activa",
                    "activar",
                    "trae al frente",
                    "pon al frente",
                    "poner al frente",
                )
            )
        ):

            titulo = (
                self._extraer_titulo_ventana(
                    original
                )
            )

            if titulo:

                return AccionSistema(
                    tipo=(
                        TipoAccionSistema
                        .ACTIVAR_VENTANA
                    ),
                    argumentos={
                        "titulo":
                            titulo
                    },
                )

        # -----------------------------------------------------
        # PROCESOS
        # -----------------------------------------------------

        if (
            (
                "procesos" in t
                or "programas abiertos" in t
                or "aplicaciones abiertas" in t
            )
            and any(
                verbo in t
                for verbo in (
                    "lista",
                    "listar",
                    "muestra",
                    "mostrar",
                    "ver",
                    "dime",
                )
            )
        ):

            return AccionSistema(
                tipo=(
                    TipoAccionSistema
                    .LISTAR_PROCESOS
                )
            )

        # -----------------------------------------------------
        # CARPETA
        # -----------------------------------------------------

        if (
            "carpeta" in t
            and any(
                verbo in t
                for verbo in (
                    "crea",
                    "crear",
                    "haz",
                    "hacer",
                )
            )
        ):

            base = (
                self._resolver_ubicacion_natural(
                    original
                )
            )

            nombre = (
                self._extraer_nombre_carpeta(
                    original
                )
            )

            ruta_explicita = (
                self._extraer_ruta_explicita(
                    original
                )
            )

            if ruta_explicita:

                destino = Path(
                    ruta_explicita
                ).expanduser()

            elif (
                base is not None
                and nombre
            ):

                destino = (
                    base
                    / nombre
                )

            else:

                return None

            return AccionSistema(
                tipo=(
                    TipoAccionSistema
                    .CREAR_CARPETA
                ),
                argumentos={
                    "ruta":
                        str(
                            destino
                        )
                },
            )

        # -----------------------------------------------------
        # ABRIR APP
        # -----------------------------------------------------

        if any(
            verbo in t
            for verbo in (
                "abre",
                "abrir",
                "inicia",
                "iniciar",
                "ejecuta",
            )
        ):

            alias_map = {
                "visual studio code":
                    "vscode",

                "vs code":
                    "vscode",

                "vscode":
                    "vscode",

                "explorador":
                    "explorador",

                "explorer":
                    "explorador",

                "bloc de notas":
                    "bloc_notas",

                "notepad":
                    "notepad",

                "powershell":
                    "powershell",

                "cmd":
                    "cmd",
            }

            for texto_alias, alias in (
                alias_map.items()
            ):

                if texto_alias in t:

                    return AccionSistema(
                        tipo=(
                            TipoAccionSistema
                            .ABRIR_APLICACION
                        ),
                        argumentos={
                            "alias":
                                alias
                        },
                    )

        # -----------------------------------------------------
        # ABRIR RUTA
        # -----------------------------------------------------

        if any(
            verbo in t
            for verbo in (
                "abre",
                "abrir",
                "muéstrame",
                "muestrame",
            )
        ):

            ruta = (
                self._extraer_ruta_explicita(
                    original
                )
            )

            if ruta:

                return AccionSistema(
                    tipo=(
                        TipoAccionSistema
                        .ABRIR_RUTA
                    ),
                    argumentos={
                        "ruta":
                            ruta
                    },
                )

        # -----------------------------------------------------
        # LISTAR DIRECTORIO
        # -----------------------------------------------------

        if any(
            frase in t
            for frase in (
                "qué hay en",
                "que hay en",
                "lista los archivos",
                "listar archivos",
                "muestra los archivos",
            )
        ):

            ruta = (
                self._extraer_ruta_explicita(
                    original
                )
            )

            if not ruta:

                base = (
                    self._resolver_ubicacion_natural(
                        original
                    )
                )

                ruta = (
                    str(
                        base
                    )
                    if base
                    else None
                )

            if ruta:

                return AccionSistema(
                    tipo=(
                        TipoAccionSistema
                        .LISTAR_DIRECTORIO
                    ),
                    argumentos={
                        "ruta":
                            ruta
                    },
                )

        # -----------------------------------------------------
        # LEER
        # -----------------------------------------------------

        if any(
            frase in t
            for frase in (
                "lee el archivo",
                "leer el archivo",
                "abre y lee",
                "contenido del archivo",
            )
        ):

            ruta = (
                self._extraer_ruta_explicita(
                    original
                )
            )

            if ruta:

                return AccionSistema(
                    tipo=(
                        TipoAccionSistema
                        .LEER_TEXTO
                    ),
                    argumentos={
                        "ruta":
                            ruta
                    },
                )

        return None

    # =========================================================
    # POLÍTICA
    # =========================================================

    @staticmethod
    def _nombre_politica(
        accion: AccionSistema,
    ) -> str:

        return accion.tipo.value

    # =========================================================
    # EJECUTAR
    # =========================================================

    def ejecutar(
        self,
        accion: AccionSistema,
        es_autonoma: bool,
        confirmada: bool = False,
    ) -> ResultadoCapacidadSistema:

        nombre = (
            self._nombre_politica(
                accion
            )
        )

        evaluacion = (
            self.autonomia.evaluar(
                accion=nombre,
                es_autonoma=es_autonoma,
                confirmada=confirmada,
            )
        )

        if not evaluacion.permitida:

            return ResultadoCapacidadSistema(
                ok=False,
                accion=nombre,
                mensaje=evaluacion.motivo,
                requiere_confirmacion=(
                    evaluacion
                    .requiere_confirmacion
                ),
                error=(
                    "accion_bloqueada"
                    if evaluacion.bloqueada
                    else (
                        "requiere_confirmacion"
                        if evaluacion
                        .requiere_confirmacion
                        else "no_permitida"
                    )
                ),
                datos={
                    "nivel":
                        evaluacion.nivel.value,

                    "costo":
                        evaluacion.costo,

                    "presupuesto_restante":
                        evaluacion
                        .presupuesto_restante,
                },
            )

        resultado = (
            self.ejecutor.ejecutar(
                accion
            )
        )

        if (
            resultado.ok
            and es_autonoma
        ):

            self.autonomia.consumir(
                evaluacion,
                es_autonoma=True,
            )

        return ResultadoCapacidadSistema(
            ok=resultado.ok,
            accion=nombre,
            mensaje=resultado.mensaje,
            datos=resultado.datos,
            error=resultado.error,
        )

    def ejecutar_desde_texto(
        self,
        texto: str,
        es_autonoma: bool = False,
        confirmada: bool = False,
    ) -> ResultadoCapacidadSistema:

        accion = (
            self.planificar_desde_texto(
                texto
            )
        )

        if accion is None:

            return ResultadoCapacidadSistema(
                ok=False,
                accion="desconocida",
                error="no_se_pudo_planificar",
                mensaje=(
                    "No se reconoció una acción "
                    "estructurada segura."
                ),
            )

        return self.ejecutar(
            accion=accion,
            es_autonoma=es_autonoma,
            confirmada=confirmada,
        )