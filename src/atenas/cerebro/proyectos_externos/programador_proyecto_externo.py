from __future__ import annotations

import ast
import json
import re

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ArchivoProyectoGenerado:
    ruta: str
    lenguaje: str
    valido: bool
    error: str | None = None


@dataclass
class ResultadoProgramacionProyectoExterno:
    ok: bool
    carpeta: str
    lenguaje_principal: str | None = None
    archivos: list[ArchivoProyectoGenerado] = field(default_factory=list)
    resumen: str = ""
    completado: bool = False
    error: str | None = None


class ProgramadorProyectoExterno:
    """
    Genera una solución pequeña/mediana directamente dentro de un
    proyecto externo ya creado.

    Seguridad:
    - solo escribe dentro de la carpeta del proyecto;
    - bloquea rutas absolutas y '..';
    - no ejecuta shell;
    - no instala paquetes;
    - valida Python y JSON antes de escribirlos;
    - no sobrescribe documentación estructural salvo que el LLM
      genere archivos distintos.
    """

    EXTENSIONES_PERMITIDAS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".md": "markdown",
        ".txt": "text",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".ino": "arduino",
        ".java": "java",
        ".rs": "rust",
        ".go": "go",
        ".php": "php",
        ".sql": "sql",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".toml": "toml",
    }

    ARCHIVOS_PROTEGIDOS = {
        "proyecto.json",
        "ESPECIFICACIONES.md",
        "ESPECIFICACIONES.pdf",
    }

    def __init__(
        self,
        llm: Any,
        max_archivos: int = 20,
    ):
        self.llm = llm
        self.max_archivos = max(
            1,
            int(max_archivos),
        )

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

                mensaje = (
                    respuesta.get(
                        "message"
                    )
                    or {}
                )

                if isinstance(
                    mensaje,
                    dict,
                ):

                    contenido = (
                        mensaje.get(
                            "content"
                        )
                    )

                    if contenido:
                        return str(
                            contenido
                        )

                contenido = (
                    respuesta.get(
                        "content"
                    )
                )

                if contenido:
                    return str(
                        contenido
                    )

        if hasattr(
            self.llm,
            "chat_stream",
        ):

            return "".join(
                str(fragmento)
                for fragmento
                in self.llm.chat_stream(
                    mensajes
                )
            )

        raise RuntimeError(
            "LLM incompatible: no expone chat ni chat_stream."
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
                "El LLM no devolvió un objeto JSON."
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
            ruta = ruta[2:]

        return ruta

    def _ruta_valida(
        self,
        ruta: str,
    ) -> bool:

        ruta = self._normalizar_ruta(
            ruta
        )

        if not ruta:
            return False

        if ruta.startswith("/"):
            return False

        if ":" in ruta:
            return False

        partes = Path(
            ruta
        ).parts

        if ".." in partes:
            return False

        if Path(
            ruta
        ).name in self.ARCHIVOS_PROTEGIDOS:
            return False

        extension = Path(
            ruta
        ).suffix.lower()

        return (
            extension
            in self.EXTENSIONES_PERMITIDAS
        )

    # =========================================================
    # VALIDACIÓN
    # =========================================================

    def _validar_contenido(
        self,
        ruta: str,
        contenido: str,
    ) -> tuple[bool, str | None]:

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
                f"{type(error).__name__}: {error}",
            )

        return (
            True,
            None,
        )

    # =========================================================
    # PROGRAMAR
    # =========================================================

    def programar(
        self,
        carpeta_proyecto: str | Path,
        especificaciones: dict,
    ) -> ResultadoProgramacionProyectoExterno:

        carpeta = Path(
            carpeta_proyecto
        ).resolve()

        if not carpeta.exists():

            return ResultadoProgramacionProyectoExterno(
                ok=False,
                carpeta=str(carpeta),
                error="carpeta_proyecto_no_existe",
            )

        system = """
Eres el programador autónomo de proyectos externos de ATENAS.

Debes convertir unas especificaciones ya definidas en una solución
funcional pequeña o mediana.

Puedes generar varios archivos y elegir la estructura técnica.

REGLAS:
- No ejecutes comandos.
- No instales paquetes.
- No uses rutas absolutas.
- No uses '..'.
- No generes binarios.
- No afirmes que probaste algo que no ejecutaste.
- Respeta la documentación y los requisitos recibidos.
- Usa la carpeta src/ para código cuando corresponda.
- Usa tests/ para pruebas.
- Puedes crear requirements.txt, package.json, pyproject.toml,
  archivos de configuración o documentación auxiliar.
- No sobrescribas proyecto.json, ESPECIFICACIONES.md ni
  ESPECIFICACIONES.pdf.

Devuelve SOLO JSON válido:

{
  "lenguaje_principal": "python",
  "resumen": "qué solución generaste",
  "completado": true,
  "archivos": [
    {
      "ruta": "src/main.py",
      "lenguaje": "python",
      "contenido": "..."
    },
    {
      "ruta": "tests/test_main.py",
      "lenguaje": "python",
      "contenido": "..."
    }
  ]
}

La solución debe ser coherente con las especificaciones.
""".strip()

        usuario = (
            "ESPECIFICACIONES DEL PROYECTO:\n"
            + json.dumps(
                especificaciones,
                ensure_ascii=False,
                indent=2,
            )
        )

        try:

            respuesta = self._preguntar([
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": usuario,
                },
            ])

            datos = self._extraer_json(
                respuesta
            )

        except Exception as error:

            return ResultadoProgramacionProyectoExterno(
                ok=False,
                carpeta=str(carpeta),
                error=(
                    f"{type(error).__name__}: {error}"
                ),
            )

        archivos_raw = datos.get(
            "archivos"
        )

        if (
            not isinstance(
                archivos_raw,
                list,
            )
            or not archivos_raw
        ):

            return ResultadoProgramacionProyectoExterno(
                ok=False,
                carpeta=str(carpeta),
                error="sin_archivos_generados",
            )

        resultados: list[
            ArchivoProyectoGenerado
        ] = []

        for item in archivos_raw[
            :self.max_archivos
        ]:

            if not isinstance(
                item,
                dict,
            ):
                continue

            ruta = self._normalizar_ruta(
                str(
                    item.get(
                        "ruta",
                        "",
                    )
                    or ""
                )
            )

            contenido = str(
                item.get(
                    "contenido",
                    "",
                )
                or ""
            )

            lenguaje = str(
                item.get(
                    "lenguaje",
                    "",
                )
                or ""
            ).strip().lower()

            if not self._ruta_valida(
                ruta
            ):

                resultados.append(
                    ArchivoProyectoGenerado(
                        ruta=ruta,
                        lenguaje=lenguaje,
                        valido=False,
                        error="ruta_no_permitida",
                    )
                )

                continue

            valido, error = (
                self._validar_contenido(
                    ruta,
                    contenido,
                )
            )

            if not valido:

                resultados.append(
                    ArchivoProyectoGenerado(
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
                    ArchivoProyectoGenerado(
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
                ArchivoProyectoGenerado(
                    ruta=ruta,
                    lenguaje=lenguaje,
                    valido=True,
                    error=None,
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

        manifest = (
            carpeta
            / "ATENAS_GENERACION.json"
        )

        manifest.write_text(
            json.dumps(
                {
                    "lenguaje_principal":
                        datos.get(
                            "lenguaje_principal"
                        ),

                    "resumen":
                        datos.get(
                            "resumen",
                            "",
                        ),

                    "completado":
                        completado,

                    "archivos": [
                        {
                            "ruta":
                                archivo.ruta,

                            "lenguaje":
                                archivo.lenguaje,

                            "valido":
                                archivo.valido,

                            "error":
                                archivo.error,
                        }
                        for archivo
                        in resultados
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return ResultadoProgramacionProyectoExterno(
            ok=bool(
                validos
            ),
            carpeta=str(
                carpeta
            ),
            lenguaje_principal=(
                str(
                    datos.get(
                        "lenguaje_principal",
                        "",
                    )
                    or ""
                )
            ),
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