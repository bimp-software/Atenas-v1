from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.atenas.cerebro.estado import (
    estado_atenas,
)

from .identidad import IdentidadAtenas


@dataclass
class EstadoAutoconcepto:
    """
    Fotografía técnica de cómo ATENAS
    entiende su propio sistema.
    """

    nombre: str
    version: str
    estado: str

    capacidades: dict[str, Any] = field(
        default_factory=dict
    )

    componentes: dict[str, bool] = field(
        default_factory=dict
    )

    limitaciones: list[str] = field(
        default_factory=list
    )

    actualizado_en: str = ""


class AutoconceptoAtenas:

    def __init__(
        self,
        identidad: IdentidadAtenas,
    ):
        self.identidad = identidad

        self._componentes: dict[str, bool] = {
            "llm": False,
            "memoria": False,
            "vector_store": False,
            "knowledge_graph": False,
            "internet": False,
            "investigacion": False,
            "voz_salida": False,
            "voz_entrada": False,
            "vision": False,
            "agente": False,
            "herramientas": False,
            "servidor_local": False,
            "robot": False,
            "autoprogramacion": False,
            "autorreparacion": False,
        }

        self._limitaciones: set[str] = set()

    # =========================================================
    # COMPONENTES
    # =========================================================

    def registrar_componente(
        self,
        nombre: str,
        disponible: bool = True,
    ) -> None:

        nombre = nombre.strip().lower()

        if not nombre:
            return

        self._componentes[
            nombre
        ] = bool(
            disponible
        )

    def desactivar_componente(
        self,
        nombre: str,
    ) -> None:

        self.registrar_componente(
            nombre,
            False,
        )

    def componente_disponible(
        self,
        nombre: str,
    ) -> bool:

        return bool(
            self._componentes.get(
                nombre.strip().lower(),
                False,
            )
        )

    # =========================================================
    # LIMITACIONES
    # =========================================================

    def registrar_limitacion(
        self,
        descripcion: str,
    ) -> None:

        descripcion = (
            descripcion
            or ""
        ).strip()

        if descripcion:
            self._limitaciones.add(
                descripcion
            )

    def eliminar_limitacion(
        self,
        descripcion: str,
    ) -> None:

        self._limitaciones.discard(
            descripcion
        )

    # =========================================================
    # CAPACIDADES DEL ESTADO
    # =========================================================

    def _extraer_capacidades_estado(
        self,
    ) -> dict[str, Any]:

        capacidades = (
            estado_atenas.capacidades
        )

        resultado = {}

        # No dependemos de conocer todos los campos
        # definidos actualmente en CapacidadesAtenas.
        if hasattr(
            capacidades,
            "__dict__",
        ):

            for nombre, valor in (
                vars(capacidades).items()
            ):

                resultado[
                    nombre
                ] = valor

        return resultado

    # =========================================================
    # SINCRONIZAR
    # =========================================================

    def actualizar_desde_estado(
        self,
    ) -> None:

        capacidades = (
            self._extraer_capacidades_estado()
        )

        mapeo = {
            "voz_salida":
                "voz_salida",

            "voz_entrada":
                "voz_entrada",

            "memoria_persistente":
                "memoria",

            "vision":
                "vision",

            "internet":
                "internet",

            "robot":
                "robot",
        }

        for capacidad, componente in (
            mapeo.items()
        ):

            if capacidad not in capacidades:
                continue

            self._componentes[
                componente
            ] = bool(
                capacidades[
                    capacidad
                ]
            )

    # =========================================================
    # ESTADO COMPLETO
    # =========================================================

    def obtener_estado(
        self,
    ) -> EstadoAutoconcepto:

        self.actualizar_desde_estado()

        return EstadoAutoconcepto(
            nombre=estado_atenas.nombre,
            version=estado_atenas.version,
            estado=estado_atenas.estado,

            capacidades=(
                self._extraer_capacidades_estado()
            ),

            componentes=dict(
                self._componentes
            ),

            limitaciones=sorted(
                self._limitaciones
            ),

            actualizado_en=(
                datetime.now()
                .astimezone()
                .isoformat()
            ),
        )

    # =========================================================
    # CAPACIDADES ACTIVAS
    # =========================================================

    def obtener_capacidades(
        self,
    ) -> list[str]:

        estado = self.obtener_estado()

        return sorted(
            nombre
            for nombre, disponible
            in estado.componentes.items()
            if disponible
        )

    # =========================================================
    # LIMITACIONES ACTUALES
    # =========================================================

    def obtener_limitaciones(
        self,
    ) -> list[str]:

        estado = self.obtener_estado()

        limitaciones = list(
            estado.limitaciones
        )

        for nombre, disponible in (
            estado.componentes.items()
        ):

            if not disponible:

                limitaciones.append(
                    f"Componente '{nombre}' "
                    "no disponible actualmente."
                )

        return sorted(
            set(limitaciones)
        )

    # =========================================================
    # CONTEXTO PARA QWEN
    # =========================================================

    def contexto_para_llm(
        self,
    ) -> str:

        estado = self.obtener_estado()

        disponibles = [
            nombre
            for nombre, disponible
            in estado.componentes.items()
            if disponible
        ]

        no_disponibles = [
            nombre
            for nombre, disponible
            in estado.componentes.items()
            if not disponible
        ]

        texto_disponibles = (
            "\n".join(
                f"- {nombre}"
                for nombre in disponibles
            )
            if disponibles
            else "- ninguno registrado"
        )

        texto_no_disponibles = (
            "\n".join(
                f"- {nombre}"
                for nombre in no_disponibles
            )
            if no_disponibles
            else "- ninguno"
        )

        limitaciones = (
            "\n".join(
                f"- {limitacion}"
                for limitacion
                in estado.limitaciones
            )
            if estado.limitaciones
            else "- ninguna limitación adicional registrada"
        )

        return f"""
            AUTOCONCEPTO TÉCNICO ACTUAL:

            Nombre: {estado.nombre}
            Versión: {estado.version}
            Estado: {estado.estado}

            COMPONENTES DISPONIBLES:

            {texto_disponibles}

            COMPONENTES TODAVÍA NO DISPONIBLES:

            {texto_no_disponibles}

            LIMITACIONES REGISTRADAS:

            {limitaciones}

            IMPORTANTE:

            Este bloque representa el estado real conocido
            por ATENAS en este momento.

            No conviertas componentes no disponibles
            en capacidades imaginarias.
            """.strip()


autoconcepto_atenas = AutoconceptoAtenas(
    identidad=IdentidadAtenas
)