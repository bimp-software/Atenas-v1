from __future__ import annotations

import ast
import json
import re

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .proyectos_internos import (
    GestorProyectosInternos,
    ObjetivoProyecto,
    ProyectoInterno,
)


@dataclass
class ArchivoSolucion:
    ruta: str
    lenguaje: str
    contenido: str
    valido: bool = True
    error: str | None = None


@dataclass
class ResultadoProgramacionObjetivo:
    ok: bool

    proyecto_id: str | None = None
    objetivo_id: str | None = None

    proyecto: str | None = None
    objetivo: str | None = None

    lenguaje_principal: str | None = None

    archivos: list[ArchivoSolucion] = field(
        default_factory=list
    )

    carpeta_solucion: str | None = None

    completado: bool = False

    resumen: str = ""

    error: str | None = None


class ProgramadorObjetivosAutonomo:
    """
    Convierte objetivos técnicos pequeños en soluciones de código.

    Primera etapa deliberadamente segura:

    - puede crear soluciones pequeñas en varios lenguajes;
    - puede crear múltiples archivos;
    - solo escribe dentro de data/soluciones_objetivos;
    - no ejecuta shell;
    - no instala paquetes;
    - no toca código productivo de ATENAS;
    - valida rutas;
    - hace validaciones estáticas básicas;
    - persiste los archivos para retomarlos después.

    Más adelante este módulo podrá entregar su solución al sistema
    de sandbox/parches para integración real.
    """

    EXTENSIONES_PERMITIDAS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
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
    }

    def __init__(
        self,
        llm: Any,
        gestor: GestorProyectosInternos,
        desarrollo,
        raiz_soluciones: str | Path,
    ):
        self.llm = llm
        self.gestor = gestor
        self.desarrollo = desarrollo

        self.raiz_soluciones = Path(
            raiz_soluciones
        ).resolve()

        self.raiz_soluciones.mkdir(
            parents=True,
            exist_ok=True,
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

            respuesta = (
                self.llm.chat(
                    mensajes
                )
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
    # CONTEXTO
    # =========================================================

    def _contexto_proyecto(
        self,
    ) -> str:

        try:

            return (
                self.desarrollo
                .mapa
                .contexto_para_llm()
            )

        except Exception:

            return (
                "Mapa del proyecto no disponible."
            )

    # =========================================================
    # SEGURIDAD DE RUTAS
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

        extension = Path(
            ruta
        ).suffix.lower()

        return (
            extension
            in self.EXTENSIONES_PERMITIDAS
        )

    # =========================================================
    # VALIDACIÓN ESTÁTICA
    # =========================================================

    def _validar_archivo(
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

            elif extension in {
                ".js",
                ".ts",
                ".html",
                ".css",
                ".md",
                ".txt",
                ".c",
                ".h",
                ".cpp",
                ".hpp",
                ".ino",
                ".java",
                ".rs",
                ".go",
                ".php",
                ".sql",
            }:

                if not contenido.strip():

                    return (
                        False,
                        "archivo_vacio",
                    )

            else:

                return (
                    False,
                    "extension_no_permitida",
                )

        except Exception as error:

            return (
                False,
                f"{type(error).__name__}: "
                f"{error}",
            )

        return (
            True,
            None,
        )

    # =========================================================
    # CARPETA DE SOLUCIÓN
    # =========================================================

    def _carpeta_objetivo(
        self,
        proyecto: ProyectoInterno,
        objetivo: ObjetivoProyecto,
    ) -> Path:

        carpeta = (
            self.raiz_soluciones
            / proyecto.id
            / objetivo.id
        )

        carpeta.mkdir(
            parents=True,
            exist_ok=True,
        )

        return carpeta

    # =========================================================
    # GENERAR
    # =========================================================

    def programar_objetivo(
        self,
        proyecto: ProyectoInterno,
        objetivo: ObjetivoProyecto,
    ) -> ResultadoProgramacionObjetivo:

        contexto = (
            self._contexto_proyecto()
        )

        system = """
Eres el programador autónomo de soluciones pequeñas de ATENAS.

Debes resolver UN objetivo técnico creando una solución pequeña,
clara y verificable.

Puedes generar:
- Python
- JavaScript
- TypeScript
- HTML/CSS
- JSON
- C/C++
- Arduino
- Java
- Rust
- Go
- PHP
- SQL
- documentación Markdown

No ejecutes comandos.
No instales paquetes.
No inventes que ejecutaste pruebas.
No modifiques directamente el código real de ATENAS.
No uses rutas absolutas.
No uses ".." en rutas.
No generes binarios.

Devuelve SOLO JSON:

{
  "lenguaje_principal": "python",
  "resumen": "...",
  "completado": true,
  "archivos": [
    {
      "ruta": "main.py",
      "lenguaje": "python",
      "contenido": "..."
    }
  ]
}

Máximo 12 archivos.
La solución debe ser pequeña y autocontenida.
""".strip()

        usuario = f"""
PROYECTO INTERNO:
{proyecto.nombre}

DESCRIPCIÓN:
{proyecto.descripcion}

OBJETIVO:
{objetivo.descripcion}

CONTEXTO REAL DEL REPOSITORIO:
{contexto}

Genera una solución pequeña para este objetivo.
""".strip()

        try:

            respuesta = (
                self._preguntar([
                    {
                        "role": "system",
                        "content": system,
                    },
                    {
                        "role": "user",
                        "content": usuario,
                    },
                ])
            )

            datos = (
                self._extraer_json(
                    respuesta
                )
            )

        except Exception as error:

            return ResultadoProgramacionObjetivo(
                ok=False,
                proyecto_id=(
                    proyecto.id
                ),
                objetivo_id=(
                    objetivo.id
                ),
                proyecto=(
                    proyecto.nombre
                ),
                objetivo=(
                    objetivo.descripcion
                ),
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

            return ResultadoProgramacionObjetivo(
                ok=False,
                proyecto_id=(
                    proyecto.id
                ),
                objetivo_id=(
                    objetivo.id
                ),
                proyecto=(
                    proyecto.nombre
                ),
                objetivo=(
                    objetivo.descripcion
                ),
                error="sin_archivos",
            )

        carpeta = (
            self._carpeta_objetivo(
                proyecto,
                objetivo,
            )
        )

        archivos: list[
            ArchivoSolucion
        ] = []

        for item in archivos_raw[
            :12
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

            if not self._ruta_permitida(
                ruta
            ):

                archivos.append(
                    ArchivoSolucion(
                        ruta=ruta,
                        lenguaje=lenguaje,
                        contenido=contenido,
                        valido=False,
                        error=(
                            "ruta_no_permitida"
                        ),
                    )
                )

                continue

            valido, error = (
                self._validar_archivo(
                    ruta,
                    contenido,
                )
            )

            archivo = ArchivoSolucion(
                ruta=ruta,
                lenguaje=lenguaje,
                contenido=contenido,
                valido=valido,
                error=error,
            )

            archivos.append(
                archivo
            )

            if not valido:
                continue

            destino = (
                carpeta
                / ruta
            ).resolve()

            try:

                destino.relative_to(
                    carpeta.resolve()
                )

            except ValueError:

                archivo.valido = False
                archivo.error = (
                    "escape_de_carpeta"
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

        validos = [
            archivo
            for archivo
            in archivos
            if archivo.valido
        ]

        invalidos = [
            archivo
            for archivo
            in archivos
            if not archivo.valido
        ]

        completado_llm = bool(
            datos.get(
                "completado",
                False,
            )
        )

        completado = bool(
            completado_llm
            and validos
            and not invalidos
        )

        resumen = str(
            datos.get(
                "resumen",
                "",
            )
            or ""
        ).strip()

        if completado:

            self.gestor.completar_objetivo(
                objetivo.id
            )

        else:

            self.gestor.iniciar_objetivo(
                objetivo.id
            )

        self.gestor.registrar_trabajo(
            proyecto.id,
            (
                f"Solución pequeña para "
                f"{objetivo.descripcion}: "
                f"{resumen}"
            )[:2000],
        )

        manifest = {
            "proyecto_id":
                proyecto.id,

            "objetivo_id":
                objetivo.id,

            "lenguaje_principal":
                datos.get(
                    "lenguaje_principal"
                ),

            "resumen":
                resumen,

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
                in archivos
            ],
        }

        (
            carpeta
            / "manifest.json"
        ).write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return ResultadoProgramacionObjetivo(
            ok=bool(
                validos
            ),
            proyecto_id=(
                proyecto.id
            ),
            objetivo_id=(
                objetivo.id
            ),
            proyecto=(
                proyecto.nombre
            ),
            objetivo=(
                objetivo.descripcion
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
            archivos=archivos,
            carpeta_solucion=(
                str(
                    carpeta
                )
            ),
            completado=(
                completado
            ),
            resumen=(
                resumen
            ),
            error=(
                None
                if validos
                else "ningun_archivo_valido"
            ),
        )

    # =========================================================
    # ELEGIR PROYECTO / OBJETIVO
    # =========================================================

    def ejecutar_siguiente(
        self,
        proyecto_id: str | None = None,
    ) -> ResultadoProgramacionObjetivo:

        if proyecto_id:

            proyecto = (
                self.gestor
                .obtener_proyecto(
                    proyecto_id
                )
            )

        else:

            proyecto = (
                self.gestor
                .proyecto_prioritario()
            )

        if proyecto is None:

            return ResultadoProgramacionObjetivo(
                ok=True,
                resumen=(
                    "No hay proyectos activos."
                ),
            )

        objetivo = (
            self.gestor
            .siguiente_objetivo(
                proyecto.id
            )
        )

        if objetivo is None:

            return ResultadoProgramacionObjetivo(
                ok=True,
                proyecto_id=(
                    proyecto.id
                ),
                proyecto=(
                    proyecto.nombre
                ),
                resumen=(
                    "No hay objetivos "
                    "ejecutables."
                ),
            )

        return (
            self.programar_objetivo(
                proyecto=proyecto,
                objetivo=objetivo,
            )
        )