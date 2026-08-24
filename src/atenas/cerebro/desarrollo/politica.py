from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class NivelRiesgo(str, Enum):
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"
    CRITICO = "critico"


@dataclass(frozen=True)
class ResultadoPolitica:
    permitido: bool
    riesgo: NivelRiesgo
    requiere_confirmacion: bool
    motivo: str


class PoliticaDesarrollo:
    """
    Reglas estructurales para el sistema de autodesarrollo de ATENAS.

    Esta clase NO ejecuta cambios.
    Solo decide si una ruta o tipo de modificación es aceptable.
    """

    EXTENSIONES_LECTURA = {
        ".py",
        ".json",
        ".toml",
        ".yaml",
        ".yml",
        ".md",
        ".txt",
        ".html",
        ".css",
        ".js",
        ".ts",
        ".tsx",
    }

    EXTENSIONES_MODIFICABLES = {
        ".py",
        ".json",
        ".toml",
        ".yaml",
        ".yml",
        ".md",
        ".html",
        ".css",
        ".js",
        ".ts",
        ".tsx",
    }

    DIRECTORIOS_IGNORADOS = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".idea",
        ".vscode",
        "node_modules",
        ".atenas",
    }

    ARCHIVOS_PROTEGIDOS = {
        "src/atenas/cerebro/desarrollo/politica.py",
        "src/atenas/cerebro/desarrollo/sandbox.py",
        "src/atenas/cerebro/desarrollo/verificador.py",
        "src/atenas/cerebro/desarrollo/rollback.py",
    }

    PREFIJOS_ALTO_RIESGO = (
        "src/atenas/herramientas/mouse/",
        "src/atenas/herramientas/sistema/",
        "src/atenas/herramientas/internet/",
        "src/atenas/robot/",
        "src/atenas/cerebro/estado/",
    )

    PREFIJOS_MEDIO_RIESGO = (
        "src/atenas/cerebro/memoria/",
        "src/atenas/memoria/",
        "src/atenas/cerebro/agente/",
        "src/atenas/cerebro/investigacion/",
        "src/atenas/cerebro/identidad/",
    )

    def __init__(
        self,
        raiz_proyecto: str | Path = ".",
    ):
        self.raiz = Path(
            raiz_proyecto
        ).resolve()

    # =========================================================
    # NORMALIZAR
    # =========================================================

    def normalizar_ruta(
        self,
        ruta: str | Path,
    ) -> str:

        ruta_path = Path(ruta)

        if ruta_path.is_absolute():

            try:
                relativa = ruta_path.resolve().relative_to(
                    self.raiz
                )

            except ValueError as error:
                raise PermissionError(
                    "La ruta está fuera del proyecto."
                ) from error

        else:
            absoluta = (
                self.raiz
                / ruta_path
            ).resolve()

            try:
                relativa = absoluta.relative_to(
                    self.raiz
                )

            except ValueError as error:
                raise PermissionError(
                    "La ruta intenta salir del proyecto."
                ) from error

        return relativa.as_posix()

    # =========================================================
    # IGNORAR
    # =========================================================

    def debe_ignorar(
        self,
        ruta: str | Path,
    ) -> bool:

        try:
            relativa = self.normalizar_ruta(
                ruta
            )
        except PermissionError:
            return True

        partes = Path(relativa).parts

        return any(
            parte in self.DIRECTORIOS_IGNORADOS
            for parte in partes
        )

    # =========================================================
    # LECTURA
    # =========================================================

    def puede_leer(
        self,
        ruta: str | Path,
    ) -> bool:

        try:
            relativa = self.normalizar_ruta(
                ruta
            )
        except PermissionError:
            return False

        if self.debe_ignorar(
            relativa
        ):
            return False

        extension = (
            Path(relativa)
            .suffix
            .lower()
        )

        return (
            extension
            in self.EXTENSIONES_LECTURA
        )

    # =========================================================
    # ARCHIVO PROTEGIDO
    # =========================================================

    def es_protegido(
        self,
        ruta: str | Path,
    ) -> bool:

        try:
            relativa = self.normalizar_ruta(
                ruta
            )
        except PermissionError:
            return True

        return (
            relativa
            in self.ARCHIVOS_PROTEGIDOS
        )

    # =========================================================
    # EVALUAR MODIFICACIÓN
    # =========================================================

    def evaluar_modificacion(
        self,
        ruta: str | Path,
    ) -> ResultadoPolitica:

        try:
            relativa = self.normalizar_ruta(
                ruta
            )

        except PermissionError:

            return ResultadoPolitica(
                permitido=False,
                riesgo=NivelRiesgo.CRITICO,
                requiere_confirmacion=True,
                motivo=(
                    "La ruta está fuera "
                    "del proyecto."
                ),
            )

        if self.es_protegido(
            relativa
        ):

            return ResultadoPolitica(
                permitido=False,
                riesgo=NivelRiesgo.CRITICO,
                requiere_confirmacion=True,
                motivo="Archivo protegido.",
            )

        if self.debe_ignorar(
            relativa
        ):

            return ResultadoPolitica(
                permitido=False,
                riesgo=NivelRiesgo.CRITICO,
                requiere_confirmacion=True,
                motivo="Directorio no modificable.",
            )

        extension = (
            Path(relativa)
            .suffix
            .lower()
        )

        if (
            extension
            not in self.EXTENSIONES_MODIFICABLES
        ):

            return ResultadoPolitica(
                permitido=False,
                riesgo=NivelRiesgo.ALTO,
                requiere_confirmacion=True,
                motivo=(
                    "Tipo de archivo "
                    "no modificable."
                ),
            )

        if any(
            relativa.startswith(prefijo)
            for prefijo
            in self.PREFIJOS_ALTO_RIESGO
        ):

            return ResultadoPolitica(
                permitido=True,
                riesgo=NivelRiesgo.ALTO,
                requiere_confirmacion=True,
                motivo=(
                    "El cambio afecta una "
                    "capacidad sensible."
                ),
            )

        if any(
            relativa.startswith(prefijo)
            for prefijo
            in self.PREFIJOS_MEDIO_RIESGO
        ):

            return ResultadoPolitica(
                permitido=True,
                riesgo=NivelRiesgo.MEDIO,
                requiere_confirmacion=True,
                motivo=(
                    "El cambio afecta la "
                    "lógica cognitiva de ATENAS."
                ),
            )

        if relativa.startswith(
            "tests/"
        ):

            return ResultadoPolitica(
                permitido=True,
                riesgo=NivelRiesgo.BAJO,
                requiere_confirmacion=False,
                motivo="Archivo de pruebas.",
            )

        return ResultadoPolitica(
            permitido=True,
            riesgo=NivelRiesgo.BAJO,
            requiere_confirmacion=False,
            motivo="Cambio local de bajo riesgo.",
        )