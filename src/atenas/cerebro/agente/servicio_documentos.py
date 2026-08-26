from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .analizador_documentos import (
    AnalizadorDocumentos,
    ResultadoLecturaDocumento,
)
from .registro_documentos import (
    RegistroDocumentos,
)


@dataclass
class ResultadoServicioDocumentos:
    ok: bool
    mensaje: str = ""
    documento_id: str | None = None
    datos: dict[str, Any] | None = None
    error: str | None = None


class ServicioDocumentos:
    """
    Fachada que la futura API/web utilizará para documentos.
    """

    def __init__(
        self,
        analizador: AnalizadorDocumentos | None = None,
        registro: RegistroDocumentos | None = None,
    ):
        self.analizador = analizador or AnalizadorDocumentos()
        self.registro = registro or RegistroDocumentos()

    def importar(
        self,
        ruta: str,
    ) -> ResultadoServicioDocumentos:
        resultado: ResultadoLecturaDocumento = (
            self.analizador.analizar(
                ruta
            )
        )

        if (
            not resultado.ok
            or resultado.documento
            is None
        ):
            return ResultadoServicioDocumentos(
                ok=False,
                mensaje=resultado.mensaje,
                error=resultado.error,
            )

        documento = resultado.documento

        self.registro.guardar(
            documento
        )

        return ResultadoServicioDocumentos(
            ok=True,
            mensaje="Documento importado.",
            documento_id=documento.id,
            datos={
                "nombre":
                    documento.nombre,

                "tipo":
                    documento.tipo.value,

                "paginas":
                    documento.paginas,

                "fragmentos":
                    len(
                        documento.fragmentos
                    ),

                "tamaño_bytes":
                    documento.tamaño_bytes,
            },
        )

    def listar(
        self,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id":
                    documento.id,

                "nombre":
                    documento.nombre,

                "tipo":
                    documento.tipo.value,

                "ruta":
                    documento.ruta,

                "paginas":
                    documento.paginas,

                "fragmentos":
                    len(
                        documento.fragmentos
                    ),

                "creado_en":
                    documento.creado_en,
            }
            for documento in self.registro.listar()
        ]

    def buscar(
        self,
        consulta: str,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        return self.registro.buscar(
            consulta=consulta,
            limite=limite,
        )