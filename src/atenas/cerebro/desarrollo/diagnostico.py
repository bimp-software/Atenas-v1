from __future__ import annotations

import re

from dataclasses import dataclass, field
from pathlib import Path

from .inspector_codigo import InspectorCodigo
from .mapa_proyecto import MapaProyecto


@dataclass
class FrameTraceback:
    archivo: str
    linea: int | None
    funcion: str | None
    codigo: str | None = None


@dataclass
class DiagnosticoError:
    tipo_error: str
    mensaje: str

    archivo_principal: str | None = None
    linea_principal: int | None = None
    funcion_principal: str | None = None

    frames: list[FrameTraceback] = field(
        default_factory=list
    )

    archivos_relacionados: list[str] = field(
        default_factory=list
    )

    simbolos_relacionados: list[str] = field(
        default_factory=list
    )

    categoria: str = "desconocido"

    confianza: float = 0.5

    resumen: str = ""


class DiagnosticoCodigo:
    """
    Analiza errores Python y los relaciona con
    la estructura real del proyecto ATENAS.
    """

    PATRON_FRAME = re.compile(
        r'File "([^"]+)", line (\d+), in ([^\n]+)'
    )

    PATRON_ERROR_FINAL = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):\s*(.*)$"
    )

    PATRON_MODULO_NO_EXISTE = re.compile(
        r"No module named ['\"]([^'\"]+)['\"]"
    )

    PATRON_ATRIBUTO = re.compile(
        r"has no attribute ['\"]([^'\"]+)['\"]"
    )

    PATRON_IMPORT = re.compile(
        r"cannot import name ['\"]([^'\"]+)['\"]"
    )

    def __init__(
        self,
        inspector: InspectorCodigo,
        mapa: MapaProyecto | None = None,
    ):
        self.inspector = inspector

        self.mapa = (
            mapa
            or MapaProyecto(
                inspector=inspector
            )
        )

        self.raiz = (
            self.inspector.raiz
        )

    # =========================================================
    # NORMALIZAR ARCHIVO
    # =========================================================

    def _normalizar_archivo(
        self,
        ruta: str,
    ) -> str:

        try:

            ruta_path = Path(
                ruta
            ).resolve()

            return (
                ruta_path
                .relative_to(
                    self.raiz
                )
                .as_posix()
            )

        except Exception:

            return ruta.replace(
                "\\",
                "/",
            )

    # =========================================================
    # EXTRAER FRAMES
    # =========================================================

    def _extraer_frames(
        self,
        traceback_texto: str,
    ) -> list[FrameTraceback]:

        frames = []

        lineas = traceback_texto.splitlines()

        for indice, linea in enumerate(
            lineas
        ):

            match = (
                self.PATRON_FRAME.search(
                    linea
                )
            )

            if not match:
                continue

            archivo = (
                self._normalizar_archivo(
                    match.group(1)
                )
            )

            numero_linea = int(
                match.group(2)
            )

            funcion = (
                match.group(3)
                .strip()
            )

            codigo = None

            if indice + 1 < len(
                lineas
            ):

                posible_codigo = (
                    lineas[indice + 1]
                    .strip()
                )

                if (
                    posible_codigo
                    and not posible_codigo.startswith(
                        "File "
                    )
                    and not posible_codigo.startswith(
                        "Traceback"
                    )
                ):
                    codigo = (
                        posible_codigo
                    )

            frames.append(
                FrameTraceback(
                    archivo=archivo,
                    linea=numero_linea,
                    funcion=funcion,
                    codigo=codigo,
                )
            )

        return frames

    # =========================================================
    # EXTRAER ERROR FINAL
    # =========================================================

    def _extraer_error_final(
        self,
        traceback_texto: str,
    ) -> tuple[str, str]:

        lineas = [
            linea.strip()
            for linea
            in traceback_texto.splitlines()
            if linea.strip()
        ]

        for linea in reversed(
            lineas
        ):

            match = (
                self.PATRON_ERROR_FINAL.match(
                    linea
                )
            )

            if match:

                return (
                    match.group(1),
                    match.group(2),
                )

        return (
            "ErrorDesconocido",
            (
                lineas[-1]
                if lineas
                else "Sin información."
            ),
        )

    # =========================================================
    # CATEGORIZAR
    # =========================================================

    def _categorizar(
        self,
        tipo_error: str,
        mensaje: str,
    ) -> str:

        if tipo_error in {
            "ModuleNotFoundError",
            "ImportError",
        }:

            if (
                "partially initialized module"
                in mensaje.lower()
                or "circular import"
                in mensaje.lower()
            ):
                return "import_circular"

            return "import"

        if tipo_error == "AttributeError":
            return "atributo"

        if tipo_error == "TypeError":
            return "tipo"

        if tipo_error == "NameError":
            return "nombre"

        if tipo_error == "SyntaxError":
            return "sintaxis"

        if tipo_error in {
            "FileNotFoundError",
            "PermissionError",
        }:
            return "filesystem"

        if tipo_error in {
            "sqlite3.OperationalError",
            "OperationalError",
            "IntegrityError",
        }:
            return "base_datos"

        if tipo_error in {
            "AssertionError",
        }:
            return "test"

        return "runtime"

    # =========================================================
    # EXTRAER SÍMBOLOS
    # =========================================================

    def _extraer_simbolos(
        self,
        tipo_error: str,
        mensaje: str,
    ) -> list[str]:

        simbolos = []

        if tipo_error == "ModuleNotFoundError":

            match = (
                self.PATRON_MODULO_NO_EXISTE.search(
                    mensaje
                )
            )

            if match:
                simbolos.append(
                    match.group(1)
                )

        if tipo_error == "AttributeError":

            match = (
                self.PATRON_ATRIBUTO.search(
                    mensaje
                )
            )

            if match:
                simbolos.append(
                    match.group(1)
                )

        if tipo_error == "ImportError":

            match = (
                self.PATRON_IMPORT.search(
                    mensaje
                )
            )

            if match:
                simbolos.append(
                    match.group(1)
                )

        return list(
            dict.fromkeys(
                simbolos
            )
        )

    # =========================================================
    # ARCHIVOS RELACIONADOS
    # =========================================================

    def _buscar_archivos_relacionados(
        self,
        frames: list[FrameTraceback],
        simbolos: list[str],
    ) -> list[str]:

        relacionados = []

        # ---------------------------------------------
        # Archivos presentes en el traceback
        # ---------------------------------------------

        for frame in frames:

            if frame.archivo.startswith(
                "src/"
            ) or frame.archivo in {
                "main.py",
                "app.py",
            }:

                relacionados.append(
                    frame.archivo
                )

        # ---------------------------------------------
        # Archivos que definen símbolos mencionados
        # ---------------------------------------------

        for simbolo in simbolos:

            resultados = (
                self.inspector
                .buscar_simbolo(
                    simbolo
                )
            )

            for resultado in resultados:

                relacionados.append(
                    resultado[
                        "archivo"
                    ]
                )

        # ---------------------------------------------
        # Imports relacionados
        # ---------------------------------------------

        for simbolo in simbolos:

            if "." not in simbolo:
                continue

            resultados = (
                self.inspector
                .buscar_import(
                    simbolo
                )
            )

            for resultado in resultados:

                relacionados.append(
                    resultado[
                        "archivo"
                    ]
                )

        return list(
            dict.fromkeys(
                relacionados
            )
        )

    # =========================================================
    # RESUMEN
    # =========================================================

    def _crear_resumen(
        self,
        tipo_error: str,
        mensaje: str,
        categoria: str,
        archivo: str | None,
        linea: int | None,
    ) -> str:

        ubicacion = ""

        if archivo:

            ubicacion = (
                f" en {archivo}"
            )

            if linea is not None:

                ubicacion += (
                    f":{linea}"
                )

        return (
            f"Se detectó {tipo_error}{ubicacion}. "
            f"Categoría: {categoria}. "
            f"Mensaje: {mensaje}"
        )

    # =========================================================
    # ANALIZAR
    # =========================================================

    def analizar(
        self,
        traceback_texto: str,
    ) -> DiagnosticoError:

        traceback_texto = (
            traceback_texto
            or ""
        ).strip()

        tipo_error, mensaje = (
            self._extraer_error_final(
                traceback_texto
            )
        )

        frames = (
            self._extraer_frames(
                traceback_texto
            )
        )

        categoria = (
            self._categorizar(
                tipo_error,
                mensaje,
            )
        )

        simbolos = (
            self._extraer_simbolos(
                tipo_error,
                mensaje,
            )
        )

        archivo_principal = None
        linea_principal = None
        funcion_principal = None

        # Preferimos el último frame perteneciente
        # al proyecto ATENAS.
        for frame in reversed(
            frames
        ):

            if (
                frame.archivo.startswith(
                    "src/"
                )
                or frame.archivo
                in {
                    "main.py",
                    "app.py",
                }
                or frame.archivo.startswith(
                    "tests/"
                )
            ):

                archivo_principal = (
                    frame.archivo
                )

                linea_principal = (
                    frame.linea
                )

                funcion_principal = (
                    frame.funcion
                )

                break

        if (
            archivo_principal is None
            and frames
        ):

            ultimo = frames[-1]

            archivo_principal = (
                ultimo.archivo
            )

            linea_principal = (
                ultimo.linea
            )

            funcion_principal = (
                ultimo.funcion
            )

        archivos_relacionados = (
            self._buscar_archivos_relacionados(
                frames=frames,
                simbolos=simbolos,
            )
        )

        confianza = 0.60

        if tipo_error != "ErrorDesconocido":
            confianza += 0.15

        if archivo_principal:
            confianza += 0.10

        if categoria != "runtime":
            confianza += 0.10

        confianza = min(
            confianza,
            0.98,
        )

        resumen = (
            self._crear_resumen(
                tipo_error=tipo_error,
                mensaje=mensaje,
                categoria=categoria,
                archivo=archivo_principal,
                linea=linea_principal,
            )
        )

        return DiagnosticoError(
            tipo_error=tipo_error,
            mensaje=mensaje,

            archivo_principal=(
                archivo_principal
            ),

            linea_principal=(
                linea_principal
            ),

            funcion_principal=(
                funcion_principal
            ),

            frames=frames,

            archivos_relacionados=(
                archivos_relacionados
            ),

            simbolos_relacionados=(
                simbolos
            ),

            categoria=categoria,
            confianza=confianza,
            resumen=resumen,
        )

    # =========================================================
    # CONTEXTO PARA LLM
    # =========================================================

    def contexto_para_llm(
        self,
        diagnostico: DiagnosticoError,
    ) -> str:

        archivos = (
            "\n".join(
                f"- {archivo}"
                for archivo
                in diagnostico.archivos_relacionados
            )
            if diagnostico.archivos_relacionados
            else "- ninguno detectado"
        )

        simbolos = (
            "\n".join(
                f"- {simbolo}"
                for simbolo
                in diagnostico.simbolos_relacionados
            )
            if diagnostico.simbolos_relacionados
            else "- ninguno detectado"
        )

        return f"""
DIAGNÓSTICO AUTOMÁTICO DE ATENAS:

Tipo de error:
{diagnostico.tipo_error}

Categoría:
{diagnostico.categoria}

Mensaje:
{diagnostico.mensaje}

Archivo principal:
{diagnostico.archivo_principal or "desconocido"}

Línea:
{diagnostico.linea_principal or "desconocida"}

Función:
{diagnostico.funcion_principal or "desconocida"}

Confianza del diagnóstico:
{diagnostico.confianza:.2f}

Archivos relacionados:
{archivos}

Símbolos relacionados:
{simbolos}

Resumen:
{diagnostico.resumen}
""".strip()