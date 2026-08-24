from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .historial_cambios import (
    HistorialCambios,
)

from .parche import (
    GestorParches,
)

from .politica import (
    PoliticaDesarrollo,
)


@dataclass
class ResultadoRollback:
    ok: bool
    cambio_id: str
    archivo: str | None
    mensaje: str


class GestorRollback:

    def __init__(
        self,
        raiz_proyecto: str | Path,
        historial: HistorialCambios,
        politica: PoliticaDesarrollo,
    ):
        self.raiz = Path(
            raiz_proyecto
        ).resolve()

        self.historial = historial
        self.politica = politica

        self.gestor = (
            GestorParches(
                raiz_proyecto=self.raiz,
                politica=self.politica,
            )
        )

    # =========================================================
    # REVERTIR
    # =========================================================

    def revertir(
        self,
        cambio_id: str,
    ) -> ResultadoRollback:

        registro = (
            self.historial.obtener(
                cambio_id
            )
        )

        if registro is None:

            return ResultadoRollback(
                ok=False,
                cambio_id=cambio_id,
                archivo=None,
                mensaje=(
                    "El cambio no existe."
                ),
            )

        archivo = (
            registro["archivo"]
        )

        if registro["estado"] != "aplicado":

            return ResultadoRollback(
                ok=False,
                cambio_id=cambio_id,
                archivo=archivo,
                mensaje=(
                    "El cambio no está "
                    "en estado aplicado."
                ),
            )

        evaluacion = (
            self.politica
            .evaluar_modificacion(
                archivo
            )
        )

        if not evaluacion.permitido:

            return ResultadoRollback(
                ok=False,
                cambio_id=cambio_id,
                archivo=archivo,
                mensaje=(
                    "La política impide "
                    "revertir este archivo."
                ),
            )

        contenido_original = (
            registro.get(
                "contenido_original"
            )
        )

        if contenido_original is None:

            return ResultadoRollback(
                ok=False,
                cambio_id=cambio_id,
                archivo=archivo,
                mensaje=(
                    "No existe snapshot "
                    "del contenido original."
                ),
            )

        ruta = (
            self.raiz
            / archivo
        ).resolve()

        try:

            ruta.write_text(
                contenido_original,
                encoding="utf-8",
            )

        except OSError as error:

            return ResultadoRollback(
                ok=False,
                cambio_id=cambio_id,
                archivo=archivo,
                mensaje=(
                    f"No fue posible revertir: "
                    f"{error}"
                ),
            )

        self.historial.marcar_revertido(
            cambio_id
        )

        return ResultadoRollback(
            ok=True,
            cambio_id=cambio_id,
            archivo=archivo,
            mensaje=(
                "Cambio revertido "
                "correctamente."
            ),
        )