from __future__ import annotations

import ast
import json
import re

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .planificador_sistema_software import (
    TareaSoftware,
)


@dataclass
class ArchivoTareaGenerado:
    ruta: str
    lenguaje: str
    valido: bool
    error: str | None = None


@dataclass
class ResultadoProgramacionTarea:
    ok: bool

    tarea_id: str
    titulo: str

    archivos: list[
        ArchivoTareaGenerado
    ] = field(
        default_factory=list
    )

    resumen: str = ""

    completado: bool = False

    error: str | None = None


class ProgramadorTareaSoftware:
    """
    Programa UNA tarea pequeña de un plan de software.

    No intenta construir el sistema entero de una vez.

    Puede crear archivos de:
    - backend;
    - API;
    - frontend;
    - escritorio;
    - base de datos/migraciones;
    - tests;
    - configuración;
    - documentación técnica.

    Seguridad:
    - solo escribe dentro de la carpeta del proyecto;
    - bloquea rutas absolutas y '..';
    - no ejecuta shell;
    - no instala paquetes;
    - valida Python y JSON antes de escribir.
    """

    EXTENSIONES_PERMITIDAS = {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".html",
        ".css",
        ".json",
        ".md",
        ".txt",
        ".sql",
        ".yml",
        ".yaml",
        ".toml",
        ".ini",
        ".env.example",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".ino",
        ".java",
        ".rs",
        ".go",
        ".php",
    }

    def __init__(
        self,
        llm: Any,
    ):
        self.llm = llm

    # =========================================================
    # LLM
    # =========================================================

    def _preguntar(
        self,
        mensajes: list[dict],
    ) -> str:

        if hasattr(
            self.llm,
            "chat",
        ):

            respuesta = self.llm.chat(
                mensajes
            )

            if isinstance(
                respuesta,
                str,
            ):
                return respuesta

            if isinstance(
                respuesta,
                dict,
            ):

                message = (
                    respuesta.get(
                        "message"
                    )
                    or {}
                )

                if isinstance(
                    message,
                    dict,
                ):

                    contenido = (
                        message.get(
                            "content"
                        )
                    )

                    if contenido:
                        return str(
                            contenido
                        )

                if respuesta.get(
                    "content"
                ):

                    return str(
                        respuesta[
                            "content"
                        ]
                    )

        if hasattr(
            self.llm,
            "chat_stream",
        ):

            return "".join(
                str(
                    fragmento
                )
                for fragmento
                in self.llm.chat_stream(
                    mensajes
                )
            )

        raise RuntimeError(
            "LLM incompatible."
        )

    @staticmethod
    def _extraer_json(
        texto: str,
    ) -> dict:

        texto = (
            texto
            or ""
        ).strip()

        bloque = re.search(
            r"```(?:json)?\s*(\{.*\})\s*```",
            texto,
            re.DOTALL,
        )

        if bloque:

            texto = bloque.group(1)

        else:

            inicio = texto.find("{")
            fin = texto.rfind("}")

            if (
                inicio < 0
                or fin <= inicio
            ):

                raise ValueError(
                    "No se encontró JSON válido."
                )

            texto = texto[
                inicio:
                fin + 1
            ]

        datos = json.loads(
            texto
        )

        if not isinstance(
            datos,
            dict,
        ):

            raise ValueError(
                "Respuesta JSON inválida."
            )

        return datos

    # =========================================================
    # RUTAS
    # =========================================================

    @staticmethod
    def _normalizar_ruta(
        ruta: str,
    ) -> str:

        ruta = (
            ruta
            or ""
        ).strip()

        ruta = ruta.replace(
            "\\",
            "/",
        )

        while ruta.startswith(
            "./"
        ):

            ruta = ruta[
                2:
            ]

        return ruta

    def _ruta_permitida(
        self,
        ruta: str,
    ) -> bool:

        ruta = self._normalizar_ruta(
            ruta
        )

        if not ruta:
            return False

        if ruta.startswith(
            "/"
        ):

            return False

        if ":" in ruta:
            return False

        partes = Path(
            ruta
        ).parts

        if ".." in partes:
            return False

        nombre = Path(
            ruta
        ).name

        if nombre == ".env":
            return False

        extension = Path(
            ruta
        ).suffix.lower()

        if nombre.endswith(
            ".env.example"
        ):

            return True

        return (
            extension
            in self.EXTENSIONES_PERMITIDAS
        )

    # =========================================================
    # VALIDACIÓN
    # =========================================================

    @staticmethod
    def _validar(
        ruta: str,
        contenido: str,
    ) -> tuple[
        bool,
        str | None,
    ]:

        extension = Path(
            ruta
        ).suffix.lower()

        try:

            if extension == ".py":

                ast.parse(
                    contenido
                )

            elif extension == ".json":

                json.loads(
                    contenido
                )

            elif not contenido.strip():

                return (
                    False,
                    "archivo_vacio",
                )

        except Exception as error:

            return (
                False,
                (
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        return (
            True,
            None,
        )

    # =========================================================
    # PROGRAMAR UNA TAREA
    # =========================================================

    def programar(
        self,
        carpeta_proyecto: str | Path,
        tarea: TareaSoftware,
        contexto_sistema: dict,
    ) -> ResultadoProgramacionTarea:

        carpeta = Path(
            carpeta_proyecto
        ).resolve()

        carpeta.mkdir(
            parents=True,
            exist_ok=True,
        )

        system = """
Eres el programador incremental de ATENAS.

Debes implementar UNA sola tarea de un plan de software.

No intentes construir el sistema entero.
Respeta arquitectura, modelo de datos y dependencias recibidas.

Reglas:
- Usa los archivos estimados como guía, no obligación absoluta.
- Mantén responsabilidades separadas.
- No inventes que ejecutaste tests.
- Si la tarea requiere pruebas, genera pruebas coherentes.
- Si requiere documentación, genera documentación puntual.
- No uses rutas absolutas.
- No uses '..'.
- No generes secretos.
- No escribas .env; usa .env.example.
- No ejecutes comandos.
- No instales dependencias.

Devuelve SOLO JSON:

{
  "resumen": "...",
  "completado": true,
  "archivos": [
    {
      "ruta": "src/...",
      "lenguaje": "python",
      "contenido": "..."
    }
  ]
}
""".strip()

        entrada = {
            "tarea": {
                "id":
                    tarea.id,

                "titulo":
                    tarea.titulo,

                "descripcion":
                    tarea.descripcion,

                "tipo":
                    tarea.tipo,

                "prioridad":
                    tarea.prioridad,

                "criterios_aceptacion":
                    tarea
                    .criterios_aceptacion,

                "archivos_estimados":
                    tarea
                    .archivos_estimados,

                "lenguaje":
                    tarea.lenguaje,

                "tecnologia":
                    tarea.tecnologia,

                "requiere_pruebas":
                    tarea
                    .requiere_pruebas,

                "requiere_documentacion":
                    tarea
                    .requiere_documentacion,
            },

            "contexto_sistema":
                contexto_sistema,
        }

        try:

            respuesta = (
                self._preguntar([
                    {
                        "role": "system",
                        "content": system,
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            entrada,
                            ensure_ascii=False,
                            indent=2,
                            default=str,
                        ),
                    },
                ])
            )

            datos = (
                self._extraer_json(
                    respuesta
                )
            )

        except Exception as error:

            return ResultadoProgramacionTarea(
                ok=False,
                tarea_id=tarea.id,
                titulo=tarea.titulo,
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        archivos_raw = (
            datos.get(
                "archivos"
            )
        )

        if (
            not isinstance(
                archivos_raw,
                list,
            )
            or not archivos_raw
        ):

            return ResultadoProgramacionTarea(
                ok=False,
                tarea_id=tarea.id,
                titulo=tarea.titulo,
                resumen=str(
                    datos.get(
                        "resumen",
                        "",
                    )
                    or ""
                ),
                error="sin_archivos",
            )

        resultados = []

        for item in archivos_raw[
            :20
        ]:

            if not isinstance(
                item,
                dict,
            ):
                continue

            ruta = (
                self._normalizar_ruta(
                    str(
                        item.get(
                            "ruta",
                            "",
                        )
                        or ""
                    )
                )
            )

            lenguaje = str(
                item.get(
                    "lenguaje",
                    "",
                )
                or ""
            )

            contenido = str(
                item.get(
                    "contenido",
                    "",
                )
                or ""
            )

            if not self._ruta_permitida(
                ruta
            ):

                resultados.append(
                    ArchivoTareaGenerado(
                        ruta=ruta,
                        lenguaje=lenguaje,
                        valido=False,
                        error="ruta_no_permitida",
                    )
                )

                continue

            valido, error = (
                self._validar(
                    ruta,
                    contenido,
                )
            )

            if not valido:

                resultados.append(
                    ArchivoTareaGenerado(
                        ruta=ruta,
                        lenguaje=lenguaje,
                        valido=False,
                        error=error,
                    )
                )

                continue

            destino = (
                carpeta
                / ruta
            ).resolve()

            try:

                destino.relative_to(
                    carpeta
                )

            except ValueError:

                resultados.append(
                    ArchivoTareaGenerado(
                        ruta=ruta,
                        lenguaje=lenguaje,
                        valido=False,
                        error="escape_de_carpeta",
                    )
                )

                continue

            destino.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            destino.write_text(
                contenido,
                encoding="utf-8",
            )

            resultados.append(
                ArchivoTareaGenerado(
                    ruta=ruta,
                    lenguaje=lenguaje,
                    valido=True,
                )
            )

        validos = [
            archivo
            for archivo
            in resultados
            if archivo.valido
        ]

        invalidos = [
            archivo
            for archivo
            in resultados
            if not archivo.valido
        ]

        completado = bool(
            datos.get(
                "completado",
                False,
            )
            and validos
            and not invalidos
        )

        return ResultadoProgramacionTarea(
            ok=bool(
                validos
            ),
            tarea_id=tarea.id,
            titulo=tarea.titulo,
            archivos=resultados,
            resumen=str(
                datos.get(
                    "resumen",
                    "",
                )
                or ""
            ),
            completado=completado,
            error=(
                None
                if validos
                else "ningun_archivo_valido"
            ),
        )