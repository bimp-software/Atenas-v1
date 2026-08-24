from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class EstadoVisionOllama:
    disponible: bool
    servidor: str
    modelo: str

    mensaje: str = ""
    error: str | None = None


class AdaptadorVisionOllama:
    """
    Adaptador multimodal local para Ollama.

    Características:
    - no requiere requests;
    - usa únicamente urllib de la librería estándar;
    - no hace llamadas en __init__;
    - admite imágenes locales;
    - devuelve texto crudo al InterpretadorVisual;
    - permite cambiar modelo/servidor mediante variables de entorno.

    Variables opcionales:
        ATENAS_OLLAMA_URL
        ATENAS_VISION_MODEL

    Valores por defecto:
        http://127.0.0.1:11434
        qwen2.5vl:7b
    """

    def __init__(
        self,
        modelo: str | None = None,
        servidor: str | None = None,
        timeout: float = 120.0,
    ):
        self.modelo = (
            modelo
            or os.getenv(
                "ATENAS_VISION_MODEL"
            )
            or "qwen2.5vl:7b"
        ).strip()

        self.servidor = (
            servidor
            or os.getenv(
                "ATENAS_OLLAMA_URL"
            )
            or "http://127.0.0.1:11434"
        ).rstrip("/")

        self.timeout = max(
            5.0,
            float(
                timeout
            ),
        )

    # =========================================================
    # HTTP
    # =========================================================

    def _request_json(
        self,
        ruta: str,
        payload: dict[str, Any] | None = None,
        metodo: str | None = None,
    ) -> dict[str, Any]:

        url = (
            self.servidor
            + ruta
        )

        cuerpo = None

        if payload is not None:

            cuerpo = json.dumps(
                payload,
                ensure_ascii=False,
            ).encode(
                "utf-8"
            )

        request = urllib.request.Request(
            url=url,
            data=cuerpo,
            method=(
                metodo
                or (
                    "POST"
                    if payload is not None
                    else "GET"
                )
            ),
            headers={
                "Content-Type":
                    "application/json",
            },
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as respuesta:

                contenido = (
                    respuesta.read()
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )

        except urllib.error.HTTPError as error:

            detalle = ""

            try:

                detalle = (
                    error.read()
                    .decode(
                        "utf-8",
                        errors="replace",
                    )
                )

            except Exception:
                pass

            raise RuntimeError(
                (
                    f"ollama_http_{error.code}: "
                    f"{detalle or error.reason}"
                )
            ) from error

        except urllib.error.URLError as error:

            raise RuntimeError(
                (
                    "ollama_no_disponible: "
                    f"{error.reason}"
                )
            ) from error

        try:

            return json.loads(
                contenido
            )

        except json.JSONDecodeError as error:

            raise RuntimeError(
                "respuesta_ollama_no_json"
            ) from error

    # =========================================================
    # ESTADO
    # =========================================================

    def estado(
        self,
    ) -> EstadoVisionOllama:

        try:

            datos = (
                self._request_json(
                    "/api/tags"
                )
            )

            modelos = {
                str(
                    item.get(
                        "name",
                        "",
                    )
                )
                for item
                in (
                    datos.get(
                        "models",
                        []
                    )
                    or []
                )
                if isinstance(
                    item,
                    dict,
                )
            }

            # Ollama puede mostrar nombre completo con tag.
            disponible_modelo = (
                self.modelo in modelos
                or any(
                    nombre.split(
                        ":",
                        1,
                    )[0]
                    == self.modelo.split(
                        ":",
                        1,
                    )[0]
                    for nombre
                    in modelos
                )
            )

            if not disponible_modelo:

                return EstadoVisionOllama(
                    disponible=False,
                    servidor=self.servidor,
                    modelo=self.modelo,
                    mensaje=(
                        "Ollama responde, pero el modelo "
                        "visual configurado no está instalado."
                    ),
                    error="modelo_vision_no_instalado",
                )

            return EstadoVisionOllama(
                disponible=True,
                servidor=self.servidor,
                modelo=self.modelo,
                mensaje=(
                    "Modelo visual local disponible."
                ),
            )

        except Exception as error:

            return EstadoVisionOllama(
                disponible=False,
                servidor=self.servidor,
                modelo=self.modelo,
                mensaje=(
                    "No se pudo verificar Ollama."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    # =========================================================
    # IMAGEN
    # =========================================================

    @staticmethod
    def _imagen_base64(
        ruta_imagen: str | Path,
    ) -> str:

        ruta = Path(
            ruta_imagen
        ).expanduser().resolve()

        if not ruta.exists():

            raise FileNotFoundError(
                f"Imagen no encontrada: {ruta}"
            )

        if not ruta.is_file():

            raise ValueError(
                "La ruta de imagen no es un archivo."
            )

        # Límite defensivo para evitar mandar archivos enormes.
        tamaño = (
            ruta.stat()
            .st_size
        )

        if tamaño > 25_000_000:

            raise ValueError(
                (
                    "La captura supera el límite "
                    "de 25 MB."
                )
            )

        return (
            base64.b64encode(
                ruta.read_bytes()
            )
            .decode(
                "ascii"
            )
        )

    # =========================================================
    # VISIÓN
    # =========================================================

    def analizar_imagen(
        self,
        ruta_imagen: str,
        prompt: str,
    ) -> str:

        imagen = (
            self._imagen_base64(
                ruta_imagen
            )
        )

        payload = {
            "model":
                self.modelo,

            "stream":
                False,

            "messages": [
                {
                    "role":
                        "user",

                    "content":
                        prompt,

                    "images": [
                        imagen
                    ],
                }
            ],

            "options": {
                "temperature":
                    0.1,
            },
        }

        respuesta = (
            self._request_json(
                "/api/chat",
                payload=payload,
            )
        )

        mensaje = (
            respuesta.get(
                "message",
                {}
            )
            or {}
        )

        contenido = str(
            mensaje.get(
                "content",
                ""
            )
            or ""
        ).strip()

        if not contenido:

            raise RuntimeError(
                "ollama_respuesta_vacia"
            )

        return contenido

    # Alias compatibles con InterpretadorVisual.
    def vision(
        self,
        ruta_imagen: str,
        prompt: str,
    ) -> str:

        return self.analizar_imagen(
            ruta_imagen,
            prompt,
        )

    def chat_vision(
        self,
        ruta_imagen: str,
        prompt: str,
    ) -> str:

        return self.analizar_imagen(
            ruta_imagen,
            prompt,
        )