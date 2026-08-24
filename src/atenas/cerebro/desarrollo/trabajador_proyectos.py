from __future__ import annotations

import json
import re

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .proyectos_internos import (
    EstadoObjetivoProyecto,
    GestorProyectosInternos,
    ObjetivoProyecto,
    ProyectoInterno,
)


@dataclass
class ResultadoTrabajoProyecto:
    ok: bool

    proyecto_id: str | None = None
    objetivo_id: str | None = None

    proyecto: str | None = None
    objetivo: str | None = None

    completado: bool = False

    resumen: str = ""
    entregable: str = ""

    archivo_resultado: str | None = None

    siguiente_recomendacion: str = ""

    error: str | None = None


class TrabajadorProyectosAutonomo:
    """
    Ejecuta trabajo intelectual/técnico de bajo riesgo para los
    proyectos internos de ATENAS.

    Esta primera versión puede avanzar autónomamente objetivos de:
    - análisis;
    - diseño;
    - planificación técnica;
    - definición de interfaces;
    - preparación de estrategias de pruebas;
    - documentación técnica.

    NO modifica código productivo.

    Los resultados se guardan en data/proyectos_internos para que
    ATENAS pueda retomarlos tras reiniciar y para que, más adelante,
    la interfaz web pueda mostrarlos.
    """

    def __init__(
        self,
        llm: Any,
        gestor: GestorProyectosInternos,
        desarrollo,
        raiz_resultados: str | Path,
    ):
        self.llm = llm
        self.gestor = gestor
        self.desarrollo = desarrollo

        self.raiz_resultados = Path(
            raiz_resultados
        ).resolve()

        self.raiz_resultados.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _ahora() -> str:

        return (
            datetime.now(
                timezone.utc
            )
            .isoformat()
        )

    @staticmethod
    def _slug(
        texto: str,
    ) -> str:

        texto = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            texto.strip(),
        )

        return (
            texto.strip("_")
            or "trabajo"
        )[:80]

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

                    content = (
                        message.get(
                            "content"
                        )
                    )

                    if content:
                        return str(
                            content
                        )

                content = (
                    respuesta.get(
                        "content"
                    )
                )

                if content:
                    return str(
                        content
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
            "El cliente LLM no expone chat "
            "ni chat_stream."
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
                "La respuesta no es un objeto JSON."
            )

        return datos

    # =========================================================
    # CONTEXTO DEL PROYECTO REAL
    # =========================================================

    def _contexto_codigo(
        self,
    ) -> str:

        try:

            return (
                self.desarrollo
                .mapa
                .contexto_para_llm()
            )

        except Exception:

            try:

                return (
                    self.desarrollo
                    .contexto_para_llm(
                        incluir_automejora=False
                    )
                )

            except Exception:

                return (
                    "No fue posible generar "
                    "el mapa técnico del proyecto."
                )

    # =========================================================
    # GUARDAR ENTREGABLE
    # =========================================================

    def _guardar_resultado(
        self,
        proyecto: ProyectoInterno,
        objetivo: ObjetivoProyecto,
        datos: dict,
    ) -> Path:

        carpeta = (
            self.raiz_resultados
            / proyecto.id
        )

        carpeta.mkdir(
            parents=True,
            exist_ok=True,
        )

        nombre = (
            f"{objetivo.orden:03d}_"
            f"{self._slug(objetivo.descripcion)}.json"
        )

        ruta = (
            carpeta
            / nombre
        )

        contenido = {
            "proyecto_id":
                proyecto.id,

            "proyecto":
                proyecto.nombre,

            "objetivo_id":
                objetivo.id,

            "objetivo":
                objetivo.descripcion,

            "generado_en":
                self._ahora(),

            "resultado":
                datos,
        }

        ruta.write_text(
            json.dumps(
                contenido,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return ruta

    # =========================================================
    # EJECUTAR OBJETIVO
    # =========================================================

    def ejecutar_objetivo(
        self,
        proyecto: ProyectoInterno,
        objetivo: ObjetivoProyecto,
    ) -> ResultadoTrabajoProyecto:

        self.gestor.iniciar_objetivo(
            objetivo.id
        )

        contexto_codigo = (
            self._contexto_codigo()
        )

        system = """
Eres el trabajador técnico autónomo de ATENAS.

Debes avanzar UN objetivo de un proyecto interno.

En esta fase puedes realizar:
- análisis de arquitectura;
- diseño técnico;
- planificación;
- definición de interfaces;
- propuesta de componentes;
- estrategia de pruebas;
- documentación técnica;
- identificación de riesgos y dependencias.

NO puedes afirmar que modificaste código.
NO puedes afirmar que ejecutaste hardware.
NO puedes inventar resultados de pruebas.
NO puedes marcar como completado un objetivo que requiera una
implementación real todavía no realizada.

Devuelve SOLO JSON válido:

{
  "completado": true,
  "resumen": "qué trabajo realizaste",
  "entregable": "resultado técnico detallado",
  "siguiente_recomendacion": "qué conviene hacer después"
}
""".strip()

        usuario = f"""
PROYECTO:
{proyecto.nombre}

DESCRIPCIÓN:
{proyecto.descripcion}

OBJETIVO ACTUAL:
{objetivo.descripcion}

PRIORIDAD DEL OBJETIVO:
{objetivo.prioridad:.2f}

CONTEXTO REAL DEL CÓDIGO DE ATENAS:
{contexto_codigo}

Trabaja únicamente en este objetivo.
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

            return ResultadoTrabajoProyecto(
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
                resumen=(
                    "No fue posible completar "
                    "el trabajo técnico."
                ),
            )

        completado = bool(
            datos.get(
                "completado",
                False,
            )
        )

        resumen = str(
            datos.get(
                "resumen",
                "",
            )
            or ""
        ).strip()

        entregable = str(
            datos.get(
                "entregable",
                "",
            )
            or ""
        ).strip()

        siguiente = str(
            datos.get(
                "siguiente_recomendacion",
                "",
            )
            or ""
        ).strip()

        try:

            ruta = (
                self._guardar_resultado(
                    proyecto=proyecto,
                    objetivo=objetivo,
                    datos={
                        "completado":
                            completado,

                        "resumen":
                            resumen,

                        "entregable":
                            entregable,

                        "siguiente_recomendacion":
                            siguiente,
                    },
                )
            )

        except Exception as error:

            return ResultadoTrabajoProyecto(
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
                resumen=(
                    "El trabajo fue generado, "
                    "pero no pudo persistirse."
                ),
            )

        if completado:

            self.gestor.completar_objetivo(
                objetivo.id
            )

        self.gestor.registrar_trabajo(
            proyecto.id,
            (
                f"{objetivo.descripcion} :: "
                f"{resumen}"
            )[:2000],
        )

        return ResultadoTrabajoProyecto(
            ok=True,
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
            completado=(
                completado
            ),
            resumen=(
                resumen
            ),
            entregable=(
                entregable
            ),
            archivo_resultado=(
                str(
                    ruta
                )
            ),
            siguiente_recomendacion=(
                siguiente
            ),
        )

    # =========================================================
    # ELEGIR Y TRABAJAR SOLO
    # =========================================================

    def ejecutar_siguiente(
        self,
        proyecto_id: str | None = None,
    ) -> ResultadoTrabajoProyecto:

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

            return ResultadoTrabajoProyecto(
                ok=True,
                resumen=(
                    "No existen proyectos "
                    "internos activos."
                ),
            )

        objetivo = (
            self.gestor
            .siguiente_objetivo(
                proyecto.id
            )
        )

        if objetivo is None:

            return ResultadoTrabajoProyecto(
                ok=True,
                proyecto_id=(
                    proyecto.id
                ),
                proyecto=(
                    proyecto.nombre
                ),
                resumen=(
                    "El proyecto no tiene "
                    "objetivos ejecutables."
                ),
            )

        return (
            self.ejecutar_objetivo(
                proyecto=proyecto,
                objetivo=objetivo,
            )
        )