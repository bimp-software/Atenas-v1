from __future__ import annotations

import json

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ContextoOperativo:
    actualizado_en: str

    proyecto_actual_id: str | None = None
    ruta_proyecto_actual: str | None = None
    nombre_proyecto_actual: str | None = None

    cliente_actual: str | None = None

    tipo_solucion: str | None = None
    lenguaje: str | None = None
    framework: str | None = None
    base_datos: str | None = None

    ventana_activa: str | None = None

    aplicaciones_relacionadas: list[str] = field(
        default_factory=list
    )

    archivos_relevantes: list[str] = field(
        default_factory=list
    )

    artefactos: list[str] = field(
        default_factory=list
    )

    ultima_tarea_id: str | None = None
    ultimo_proyecto_id: str | None = None

    ultimo_error: str | None = None

    decisiones_recientes: list[dict[str, Any]] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class GestorContextoOperativo:
    """
    Memoria de trabajo persistente del agente.

    Unifica contexto usado por:
    - desarrollo de software;
    - tareas de escritorio;
    - planificación;
    - replanificación;
    - percepción del computador;
    - futura interfaz web.

    No reemplaza memoria episódica/semántica. Su propósito es mantener
    el contexto operacional ACTUAL.
    """

    MAX_DECISIONES = 50
    MAX_ARCHIVOS = 200
    MAX_ARTEFACTOS = 200
    MAX_APLICACIONES = 50

    def __init__(
        self,
        ruta: str | Path = (
            "data/agente/contexto_operativo/contexto.json"
        ),
    ):
        self.ruta = Path(
            ruta
        ).expanduser().resolve()

        self.ruta.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not self.ruta.exists():

            self.guardar(
                ContextoOperativo(
                    actualizado_en=self._ahora()
                )
            )

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _ahora(
    ) -> str:

        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _unicos(
        valores: list[str],
        limite: int,
    ) -> list[str]:

        salida = []

        vistos = set()

        for valor in valores:

            texto = str(
                valor
            ).strip()

            if (
                not texto
                or texto in vistos
            ):
                continue

            vistos.add(
                texto
            )

            salida.append(
                texto
            )

        return salida[
            -max(
                1,
                int(
                    limite
                ),
            ):
        ]

    # =========================================================
    # SERIALIZACIÓN
    # =========================================================

    def guardar(
        self,
        contexto: ContextoOperativo,
    ) -> None:

        contexto.actualizado_en = (
            self._ahora()
        )

        datos = {
            "actualizado_en":
                contexto.actualizado_en,

            "proyecto_actual_id":
                contexto.proyecto_actual_id,

            "ruta_proyecto_actual":
                contexto.ruta_proyecto_actual,

            "nombre_proyecto_actual":
                contexto.nombre_proyecto_actual,

            "cliente_actual":
                contexto.cliente_actual,

            "tipo_solucion":
                contexto.tipo_solucion,

            "lenguaje":
                contexto.lenguaje,

            "framework":
                contexto.framework,

            "base_datos":
                contexto.base_datos,

            "ventana_activa":
                contexto.ventana_activa,

            "aplicaciones_relacionadas":
                self._unicos(
                    contexto.aplicaciones_relacionadas,
                    self.MAX_APLICACIONES,
                ),

            "archivos_relevantes":
                self._unicos(
                    contexto.archivos_relevantes,
                    self.MAX_ARCHIVOS,
                ),

            "artefactos":
                self._unicos(
                    contexto.artefactos,
                    self.MAX_ARTEFACTOS,
                ),

            "ultima_tarea_id":
                contexto.ultima_tarea_id,

            "ultimo_proyecto_id":
                contexto.ultimo_proyecto_id,

            "ultimo_error":
                contexto.ultimo_error,

            "decisiones_recientes":
                list(
                    contexto.decisiones_recientes
                )[
                    -self.MAX_DECISIONES:
                ],

            "metadata":
                contexto.metadata,
        }

        temporal = (
            self.ruta
            .with_suffix(
                ".tmp"
            )
        )

        temporal.write_text(
            json.dumps(
                datos,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        temporal.replace(
            self.ruta
        )

    def cargar(
        self,
    ) -> ContextoOperativo:

        try:

            datos = json.loads(
                self.ruta.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:

            datos = {}

        return ContextoOperativo(
            actualizado_en=str(
                datos.get(
                    "actualizado_en",
                    self._ahora(),
                )
            ),
            proyecto_actual_id=(
                datos.get(
                    "proyecto_actual_id"
                )
            ),
            ruta_proyecto_actual=(
                datos.get(
                    "ruta_proyecto_actual"
                )
            ),
            nombre_proyecto_actual=(
                datos.get(
                    "nombre_proyecto_actual"
                )
            ),
            cliente_actual=(
                datos.get(
                    "cliente_actual"
                )
            ),
            tipo_solucion=(
                datos.get(
                    "tipo_solucion"
                )
            ),
            lenguaje=(
                datos.get(
                    "lenguaje"
                )
            ),
            framework=(
                datos.get(
                    "framework"
                )
            ),
            base_datos=(
                datos.get(
                    "base_datos"
                )
            ),
            ventana_activa=(
                datos.get(
                    "ventana_activa"
                )
            ),
            aplicaciones_relacionadas=list(
                datos.get(
                    "aplicaciones_relacionadas",
                    []
                )
                or []
            ),
            archivos_relevantes=list(
                datos.get(
                    "archivos_relevantes",
                    []
                )
                or []
            ),
            artefactos=list(
                datos.get(
                    "artefactos",
                    []
                )
                or []
            ),
            ultima_tarea_id=(
                datos.get(
                    "ultima_tarea_id"
                )
            ),
            ultimo_proyecto_id=(
                datos.get(
                    "ultimo_proyecto_id"
                )
            ),
            ultimo_error=(
                datos.get(
                    "ultimo_error"
                )
            ),
            decisiones_recientes=list(
                datos.get(
                    "decisiones_recientes",
                    []
                )
                or []
            ),
            metadata=(
                datos.get(
                    "metadata",
                    {}
                )
                or {}
            ),
        )

    # =========================================================
    # ACTUALIZACIONES
    # =========================================================

    def actualizar(
        self,
        **cambios: Any,
    ) -> ContextoOperativo:

        contexto = self.cargar()

        campos = {
            "proyecto_actual_id",
            "ruta_proyecto_actual",
            "nombre_proyecto_actual",
            "cliente_actual",
            "tipo_solucion",
            "lenguaje",
            "framework",
            "base_datos",
            "ventana_activa",
            "ultima_tarea_id",
            "ultimo_proyecto_id",
            "ultimo_error",
        }

        for clave in campos:

            if clave in cambios:

                setattr(
                    contexto,
                    clave,
                    cambios[
                        clave
                    ],
                )

        if "metadata" in cambios:

            contexto.metadata.update(
                cambios.get(
                    "metadata",
                    {}
                )
                or {}
            )

        self.guardar(
            contexto
        )

        return contexto

    def registrar_aplicacion(
        self,
        nombre: str,
    ) -> ContextoOperativo:

        contexto = self.cargar()

        contexto.aplicaciones_relacionadas.append(
            nombre
        )

        self.guardar(
            contexto
        )

        return contexto

    def registrar_archivo(
        self,
        ruta: str,
    ) -> ContextoOperativo:

        contexto = self.cargar()

        contexto.archivos_relevantes.append(
            str(
                ruta
            )
        )

        self.guardar(
            contexto
        )

        return contexto

    def registrar_artefacto(
        self,
        ruta: str,
    ) -> ContextoOperativo:

        contexto = self.cargar()

        contexto.artefactos.append(
            str(
                ruta
            )
        )

        self.guardar(
            contexto
        )

        return contexto

    def registrar_error(
        self,
        error: str | None,
    ) -> ContextoOperativo:

        return self.actualizar(
            ultimo_error=(
                str(
                    error
                )
                if error
                else None
            )
        )

    def registrar_decision(
        self,
        tipo: str,
        motivo: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContextoOperativo:

        contexto = self.cargar()

        contexto.decisiones_recientes.append({
            "fecha":
                self._ahora(),

            "tipo":
                str(
                    tipo
                ),

            "motivo":
                str(
                    motivo
                ),

            "metadata":
                metadata
                or {},
        })

        self.guardar(
            contexto
        )

        return contexto

    # =========================================================
    # CONTEXTO PARA OTROS MÓDULOS
    # =========================================================

    def para_planificacion(
        self,
    ) -> dict[str, Any]:

        contexto = self.cargar()

        return {
            "proyecto_id":
                contexto.proyecto_actual_id,

            "ruta_proyecto":
                contexto.ruta_proyecto_actual,

            "nombre_proyecto":
                contexto.nombre_proyecto_actual,

            "cliente":
                contexto.cliente_actual,

            "tipo_solucion":
                contexto.tipo_solucion,

            "lenguaje":
                contexto.lenguaje,

            "framework":
                contexto.framework,

            "base_datos":
                contexto.base_datos,

            "ventana":
                contexto.ventana_activa,

            "aplicaciones_relacionadas":
                list(
                    contexto.aplicaciones_relacionadas
                ),

            "archivos_relevantes":
                list(
                    contexto.archivos_relevantes
                ),

            "artefactos":
                list(
                    contexto.artefactos
                ),

            "ultima_tarea_id":
                contexto.ultima_tarea_id,

            "ultimo_proyecto_id":
                contexto.ultimo_proyecto_id,

            "ultimo_error":
                contexto.ultimo_error,

            "metadata":
                dict(
                    contexto.metadata
                ),
        }

    def resumen(
        self,
    ) -> dict[str, Any]:

        c = self.cargar()

        return {
            "actualizado_en":
                c.actualizado_en,

            "proyecto_actual_id":
                c.proyecto_actual_id,

            "ruta_proyecto_actual":
                c.ruta_proyecto_actual,

            "cliente_actual":
                c.cliente_actual,

            "tipo_solucion":
                c.tipo_solucion,

            "lenguaje":
                c.lenguaje,

            "framework":
                c.framework,

            "base_datos":
                c.base_datos,

            "ventana_activa":
                c.ventana_activa,

            "ultima_tarea_id":
                c.ultima_tarea_id,

            "ultimo_error":
                c.ultimo_error,

            "cantidad_archivos_relevantes":
                len(
                    c.archivos_relevantes
                ),

            "cantidad_artefactos":
                len(
                    c.artefactos
                ),

            "cantidad_decisiones":
                len(
                    c.decisiones_recientes
                ),
        }