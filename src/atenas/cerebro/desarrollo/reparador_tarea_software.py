from __future__ import annotations

import ast
import json
import re

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .planificador_sistema_software import TareaSoftware
from .validador_tarea_software import (
    ResultadoValidacionTarea,
    ValidadorTareaSoftware,
)


@dataclass
class IntentoReparacion:
    numero: int
    resumen: str
    archivos_modificados: list[str] = field(default_factory=list)
    validacion_ok: bool = False
    error: str | None = None


@dataclass
class ResultadoReparacionTarea:
    ok: bool
    reparada: bool
    tarea_id: str
    titulo: str
    intentos: list[IntentoReparacion] = field(default_factory=list)
    validacion_final: ResultadoValidacionTarea | None = None
    resumen: str = ""
    error: str | None = None


class ReparadorTareaSoftware:
    """
    Reparación incremental compatible con versiones anteriores y nuevas
    de ResultadoValidacionTarea.

    No presupone la existencia de:
        motor_pruebas
        pytest_disponible
        motor en ResultadoComandoValidacion

    Esto evita que una diferencia de versión entre el validador y el
    reparador rompa todo el ciclo de desarrollo.
    """

    EXTENSIONES_PERMITIDAS = {
        ".py", ".json", ".js", ".ts", ".jsx", ".tsx",
        ".html", ".css", ".md", ".txt", ".sql",
        ".yml", ".yaml", ".toml", ".ini",
        ".c", ".h", ".cpp", ".hpp", ".ino",
        ".java", ".rs", ".go", ".php",
    }

    def __init__(
        self,
        llm: Any,
        validador: ValidadorTareaSoftware,
        max_intentos: int = 3,
        max_archivos_por_intento: int = 8,
    ):
        self.llm = llm
        self.validador = validador
        self.max_intentos = max(1, int(max_intentos))
        self.max_archivos_por_intento = max(
            1,
            int(max_archivos_por_intento),
        )

    # =========================================================
    # COMPATIBILIDAD
    # =========================================================

    @staticmethod
    def _atributo(objeto: Any, nombre: str, defecto: Any = None) -> Any:
        """
        Lee atributos opcionales sin acoplar el reparador a una versión
        concreta de las dataclasses del validador.
        """
        return getattr(objeto, nombre, defecto)

    @classmethod
    def _serializar_comando(cls, comando: Any) -> dict:
        return {
            "returncode": cls._atributo(
                comando,
                "returncode",
                -1,
            ),
            "stdout": cls._atributo(
                comando,
                "stdout",
                "",
            ) or "",
            "stderr": cls._atributo(
                comando,
                "stderr",
                "",
            ) or "",
            "motor": cls._atributo(
                comando,
                "motor",
                "desconocido",
            ),
            "comando": cls._atributo(
                comando,
                "comando",
                [],
            ) or [],
        }

    @classmethod
    def _serializar_validacion(
        cls,
        validacion: ResultadoValidacionTarea,
    ) -> dict:
        comandos = cls._atributo(
            validacion,
            "comandos",
            [],
        ) or []

        return {
            "ok": bool(
                cls._atributo(
                    validacion,
                    "ok",
                    False,
                )
            ),
            "sintaxis_ok": bool(
                cls._atributo(
                    validacion,
                    "sintaxis_ok",
                    False,
                )
            ),
            "pruebas_ok": bool(
                cls._atributo(
                    validacion,
                    "pruebas_ok",
                    False,
                )
            ),
            "errores": list(
                cls._atributo(
                    validacion,
                    "errores",
                    [],
                ) or []
            ),
            "resumen": cls._atributo(
                validacion,
                "resumen",
                "",
            ) or "",
            "motor_pruebas": cls._atributo(
                validacion,
                "motor_pruebas",
                None,
            ),
            "pytest_disponible": cls._atributo(
                validacion,
                "pytest_disponible",
                None,
            ),
            "comandos": [
                cls._serializar_comando(comando)
                for comando in comandos
            ],
        }

    # =========================================================
    # LLM
    # =========================================================

    def _preguntar(self, mensajes: list[dict]) -> str:
        if hasattr(self.llm, "chat"):
            respuesta = self.llm.chat(mensajes)

            if isinstance(respuesta, str):
                return respuesta

            if isinstance(respuesta, dict):
                message = respuesta.get("message") or {}

                if isinstance(message, dict):
                    content = message.get("content")
                    if content:
                        return str(content)

                content = respuesta.get("content")
                if content:
                    return str(content)

        if hasattr(self.llm, "chat_stream"):
            return "".join(
                str(fragmento)
                for fragmento in self.llm.chat_stream(mensajes)
            )

        raise RuntimeError("LLM incompatible.")

    @staticmethod
    def _extraer_json(texto: str) -> dict:
        texto = (texto or "").strip()

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

            if inicio < 0 or fin <= inicio:
                raise ValueError("No se encontró JSON válido.")

            texto = texto[inicio:fin + 1]

        datos = json.loads(texto)

        if not isinstance(datos, dict):
            raise ValueError("Respuesta JSON inválida.")

        return datos

    # =========================================================
    # ARCHIVOS
    # =========================================================

    @staticmethod
    def _normalizar_ruta(ruta: str) -> str:
        ruta = (ruta or "").strip().replace("\\", "/")

        while ruta.startswith("./"):
            ruta = ruta[2:]

        return ruta

    def _ruta_permitida(self, ruta: str) -> bool:
        ruta = self._normalizar_ruta(ruta)

        if not ruta:
            return False

        if ruta.startswith("/"):
            return False

        if ":" in ruta:
            return False

        if ".." in Path(ruta).parts:
            return False

        return (
            Path(ruta).suffix.lower()
            in self.EXTENSIONES_PERMITIDAS
        )

    @staticmethod
    def _validar_contenido(
        ruta: str,
        contenido: str,
    ) -> tuple[bool, str | None]:
        extension = Path(ruta).suffix.lower()

        try:
            if extension == ".py":
                ast.parse(contenido)

            elif extension == ".json":
                json.loads(contenido)

            elif not contenido.strip():
                return False, "archivo_vacio"

        except Exception as error:
            return (
                False,
                f"{type(error).__name__}: {error}",
            )

        return True, None

    @staticmethod
    def _leer_archivos_relevantes(
        raiz: Path,
        limite: int = 25,
        max_chars: int = 120_000,
    ) -> dict[str, str]:
        extensiones = {
            ".py", ".json", ".js", ".ts", ".jsx", ".tsx",
            ".html", ".css", ".sql", ".md", ".toml",
            ".yml", ".yaml",
        }

        resultado: dict[str, str] = {}
        usados = 0

        for archivo in sorted(raiz.rglob("*")):
            if not archivo.is_file():
                continue

            if archivo.suffix.lower() not in extensiones:
                continue

            if len(resultado) >= limite:
                break

            try:
                relativo = str(
                    archivo.relative_to(raiz)
                ).replace("\\", "/")

                contenido = archivo.read_text(
                    encoding="utf-8"
                )
            except Exception:
                continue

            disponible = max_chars - usados

            if disponible <= 0:
                break

            if len(contenido) > disponible:
                contenido = contenido[:disponible]

            resultado[relativo] = contenido
            usados += len(contenido)

        return resultado

    # =========================================================
    # REPARACIÓN
    # =========================================================

    def reparar(
        self,
        carpeta_proyecto: str | Path,
        tarea: TareaSoftware,
        validacion_inicial: ResultadoValidacionTarea,
        ejecutar_pruebas: bool = True,
    ) -> ResultadoReparacionTarea:
        raiz = Path(carpeta_proyecto).resolve()

        if not raiz.exists():
            return ResultadoReparacionTarea(
                ok=False,
                reparada=False,
                tarea_id=tarea.id,
                titulo=tarea.titulo,
                error="carpeta_proyecto_no_existe",
            )

        validacion_actual = validacion_inicial
        intentos: list[IntentoReparacion] = []

        for numero in range(1, self.max_intentos + 1):
            archivos_actuales = self._leer_archivos_relevantes(
                raiz
            )

            system = """
Eres el reparador incremental de código de ATENAS.

Una tarea ya fue programada pero falló la validación real.

Corrige SOLO el problema demostrado por los errores, traceback,
pruebas fallidas y criterios de aceptación.

REGLAS:
- No reescribas innecesariamente el proyecto.
- No borres archivos.
- No ejecutes comandos.
- No instales dependencias.
- No uses rutas absolutas.
- No uses '..'.
- Modifica la menor cantidad posible de archivos.
- Devuelve el contenido COMPLETO de cada archivo modificado.

Devuelve SOLO JSON:

{
  "resumen": "qué corregiste y por qué",
  "archivos": [
    {
      "ruta": "src/archivo.py",
      "contenido": "contenido completo corregido"
    }
  ]
}
""".strip()

            entrada = {
                "tarea": {
                    "id": tarea.id,
                    "titulo": tarea.titulo,
                    "descripcion": tarea.descripcion,
                    "criterios_aceptacion": getattr(
                        tarea,
                        "criterios_aceptacion",
                        [],
                    ),
                    "lenguaje": getattr(
                        tarea,
                        "lenguaje",
                        None,
                    ),
                    "tecnologia": getattr(
                        tarea,
                        "tecnologia",
                        None,
                    ),
                },
                "validacion": self._serializar_validacion(
                    validacion_actual
                ),
                "archivos_actuales": archivos_actuales,
            }

            try:
                respuesta = self._preguntar(
                    [
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
                    ]
                )

                datos = self._extraer_json(
                    respuesta
                )

            except Exception as error:
                intentos.append(
                    IntentoReparacion(
                        numero=numero,
                        resumen=(
                            "No fue posible generar "
                            "una corrección."
                        ),
                        error=(
                            f"{type(error).__name__}: {error}"
                        ),
                    )
                )
                continue

            archivos_raw = datos.get("archivos")

            if not isinstance(archivos_raw, list):
                intentos.append(
                    IntentoReparacion(
                        numero=numero,
                        resumen=str(
                            datos.get("resumen", "")
                        ),
                        error="sin_archivos",
                    )
                )
                continue

            modificados: list[str] = []
            error_intento: str | None = None

            for item in archivos_raw[
                :self.max_archivos_por_intento
            ]:
                if not isinstance(item, dict):
                    continue

                ruta = self._normalizar_ruta(
                    str(
                        item.get("ruta", "")
                        or ""
                    )
                )

                contenido = str(
                    item.get("contenido", "")
                    or ""
                )

                if not self._ruta_permitida(ruta):
                    error_intento = (
                        f"Ruta no permitida: {ruta}"
                    )
                    continue

                valido, error = self._validar_contenido(
                    ruta,
                    contenido,
                )

                if not valido:
                    error_intento = (
                        f"{ruta}: {error}"
                    )
                    continue

                destino = (raiz / ruta).resolve()

                try:
                    destino.relative_to(raiz)
                except ValueError:
                    error_intento = (
                        f"Escape de carpeta: {ruta}"
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

                modificados.append(ruta)

            validacion_actual = self.validador.validar(
                carpeta_proyecto=raiz,
                ejecutar_pruebas=ejecutar_pruebas,
            )

            intento = IntentoReparacion(
                numero=numero,
                resumen=str(
                    datos.get("resumen", "")
                    or ""
                ),
                archivos_modificados=modificados,
                validacion_ok=bool(
                    getattr(
                        validacion_actual,
                        "ok",
                        False,
                    )
                ),
                error=error_intento,
            )

            intentos.append(intento)

            if getattr(
                validacion_actual,
                "ok",
                False,
            ):
                return ResultadoReparacionTarea(
                    ok=True,
                    reparada=True,
                    tarea_id=tarea.id,
                    titulo=tarea.titulo,
                    intentos=intentos,
                    validacion_final=validacion_actual,
                    resumen=(
                        intento.resumen
                        or (
                            "La tarea fue reparada y "
                            "validada correctamente."
                        )
                    ),
                )

        return ResultadoReparacionTarea(
            ok=False,
            reparada=False,
            tarea_id=tarea.id,
            titulo=tarea.titulo,
            intentos=intentos,
            validacion_final=validacion_actual,
            resumen=(
                "No fue posible reparar la tarea "
                "dentro del límite de intentos."
            ),
            error="max_intentos_agotados",
        )