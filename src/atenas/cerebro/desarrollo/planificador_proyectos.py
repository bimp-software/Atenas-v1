from __future__ import annotations

import json
import re

from dataclasses import dataclass
from typing import Any

from .proyectos_internos import (
    GestorProyectosInternos,
    ProyectoInterno,
)


@dataclass
class ResultadoPlanificacionProyecto:
    ok: bool

    proyecto: ProyectoInterno | None = None

    mensaje: str = ""

    error: str | None = None


class PlanificadorProyectosInternos:
    """
    Usa el LLM para convertir una meta de medio plazo en un
    ProyectoInterno con objetivos ordenados y dependencias.

    No ejecuta el proyecto.
    Solo lo descompone y lo persiste.
    """

    def __init__(
        self,
        llm: Any,
        gestor: GestorProyectosInternos,
    ):
        self.llm = llm
        self.gestor = gestor

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
                    "No se encontró JSON."
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
                "Respuesta inválida."
            )

        return datos

    # =========================================================
    # PLANIFICAR
    # =========================================================

    def crear_desde_meta(
        self,
        nombre: str,
        descripcion: str,
        prioridad: float = 0.5,
        origen: str = "atenas",
        autonomia: bool = True,
        requiere_confirmacion: bool = False,
    ) -> ResultadoPlanificacionProyecto:

        system = """
Eres el planificador interno de ingeniería de ATENAS.

Convierte una meta de desarrollo en objetivos concretos,
pequeños, verificables y ordenados.

No escribas código todavía.
No ejecutes herramientas.
No inventes capacidades inexistentes.

Devuelve SOLO JSON válido:

{
  "objetivos": [
    {
      "descripcion": "...",
      "prioridad": 0.8,
      "depende_de_indices": []
    }
  ]
}

Reglas:
- 2 a 8 objetivos.
- Cada objetivo debe poder verificarse.
- Usa dependencias solo cuando sean necesarias.
- Evita objetivos vagos.
""".strip()

        usuario = f"""
PROYECTO:
{nombre}

DESCRIPCIÓN:
{descripcion}

Divide este proyecto en objetivos técnicos.
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

            return ResultadoPlanificacionProyecto(
                ok=False,
                mensaje=(
                    "No fue posible planificar "
                    "el proyecto."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        objetivos = (
            datos.get(
                "objetivos"
            )
        )

        if (
            not isinstance(
                objetivos,
                list,
            )
            or not objetivos
        ):

            return ResultadoPlanificacionProyecto(
                ok=False,
                mensaje=(
                    "El LLM no generó "
                    "objetivos válidos."
                ),
                error="objetivos_invalidos",
            )

        proyecto = (
            self.gestor
            .crear_proyecto(
                nombre=nombre,
                descripcion=descripcion,
                origen=origen,
                prioridad=prioridad,
                autonomia=autonomia,
                requiere_confirmacion=(
                    requiere_confirmacion
                ),
                activar=True,
            )
        )

        ids_creados: list[str] = []

        for indice, item in enumerate(
            objetivos[
                :8
            ]
        ):

            if not isinstance(
                item,
                dict,
            ):

                continue

            descripcion_obj = str(
                item.get(
                    "descripcion",
                    "",
                )
                or ""
            ).strip()

            if not descripcion_obj:
                continue

            dependencias_indices = (
                item.get(
                    "depende_de_indices",
                    [],
                )
                or []
            )

            dependencias_ids = []

            for dep in dependencias_indices:

                try:

                    dep_int = int(
                        dep
                    )

                except Exception:
                    continue

                if (
                    0
                    <= dep_int
                    < len(
                        ids_creados
                    )
                ):

                    dependencias_ids.append(
                        ids_creados[
                            dep_int
                        ]
                    )

            objetivo = (
                self.gestor
                .agregar_objetivo(
                    proyecto_id=(
                        proyecto.id
                    ),
                    descripcion=(
                        descripcion_obj
                    ),
                    prioridad=float(
                        item.get(
                            "prioridad",
                            0.5,
                        )
                        or 0.5
                    ),
                    orden=indice,
                    depende_de=(
                        dependencias_ids
                    ),
                )
            )

            ids_creados.append(
                objetivo.id
            )

        proyecto = (
            self.gestor
            .obtener_proyecto(
                proyecto.id
            )
        )

        return ResultadoPlanificacionProyecto(
            ok=True,
            proyecto=proyecto,
            mensaje=(
                "Proyecto interno creado "
                "y descompuesto en objetivos."
            ),
        )