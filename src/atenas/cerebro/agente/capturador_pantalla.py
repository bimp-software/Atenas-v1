from __future__ import annotations

import json
import platform
import uuid

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gestor_ventanas import (
    GestorVentanas,
)


@dataclass
class CapturaPantalla:
    id: str
    ruta: str

    ancho: int
    alto: int

    creada_en: str

    tipo: str = "pantalla"

    ventana_titulo: str | None = None
    ventana_hwnd: int | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ResultadoCapturaPantalla:
    ok: bool
    accion: str

    captura: CapturaPantalla | None = None

    mensaje: str = ""
    error: str | None = None


class CapturadorPantalla:
    """
    Captura visual estructurada de pantalla/ventanas.

    V1:
    - captura la pantalla completa;
    - captura una ventana conocida usando su geometría;
    - persiste PNG + JSON de metadatos;
    - no hace OCR;
    - no intenta interpretar visualmente la imagen.

    Dependencia opcional:
        Pillow (PIL.ImageGrab)

    Si Pillow no está disponible, el módulo falla de forma explícita
    sin romper el resto de ATENAS.
    """

    def __init__(
        self,
        raiz_capturas: str | Path = (
            "data/agente/percepcion/capturas"
        ),
        gestor_ventanas: GestorVentanas | None = None,
    ):
        self.raiz_capturas = Path(
            raiz_capturas
        ).resolve()

        self.raiz_capturas.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.gestor_ventanas = (
            gestor_ventanas
            or GestorVentanas()
        )

        self.sistema = (
            platform.system()
            .strip()
            .lower()
        )

        self._image_grab = None
        self._pillow_disponible = False

        self._inicializar_backend()

    # =========================================================
    # BACKEND
    # =========================================================

    def _inicializar_backend(
        self,
    ) -> None:

        try:

            from PIL import ImageGrab

            self._image_grab = (
                ImageGrab
            )

            self._pillow_disponible = (
                True
            )

        except Exception:

            self._image_grab = None
            self._pillow_disponible = (
                False
            )

    @property
    def disponible(
        self,
    ) -> bool:

        return (
            self._pillow_disponible
        )

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _ahora(
    ) -> str:

        return (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

    def _rutas_nueva_captura(
        self,
        prefijo: str,
    ) -> tuple[str, Path, Path]:

        identificador = str(
            uuid.uuid4()
        )

        sello = (
            datetime.now()
            .strftime(
                "%Y%m%d_%H%M%S_%f"
            )
        )

        base = (
            f"{prefijo}_{sello}_"
            f"{identificador[:8]}"
        )

        ruta_png = (
            self.raiz_capturas
            / f"{base}.png"
        )

        ruta_json = (
            self.raiz_capturas
            / f"{base}.json"
        )

        return (
            identificador,
            ruta_png,
            ruta_json,
        )

    @staticmethod
    def _guardar_metadata(
        ruta_json: Path,
        captura: CapturaPantalla,
    ) -> None:

        ruta_json.write_text(
            json.dumps(
                {
                    "id":
                        captura.id,

                    "ruta":
                        captura.ruta,

                    "ancho":
                        captura.ancho,

                    "alto":
                        captura.alto,

                    "creada_en":
                        captura.creada_en,

                    "tipo":
                        captura.tipo,

                    "ventana_titulo":
                        captura.ventana_titulo,

                    "ventana_hwnd":
                        captura.ventana_hwnd,

                    "metadata":
                        captura.metadata,
                },
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    def _sin_backend(
        self,
        accion: str,
    ) -> ResultadoCapturaPantalla:

        return ResultadoCapturaPantalla(
            ok=False,
            accion=accion,
            error="pillow_no_disponible",
            mensaje=(
                "CapturadorPantalla necesita Pillow "
                "(PIL.ImageGrab) para realizar capturas."
            ),
        )

    # =========================================================
    # PANTALLA COMPLETA
    # =========================================================

    def capturar_pantalla(
        self,
        todos_monitores: bool = True,
    ) -> ResultadoCapturaPantalla:

        if not self.disponible:

            return self._sin_backend(
                "capturar_pantalla"
            )

        try:

            imagen = (
                self._image_grab.grab(
                    all_screens=bool(
                        todos_monitores
                    )
                )
            )

            identificador, ruta_png, ruta_json = (
                self._rutas_nueva_captura(
                    "pantalla"
                )
            )

            imagen.save(
                ruta_png,
                format="PNG",
            )

            ancho, alto = (
                imagen.size
            )

            captura = CapturaPantalla(
                id=identificador,
                ruta=str(
                    ruta_png
                ),
                ancho=int(
                    ancho
                ),
                alto=int(
                    alto
                ),
                creada_en=self._ahora(),
                tipo="pantalla",
                metadata={
                    "todos_monitores":
                        bool(
                            todos_monitores
                        ),
                },
            )

            self._guardar_metadata(
                ruta_json,
                captura,
            )

            return ResultadoCapturaPantalla(
                ok=True,
                accion="capturar_pantalla",
                captura=captura,
                mensaje=(
                    "Captura de pantalla guardada."
                ),
            )

        except Exception as error:

            return ResultadoCapturaPantalla(
                ok=False,
                accion="capturar_pantalla",
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    # =========================================================
    # VENTANA
    # =========================================================

    def capturar_ventana(
        self,
        titulo: str,
    ) -> ResultadoCapturaPantalla:

        if not self.disponible:

            return self._sin_backend(
                "capturar_ventana"
            )

        resultado_ventana = (
            self.gestor_ventanas
            .buscar(
                titulo
            )
        )

        if (
            not resultado_ventana.ok
            or resultado_ventana.ventana
            is None
        ):

            return ResultadoCapturaPantalla(
                ok=False,
                accion="capturar_ventana",
                error=(
                    resultado_ventana.error
                    or "ventana_no_encontrada"
                ),
                mensaje=(
                    resultado_ventana.mensaje
                ),
            )

        ventana = (
            resultado_ventana.ventana
        )

        if (
            ventana.x is None
            or ventana.y is None
            or ventana.ancho is None
            or ventana.alto is None
        ):

            return ResultadoCapturaPantalla(
                ok=False,
                accion="capturar_ventana",
                error=(
                    "geometria_ventana_no_disponible"
                ),
            )

        if (
            ventana.ancho <= 0
            or ventana.alto <= 0
        ):

            return ResultadoCapturaPantalla(
                ok=False,
                accion="capturar_ventana",
                error="geometria_ventana_invalida",
            )

        try:

            self.gestor_ventanas.activar(
                hwnd=ventana.hwnd
            )

            izquierda = int(
                ventana.x
            )

            arriba = int(
                ventana.y
            )

            derecha = int(
                ventana.x
                + ventana.ancho
            )

            abajo = int(
                ventana.y
                + ventana.alto
            )

            imagen = (
                self._image_grab.grab(
                    bbox=(
                        izquierda,
                        arriba,
                        derecha,
                        abajo,
                    ),
                    all_screens=True,
                )
            )

            identificador, ruta_png, ruta_json = (
                self._rutas_nueva_captura(
                    "ventana"
                )
            )

            imagen.save(
                ruta_png,
                format="PNG",
            )

            ancho, alto = (
                imagen.size
            )

            captura = CapturaPantalla(
                id=identificador,
                ruta=str(
                    ruta_png
                ),
                ancho=int(
                    ancho
                ),
                alto=int(
                    alto
                ),
                creada_en=self._ahora(),
                tipo="ventana",
                ventana_titulo=(
                    ventana.titulo
                ),
                ventana_hwnd=(
                    ventana.hwnd
                ),
                metadata={
                    "x":
                        ventana.x,

                    "y":
                        ventana.y,

                    "ancho_ventana":
                        ventana.ancho,

                    "alto_ventana":
                        ventana.alto,

                    "pid":
                        ventana.proceso_id,
                },
            )

            self._guardar_metadata(
                ruta_json,
                captura,
            )

            return ResultadoCapturaPantalla(
                ok=True,
                accion="capturar_ventana",
                captura=captura,
                mensaje=(
                    f"Captura de la ventana "
                    f"'{ventana.titulo}' guardada."
                ),
            )

        except Exception as error:

            return ResultadoCapturaPantalla(
                ok=False,
                accion="capturar_ventana",
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    # =========================================================
    # ÚLTIMAS
    # =========================================================

    def listar_capturas(
        self,
        limite: int = 30,
    ) -> list[dict[str, Any]]:

        archivos = sorted(
            self.raiz_capturas.glob(
                "*.json"
            ),
            key=lambda ruta: (
                ruta.stat().st_mtime
            ),
            reverse=True,
        )

        resultado = []

        for ruta in archivos[
            :max(
                1,
                int(
                    limite
                ),
            )
        ]:

            try:

                datos = json.loads(
                    ruta.read_text(
                        encoding="utf-8"
                    )
                )

            except Exception:
                continue

            resultado.append(
                datos
            )

        return resultado