from __future__ import annotations

import json

from pathlib import Path
from typing import Any

from .analizador_documentos import (
    DocumentoAnalizado,
    FragmentoDocumento,
    TipoDocumento,
)


class RegistroDocumentos:
    """
    Índice persistente ligero de documentos conocidos por ATENAS.

    Guarda metadatos y fragmentos, no duplica el archivo original.
    """

    def __init__(
        self,
        ruta: str | Path = (
            "data/agente/documentos/documentos.json"
        ),
    ):
        self.ruta = Path(
            ruta
        ).expanduser().resolve()

        self.ruta.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.ruta.exists():
            self.ruta.write_text(
                "[]",
                encoding="utf-8",
            )

    @staticmethod
    def _a_dict(
        documento: DocumentoAnalizado,
    ) -> dict[str, Any]:
        return {
            "id":
                documento.id,

            "ruta":
                documento.ruta,

            "nombre":
                documento.nombre,

            "tipo":
                documento.tipo.value,

            "hash_sha256":
                documento.hash_sha256,

            "tamaño_bytes":
                documento.tamaño_bytes,

            "paginas":
                documento.paginas,

            "creado_en":
                documento.creado_en,

            "metadata":
                documento.metadata,

            "fragmentos": [
                {
                    "indice":
                        f.indice,

                    "texto":
                        f.texto,

                    "pagina":
                        f.pagina,

                    "inicio":
                        f.inicio,

                    "fin":
                        f.fin,

                    "metadata":
                        f.metadata,
                }
                for f in documento.fragmentos
            ],
        }

    @staticmethod
    def _desde_dict(
        datos: dict[str, Any],
    ) -> DocumentoAnalizado:
        return DocumentoAnalizado(
            id=str(
                datos["id"]
            ),
            ruta=str(
                datos.get(
                    "ruta",
                    "",
                )
            ),
            nombre=str(
                datos.get(
                    "nombre",
                    "",
                )
            ),
            tipo=TipoDocumento(
                datos.get(
                    "tipo",
                    "desconocido",
                )
            ),
            hash_sha256=str(
                datos.get(
                    "hash_sha256",
                    "",
                )
            ),
            tamaño_bytes=int(
                datos.get(
                    "tamaño_bytes",
                    0,
                )
                or 0
            ),
            texto="",
            paginas=(
                int(
                    datos["paginas"]
                )
                if datos.get(
                    "paginas"
                )
                is not None
                else None
            ),
            fragmentos=[
                FragmentoDocumento(
                    indice=int(
                        item.get(
                            "indice",
                            0,
                        )
                    ),
                    texto=str(
                        item.get(
                            "texto",
                            "",
                        )
                    ),
                    pagina=(
                        int(
                            item["pagina"]
                        )
                        if item.get(
                            "pagina"
                        )
                        is not None
                        else None
                    ),
                    inicio=(
                        int(
                            item["inicio"]
                        )
                        if item.get(
                            "inicio"
                        )
                        is not None
                        else None
                    ),
                    fin=(
                        int(
                            item["fin"]
                        )
                        if item.get(
                            "fin"
                        )
                        is not None
                        else None
                    ),
                    metadata=(
                        item.get(
                            "metadata",
                            {},
                        )
                        or {}
                    ),
                )
                for item in (
                    datos.get(
                        "fragmentos",
                        []
                    )
                    or []
                )
                if isinstance(
                    item,
                    dict,
                )
            ],
            creado_en=str(
                datos.get(
                    "creado_en",
                    "",
                )
            ),
            metadata=(
                datos.get(
                    "metadata",
                    {},
                )
                or {}
            ),
        )

    def listar(
        self,
    ) -> list[DocumentoAnalizado]:
        try:
            datos = json.loads(
                self.ruta.read_text(
                    encoding="utf-8"
                )
            )
        except Exception:
            datos = []

        if not isinstance(
            datos,
            list,
        ):
            datos = []

        salida = []

        for item in datos:
            if not isinstance(
                item,
                dict,
            ):
                continue

            try:
                salida.append(
                    self._desde_dict(
                        item
                    )
                )
            except Exception:
                continue

        return salida

    def _guardar_todos(
        self,
        documentos: list[DocumentoAnalizado],
    ) -> None:
        temporal = self.ruta.with_suffix(
            ".tmp"
        )

        temporal.write_text(
            json.dumps(
                [
                    self._a_dict(
                        documento
                    )
                    for documento
                    in documentos
                ],
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        temporal.replace(
            self.ruta
        )

    def guardar(
        self,
        documento: DocumentoAnalizado,
    ) -> None:
        actuales = [
            doc
            for doc in self.listar()
            if (
                doc.id
                != documento.id
                and doc.hash_sha256
                != documento.hash_sha256
            )
        ]

        actuales.append(
            documento
        )

        self._guardar_todos(
            actuales
        )

    def obtener(
        self,
        documento_id: str,
    ) -> DocumentoAnalizado | None:
        for documento in self.listar():
            if documento.id == documento_id:
                return documento
        return None

    def buscar(
        self,
        consulta: str,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        consulta = (
            consulta
            or ""
        ).strip().lower()

        if not consulta:
            return []

        resultados = []

        for documento in self.listar():
            for fragmento in documento.fragmentos:
                corpus = fragmento.texto.lower()

                if consulta not in corpus:
                    continue

                posicion = corpus.find(
                    consulta
                )

                inicio = max(
                    0,
                    posicion - 180,
                )

                fin = min(
                    len(fragmento.texto),
                    posicion + len(consulta) + 350,
                )

                resultados.append({
                    "documento_id":
                        documento.id,

                    "nombre":
                        documento.nombre,

                    "ruta":
                        documento.ruta,

                    "pagina":
                        fragmento.pagina,

                    "fragmento_indice":
                        fragmento.indice,

                    "extracto":
                        fragmento.texto[
                            inicio:fin
                        ],
                })

                if len(
                    resultados
                ) >= limite:
                    return resultados

        return resultados