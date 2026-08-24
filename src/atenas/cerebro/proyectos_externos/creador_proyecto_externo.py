from __future__ import annotations

import json

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .clasificador_proyecto_externo import (
    ClasificadorProyectoExterno,
)

from .documentador_proyecto import (
    DocumentadorProyecto,
    EspecificacionProyecto,
)

from .espacios_trabajo import (
    DestinoProyecto,
    GestorEspaciosTrabajo,
)

from .programador_proyecto_externo import (
    ProgramadorProyectoExterno,
    ResultadoProgramacionProyectoExterno,
)


@dataclass
class ResultadoCreacionProyectoExterno:
    ok: bool

    nombre: str

    destino: DestinoProyecto | None = None

    carpeta: str | None = None

    archivos_creados: list[str] = field(
        default_factory=list
    )

    pdf_generado: bool = False

    programacion: (
        ResultadoProgramacionProyectoExterno
        | None
    ) = None

    error: str | None = None


class CreadorProyectosExternos:
    """
    Crea y programa proyectos externos.

    Flujo:
    1. clasifica el proyecto;
    2. decide dónde guardarlo;
    3. crea la estructura;
    4. genera documentación;
    5. programa la solución;
    6. deja un manifiesto de generación.
    """

    def __init__(
        self,
        llm: Any,
        espacios: GestorEspaciosTrabajo,
    ):
        self.llm = llm
        self.espacios = espacios

        self.clasificador = (
            ClasificadorProyectoExterno(
                llm=llm
            )
        )

        self.documentador = (
            DocumentadorProyecto()
        )

        self.programador = (
            ProgramadorProyectoExterno(
                llm=llm
            )
        )

    # =========================================================
    # ESTRUCTURA
    # =========================================================

    @staticmethod
    def _crear_estructura(
        carpeta: Path,
    ) -> list[str]:

        carpetas = [
            carpeta / "src",
            carpeta / "tests",
            carpeta / "docs",
            carpeta / "assets",
        ]

        for ruta in carpetas:

            ruta.mkdir(
                parents=True,
                exist_ok=True,
            )

        gitignore = (
            carpeta
            / ".gitignore"
        )

        if not gitignore.exists():

            gitignore.write_text(
                (
                    "__pycache__/\n"
                    ".venv/\n"
                    "node_modules/\n"
                    ".env\n"
                    "dist/\n"
                    "build/\n"
                ),
                encoding="utf-8",
            )

        return [
            str(ruta)
            for ruta in carpetas
        ] + [
            str(
                gitignore
            )
        ]

    # =========================================================
    # CREAR + PROGRAMAR
    # =========================================================

    def crear(
        self,
        descripcion: str,
        objetivos: list[str] | None = None,
        requisitos: list[str] | None = None,
        arquitectura: list[str] | None = None,
        entregables: list[str] | None = None,
        pruebas: list[str] | None = None,
        riesgos: list[str] | None = None,
        programar_solucion: bool = True,
    ) -> ResultadoCreacionProyectoExterno:

        clasificacion = (
            self.clasificador
            .clasificar(
                descripcion
            )
        )

        destino = (
            self.espacios
            .resolver(
                tipo=(
                    clasificacion.tipo
                ),
                nombre_proyecto=(
                    clasificacion.nombre
                ),
                cliente=(
                    clasificacion.cliente
                ),
            )
        )

        carpeta = Path(
            destino.carpeta_proyecto
        )

        try:

            carpeta.mkdir(
                parents=True,
                exist_ok=True,
            )

            archivos = (
                self._crear_estructura(
                    carpeta
                )
            )

            spec = (
                EspecificacionProyecto(
                    nombre=(
                        clasificacion.nombre
                    ),
                    descripcion=(
                        descripcion
                    ),
                    tipo=(
                        clasificacion.tipo.value
                    ),
                    cliente=(
                        clasificacion.cliente
                    ),
                    lenguaje=(
                        clasificacion
                        .lenguaje_sugerido
                    ),
                    objetivos=(
                        objetivos
                        or []
                    ),
                    requisitos=(
                        requisitos
                        or []
                    ),
                    arquitectura=(
                        arquitectura
                        or []
                    ),
                    entregables=(
                        entregables
                        or []
                    ),
                    pruebas=(
                        pruebas
                        or []
                    ),
                    riesgos=(
                        riesgos
                        or []
                    ),
                    notas=[
                        (
                            "Destino elegido "
                            "automáticamente por ATENAS."
                        ),
                        (
                            "Confianza de clasificación: "
                            f"{clasificacion.confianza:.2f}"
                        ),
                        (
                            "Motivo: "
                            f"{clasificacion.motivo}"
                        ),
                    ],
                )
            )

            documentacion = (
                self.documentador
                .generar(
                    carpeta=carpeta,
                    spec=spec,
                    crear_pdf=(
                        clasificacion
                        .necesita_pdf
                    ),
                )
            )

            archivos.extend(
                documentacion.archivos
            )

            programacion = None

            if programar_solucion:

                especificaciones = {
                    "nombre":
                        spec.nombre,

                    "descripcion":
                        spec.descripcion,

                    "tipo":
                        spec.tipo,

                    "cliente":
                        spec.cliente,

                    "lenguaje":
                        spec.lenguaje,

                    "objetivos":
                        spec.objetivos,

                    "requisitos":
                        spec.requisitos,

                    "arquitectura":
                        spec.arquitectura,

                    "entregables":
                        spec.entregables,

                    "pruebas":
                        spec.pruebas,

                    "riesgos":
                        spec.riesgos,
                }

                programacion = (
                    self.programador
                    .programar(
                        carpeta_proyecto=(
                            carpeta
                        ),
                        especificaciones=(
                            especificaciones
                        ),
                    )
                )

                for archivo in (
                    programacion.archivos
                ):

                    if archivo.valido:

                        archivos.append(
                            str(
                                (
                                    carpeta
                                    / archivo.ruta
                                ).resolve()
                            )
                        )

                manifest = (
                    carpeta
                    / "ATENAS_GENERACION.json"
                )

                if manifest.exists():

                    archivos.append(
                        str(
                            manifest
                        )
                    )

            return ResultadoCreacionProyectoExterno(
                ok=bool(
                    documentacion.ok
                    and (
                        programacion is None
                        or programacion.ok
                    )
                ),
                nombre=(
                    clasificacion.nombre
                ),
                destino=destino,
                carpeta=str(
                    carpeta.resolve()
                ),
                archivos_creados=(
                    archivos
                ),
                pdf_generado=(
                    documentacion.pdf_generado
                ),
                programacion=(
                    programacion
                ),
                error=(
                    programacion.error
                    if (
                        programacion is not None
                        and not programacion.ok
                    )
                    else None
                ),
            )

        except Exception as error:

            return ResultadoCreacionProyectoExterno(
                ok=False,
                nombre=(
                    clasificacion.nombre
                ),
                destino=destino,
                carpeta=str(
                    carpeta
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )