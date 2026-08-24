from __future__ import annotations

import ast

from dataclasses import dataclass
from pathlib import Path

from .politica import PoliticaDesarrollo


@dataclass
class ArchivoCodigo:
    ruta: str
    extension: str
    tamanio: int
    lineas: int


@dataclass
class CoincidenciaCodigo:
    archivo: str
    linea: int
    texto: str


class InspectorCodigo:
    """
    Permite a ATENAS inspeccionar su propio proyecto.

    Solo tiene capacidad de LECTURA.
    No modifica archivos.
    """

    MAX_TAMANIO_ARCHIVO = (
        1_000_000
    )

    def __init__(
        self,
        raiz_proyecto: str | Path = ".",
        politica: PoliticaDesarrollo | None = None,
    ):
        self.raiz = Path(
            raiz_proyecto
        ).resolve()

        self.politica = (
            politica
            or PoliticaDesarrollo(
                self.raiz
            )
        )

    # =========================================================
    # RESOLVER RUTA
    # =========================================================

    def _resolver(
        self,
        ruta: str | Path,
    ) -> Path:

        relativa = (
            self.politica
            .normalizar_ruta(
                ruta
            )
        )

        absoluta = (
            self.raiz
            / relativa
        ).resolve()

        return absoluta

    # =========================================================
    # LISTAR ARCHIVOS
    # =========================================================

    def listar_archivos(
        self,
        extension: str | None = None,
    ) -> list[ArchivoCodigo]:

        resultados = []

        for archivo in self.raiz.rglob(
            "*"
        ):

            if not archivo.is_file():
                continue

            try:

                relativa = (
                    archivo
                    .relative_to(
                        self.raiz
                    )
                    .as_posix()
                )

            except ValueError:
                continue

            if (
                self.politica
                .debe_ignorar(
                    relativa
                )
            ):
                continue

            if extension:

                extension_normalizada = (
                    extension
                    if extension.startswith(".")
                    else f".{extension}"
                )

                if (
                    archivo.suffix.lower()
                    != extension_normalizada.lower()
                ):
                    continue

            if not self.politica.puede_leer(
                relativa
            ):
                continue

            try:
                tamanio = (
                    archivo.stat()
                    .st_size
                )
            except OSError:
                continue

            if (
                tamanio
                > self.MAX_TAMANIO_ARCHIVO
            ):
                continue

            try:

                contenido = (
                    archivo.read_text(
                        encoding="utf-8"
                    )
                )

            except (
                UnicodeDecodeError,
                OSError,
            ):
                continue

            resultados.append(
                ArchivoCodigo(
                    ruta=relativa,
                    extension=(
                        archivo.suffix.lower()
                    ),
                    tamanio=tamanio,
                    lineas=(
                        len(
                            contenido.splitlines()
                        )
                    ),
                )
            )

        return sorted(
            resultados,
            key=lambda item: item.ruta,
        )

    # =========================================================
    # LISTAR PYTHON
    # =========================================================

    def listar_python(
        self,
    ) -> list[ArchivoCodigo]:

        return self.listar_archivos(
            ".py"
        )

    # =========================================================
    # LEER ARCHIVO
    # =========================================================

    def leer_archivo(
        self,
        ruta: str | Path,
    ) -> dict:

        if not self.politica.puede_leer(
            ruta
        ):

            return {
                "ok": False,
                "error": (
                    "lectura_no_permitida"
                ),
            }

        try:

            archivo = self._resolver(
                ruta
            )

        except PermissionError:

            return {
                "ok": False,
                "error": (
                    "ruta_fuera_proyecto"
                ),
            }

        if not archivo.exists():

            return {
                "ok": False,
                "error": (
                    "archivo_no_existe"
                ),
            }

        if not archivo.is_file():

            return {
                "ok": False,
                "error": (
                    "no_es_archivo"
                ),
            }

        tamanio = archivo.stat().st_size

        if (
            tamanio
            > self.MAX_TAMANIO_ARCHIVO
        ):

            return {
                "ok": False,
                "error": (
                    "archivo_demasiado_grande"
                ),
            }

        try:

            contenido = (
                archivo.read_text(
                    encoding="utf-8"
                )
            )

        except UnicodeDecodeError:

            return {
                "ok": False,
                "error": (
                    "archivo_no_textual"
                ),
            }

        return {
            "ok": True,
            "ruta": (
                archivo
                .relative_to(
                    self.raiz
                )
                .as_posix()
            ),
            "contenido": contenido,
            "lineas": len(
                contenido.splitlines()
            ),
            "tamanio": tamanio,
        }

    # =========================================================
    # BUSCAR TEXTO
    # =========================================================

    def buscar_texto(
        self,
        texto: str,
        extension: str | None = ".py",
        sensible_mayusculas: bool = False,
        limite: int = 100,
    ) -> list[CoincidenciaCodigo]:

        texto = texto.strip()

        if not texto:
            return []

        coincidencias = []

        objetivo = (
            texto
            if sensible_mayusculas
            else texto.lower()
        )

        archivos = self.listar_archivos(
            extension
        )

        for archivo_info in archivos:

            lectura = self.leer_archivo(
                archivo_info.ruta
            )

            if not lectura.get(
                "ok"
            ):
                continue

            lineas = (
                lectura["contenido"]
                .splitlines()
            )

            for numero, linea in enumerate(
                lineas,
                start=1,
            ):

                comparacion = (
                    linea
                    if sensible_mayusculas
                    else linea.lower()
                )

                if objetivo not in comparacion:
                    continue

                coincidencias.append(
                    CoincidenciaCodigo(
                        archivo=(
                            archivo_info.ruta
                        ),
                        linea=numero,
                        texto=linea.strip(),
                    )
                )

                if (
                    len(coincidencias)
                    >= limite
                ):
                    return coincidencias

        return coincidencias

    # =========================================================
    # BUSCAR SÍMBOLO PYTHON
    # =========================================================

    def buscar_simbolo(
        self,
        nombre: str,
    ) -> list[dict]:

        nombre = nombre.strip()

        if not nombre:
            return []

        resultados = []

        for archivo_info in (
            self.listar_python()
        ):

            lectura = self.leer_archivo(
                archivo_info.ruta
            )

            if not lectura.get("ok"):
                continue

            try:

                arbol = ast.parse(
                    lectura["contenido"],
                    filename=archivo_info.ruta,
                )

            except SyntaxError:
                continue

            for nodo in ast.walk(
                arbol
            ):

                if isinstance(
                    nodo,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                    ),
                ):

                    if nodo.name != nombre:
                        continue

                    resultados.append({
                        "archivo":
                            archivo_info.ruta,

                        "linea":
                            nodo.lineno,

                        "tipo": (
                            "clase"
                            if isinstance(
                                nodo,
                                ast.ClassDef,
                            )
                            else "funcion"
                        ),

                        "nombre":
                            nodo.name,
                    })

        return resultados

    # =========================================================
    # BUSCAR IMPORT
    # =========================================================

    def buscar_import(
        self,
        modulo: str,
    ) -> list[dict]:

        modulo = modulo.strip()

        if not modulo:
            return []

        resultados = []

        for archivo_info in (
            self.listar_python()
        ):

            lectura = self.leer_archivo(
                archivo_info.ruta
            )

            if not lectura.get("ok"):
                continue

            try:

                arbol = ast.parse(
                    lectura["contenido"],
                    filename=archivo_info.ruta,
                )

            except SyntaxError:
                continue

            for nodo in ast.walk(
                arbol
            ):

                if isinstance(
                    nodo,
                    ast.Import,
                ):

                    for alias in nodo.names:

                        if (
                            alias.name == modulo
                            or alias.name.startswith(
                                modulo + "."
                            )
                        ):

                            resultados.append({
                                "archivo":
                                    archivo_info.ruta,

                                "linea":
                                    nodo.lineno,

                                "modulo":
                                    alias.name,
                            })

                elif isinstance(
                    nodo,
                    ast.ImportFrom,
                ):

                    nombre_modulo = (
                        nodo.module
                        or ""
                    )

                    if (
                        nombre_modulo == modulo
                        or nombre_modulo.startswith(
                            modulo + "."
                        )
                    ):

                        resultados.append({
                            "archivo":
                                archivo_info.ruta,

                            "linea":
                                nodo.lineno,

                            "modulo":
                                nombre_modulo,
                        })

        return resultados