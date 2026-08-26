from __future__ import annotations

import hashlib
import json
import mimetypes
import uuid

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class TipoDocumento(str, Enum):
    PDF = "pdf"
    TEXTO = "texto"
    MARKDOWN = "markdown"
    JSON = "json"
    CSV = "csv"
    DESCONOCIDO = "desconocido"


@dataclass
class FragmentoDocumento:
    indice: int
    texto: str
    pagina: int | None = None
    inicio: int | None = None
    fin: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentoAnalizado:
    id: str
    ruta: str
    nombre: str
    tipo: TipoDocumento

    hash_sha256: str
    tamaño_bytes: int

    texto: str = ""
    paginas: int | None = None

    fragmentos: list[FragmentoDocumento] = field(default_factory=list)

    creado_en: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResultadoLecturaDocumento:
    ok: bool
    documento: DocumentoAnalizado | None = None

    mensaje: str = ""
    error: str | None = None


class AnalizadorDocumentos:
    """
    Capa local de lectura y normalización de documentos para ATENAS.

    Soporta inicialmente:
    - PDF
    - TXT
    - MD
    - JSON
    - CSV

    Los PDFs se leen con pypdf si está instalado.

    El módulo NO decide qué significa el documento ni qué hacer con él.
    Solo:
        archivo -> texto -> páginas -> fragmentos estructurados
    """

    def __init__(
        self,
        tamaño_fragmento: int = 1800,
        solapamiento: int = 200,
    ):
        self.tamaño_fragmento = max(
            500,
            int(tamaño_fragmento),
        )

        self.solapamiento = max(
            0,
            min(
                int(solapamiento),
                self.tamaño_fragmento // 2,
            ),
        )

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _ahora() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _hash(ruta: Path) -> str:
        digest = hashlib.sha256()

        with ruta.open("rb") as archivo:
            while True:
                bloque = archivo.read(1024 * 1024)

                if not bloque:
                    break

                digest.update(bloque)

        return digest.hexdigest()

    @staticmethod
    def _tipo(ruta: Path) -> TipoDocumento:
        extension = ruta.suffix.lower()

        mapa = {
            ".pdf": TipoDocumento.PDF,
            ".txt": TipoDocumento.TEXTO,
            ".md": TipoDocumento.MARKDOWN,
            ".markdown": TipoDocumento.MARKDOWN,
            ".json": TipoDocumento.JSON,
            ".csv": TipoDocumento.CSV,
        }

        return mapa.get(
            extension,
            TipoDocumento.DESCONOCIDO,
        )

    # =========================================================
    # LECTURA
    # =========================================================

    @staticmethod
    def _leer_texto(ruta: Path) -> str:
        return ruta.read_text(
            encoding="utf-8",
            errors="replace",
        )

    @staticmethod
    def _leer_json(ruta: Path) -> str:
        datos = json.loads(
            ruta.read_text(
                encoding="utf-8",
            )
        )

        return json.dumps(
            datos,
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def _leer_pdf(
        ruta: Path,
    ) -> tuple[str, list[tuple[int, str]]]:
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise RuntimeError(
                "pypdf_no_instalado"
            ) from error

        lector = PdfReader(
            str(ruta)
        )

        paginas: list[tuple[int, str]] = []
        partes: list[str] = []

        for numero, pagina in enumerate(
            lector.pages,
            start=1,
        ):
            try:
                texto = pagina.extract_text() or ""
            except Exception:
                texto = ""

            texto = texto.strip()

            paginas.append(
                (
                    numero,
                    texto,
                )
            )

            if texto:
                partes.append(
                    f"\n[PÁGINA {numero}]\n{texto}"
                )

        return (
            "\n".join(partes).strip(),
            paginas,
        )

    # =========================================================
    # FRAGMENTACIÓN
    # =========================================================

    def _fragmentar_texto(
        self,
        texto: str,
        pagina: int | None = None,
    ) -> list[FragmentoDocumento]:
        texto = (
            texto
            or ""
        ).strip()

        if not texto:
            return []

        salida: list[FragmentoDocumento] = []

        inicio = 0
        indice = 0
        longitud = len(texto)

        while inicio < longitud:
            fin = min(
                longitud,
                inicio + self.tamaño_fragmento,
            )

            fragmento = texto[
                inicio:fin
            ].strip()

            if fragmento:
                salida.append(
                    FragmentoDocumento(
                        indice=indice,
                        texto=fragmento,
                        pagina=pagina,
                        inicio=inicio,
                        fin=fin,
                    )
                )

                indice += 1

            if fin >= longitud:
                break

            inicio = max(
                0,
                fin - self.solapamiento,
            )

        return salida

    def _fragmentar_paginas(
        self,
        paginas: list[tuple[int, str]],
    ) -> list[FragmentoDocumento]:
        salida: list[FragmentoDocumento] = []
        indice_global = 0

        for pagina, texto in paginas:
            parciales = self._fragmentar_texto(
                texto,
                pagina=pagina,
            )

            for fragmento in parciales:
                fragmento.indice = indice_global
                indice_global += 1
                salida.append(fragmento)

        return salida

    # =========================================================
    # API
    # =========================================================

    def analizar(
        self,
        ruta: str | Path,
    ) -> ResultadoLecturaDocumento:
        archivo = Path(
            ruta
        ).expanduser().resolve()

        if not archivo.exists():
            return ResultadoLecturaDocumento(
                ok=False,
                error="archivo_no_existe",
                mensaje=(
                    f"No existe el archivo: {archivo}"
                ),
            )

        if not archivo.is_file():
            return ResultadoLecturaDocumento(
                ok=False,
                error="ruta_no_es_archivo",
            )

        tipo = self._tipo(
            archivo
        )

        if tipo == TipoDocumento.DESCONOCIDO:
            return ResultadoLecturaDocumento(
                ok=False,
                error="tipo_documento_no_soportado",
                mensaje=(
                    f"Formato no soportado: {archivo.suffix}"
                ),
            )

        try:
            paginas = None

            if tipo == TipoDocumento.PDF:
                texto, paginas_pdf = self._leer_pdf(
                    archivo
                )

                fragmentos = self._fragmentar_paginas(
                    paginas_pdf
                )

                paginas = len(
                    paginas_pdf
                )

            elif tipo == TipoDocumento.JSON:
                texto = self._leer_json(
                    archivo
                )

                fragmentos = self._fragmentar_texto(
                    texto
                )

            else:
                texto = self._leer_texto(
                    archivo
                )

                fragmentos = self._fragmentar_texto(
                    texto
                )

            documento = DocumentoAnalizado(
                id=str(
                    uuid.uuid4()
                ),
                ruta=str(
                    archivo
                ),
                nombre=archivo.name,
                tipo=tipo,
                hash_sha256=self._hash(
                    archivo
                ),
                tamaño_bytes=archivo.stat().st_size,
                texto=texto,
                paginas=paginas,
                fragmentos=fragmentos,
                creado_en=self._ahora(),
                metadata={
                    "mime":
                        mimetypes.guess_type(
                            str(archivo)
                        )[0],

                    "extension":
                        archivo.suffix.lower(),
                },
            )

            return ResultadoLecturaDocumento(
                ok=True,
                documento=documento,
                mensaje=(
                    "Documento analizado correctamente."
                ),
            )

        except RuntimeError as error:
            if str(error) == "pypdf_no_instalado":
                return ResultadoLecturaDocumento(
                    ok=False,
                    error="pypdf_no_instalado",
                    mensaje=(
                        "Para analizar PDFs instala pypdf."
                    ),
                )

            return ResultadoLecturaDocumento(
                ok=False,
                error=f"RuntimeError: {error}",
            )

        except Exception as error:
            return ResultadoLecturaDocumento(
                ok=False,
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
                mensaje=(
                    "No se pudo analizar el documento."
                ),
            )