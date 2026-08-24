from __future__ import annotations

import json

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class EspecificacionProyecto:
    nombre: str
    descripcion: str
    tipo: str

    cliente: str | None = None
    lenguaje: str | None = None

    objetivos: list[str] = field(
        default_factory=list
    )

    requisitos: list[str] = field(
        default_factory=list
    )

    arquitectura: list[str] = field(
        default_factory=list
    )

    entregables: list[str] = field(
        default_factory=list
    )

    pruebas: list[str] = field(
        default_factory=list
    )

    riesgos: list[str] = field(
        default_factory=list
    )

    notas: list[str] = field(
        default_factory=list
    )


@dataclass
class ResultadoDocumentacionProyecto:
    ok: bool

    archivos: list[str] = field(
        default_factory=list
    )

    pdf_generado: bool = False

    error_pdf: str | None = None


class DocumentadorProyecto:
    """
    Genera documentación persistente de un proyecto.

    Siempre intenta crear:
    - README.md
    - ESPECIFICACIONES.md
    - proyecto.json

    Opcionalmente genera:
    - ESPECIFICACIONES.pdf
    """

    def __init__(
        self,
    ):
        pass

    # =========================================================
    # MARKDOWN
    # =========================================================

    @staticmethod
    def _lista_md(
        titulo: str,
        items: list[str],
    ) -> str:

        lineas = [
            f"## {titulo}",
            "",
        ]

        if not items:

            lineas.append(
                "- Pendiente de definir."
            )

        else:

            lineas.extend(
                f"- {item}"
                for item
                in items
            )

        lineas.append(
            ""
        )

        return "\n".join(
            lineas
        )

    def _markdown(
        self,
        spec: EspecificacionProyecto,
    ) -> str:

        lineas = [
            f"# {spec.nombre}",
            "",
            spec.descripcion,
            "",
            "## Información general",
            "",
            f"- Tipo: {spec.tipo}",
            f"- Cliente: {spec.cliente or 'No aplica'}",
            f"- Lenguaje principal: {spec.lenguaje or 'Por definir'}",
            (
                "- Generado por: ATENAS"
            ),
            (
                "- Fecha: "
                + datetime.now(
                    timezone.utc
                ).isoformat()
            ),
            "",
        ]

        for titulo, items in [
            (
                "Objetivos",
                spec.objetivos,
            ),
            (
                "Requisitos",
                spec.requisitos,
            ),
            (
                "Arquitectura",
                spec.arquitectura,
            ),
            (
                "Entregables",
                spec.entregables,
            ),
            (
                "Pruebas y validación",
                spec.pruebas,
            ),
            (
                "Riesgos",
                spec.riesgos,
            ),
            (
                "Notas",
                spec.notas,
            ),
        ]:

            lineas.append(
                self._lista_md(
                    titulo,
                    items,
                )
            )

        return "\n".join(
            lineas
        )

    # =========================================================
    # PDF
    # =========================================================

    def _crear_pdf(
        self,
        ruta: Path,
        spec: EspecificacionProyecto,
    ) -> tuple[bool, str | None]:

        try:

            from reportlab.lib.pagesizes import (
                A4,
            )

            from reportlab.lib.styles import (
                getSampleStyleSheet,
            )

            from reportlab.lib.units import (
                cm,
            )

            from reportlab.platypus import (
                ListFlowable,
                ListItem,
                Paragraph,
                SimpleDocTemplate,
                Spacer,
            )

        except Exception as error:

            return (
                False,
                (
                    "ReportLab no disponible: "
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        try:

            estilos = (
                getSampleStyleSheet()
            )

            doc = (
                SimpleDocTemplate(
                    str(
                        ruta
                    ),
                    pagesize=A4,
                    rightMargin=2 * cm,
                    leftMargin=2 * cm,
                    topMargin=2 * cm,
                    bottomMargin=2 * cm,
                    title=spec.nombre,
                    author="ATENAS",
                )
            )

            elementos = [
                Paragraph(
                    spec.nombre,
                    estilos["Title"],
                ),
                Spacer(
                    1,
                    0.4 * cm,
                ),
                Paragraph(
                    spec.descripcion,
                    estilos["BodyText"],
                ),
                Spacer(
                    1,
                    0.5 * cm,
                ),
            ]

            info = [
                f"Tipo: {spec.tipo}",
                (
                    "Cliente: "
                    + (
                        spec.cliente
                        or "No aplica"
                    )
                ),
                (
                    "Lenguaje principal: "
                    + (
                        spec.lenguaje
                        or "Por definir"
                    )
                ),
            ]

            elementos.append(
                Paragraph(
                    "Información general",
                    estilos["Heading2"],
                )
            )

            elementos.append(
                ListFlowable([
                    ListItem(
                        Paragraph(
                            item,
                            estilos[
                                "BodyText"
                            ],
                        )
                    )
                    for item
                    in info
                ])
            )

            secciones = [
                (
                    "Objetivos",
                    spec.objetivos,
                ),
                (
                    "Requisitos",
                    spec.requisitos,
                ),
                (
                    "Arquitectura",
                    spec.arquitectura,
                ),
                (
                    "Entregables",
                    spec.entregables,
                ),
                (
                    "Pruebas y validación",
                    spec.pruebas,
                ),
                (
                    "Riesgos",
                    spec.riesgos,
                ),
                (
                    "Notas",
                    spec.notas,
                ),
            ]

            for titulo, items in secciones:

                elementos.append(
                    Spacer(
                        1,
                        0.35 * cm,
                    )
                )

                elementos.append(
                    Paragraph(
                        titulo,
                        estilos[
                            "Heading2"
                        ],
                    )
                )

                elementos.append(
                    ListFlowable([
                        ListItem(
                            Paragraph(
                                item,
                                estilos[
                                    "BodyText"
                                ],
                            )
                        )
                        for item
                        in (
                            items
                            or [
                                "Pendiente de definir."
                            ]
                        )
                    ])
                )

            doc.build(
                elementos
            )

            return (
                True,
                None,
            )

        except Exception as error:

            return (
                False,
                (
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    # =========================================================
    # GENERAR TODO
    # =========================================================

    def generar(
        self,
        carpeta: str | Path,
        spec: EspecificacionProyecto,
        crear_pdf: bool = True,
    ) -> ResultadoDocumentacionProyecto:

        carpeta = Path(
            carpeta
        ).resolve()

        carpeta.mkdir(
            parents=True,
            exist_ok=True,
        )

        markdown = (
            self._markdown(
                spec
            )
        )

        readme = (
            carpeta
            / "README.md"
        )

        especificaciones_md = (
            carpeta
            / "ESPECIFICACIONES.md"
        )

        proyecto_json = (
            carpeta
            / "proyecto.json"
        )

        readme.write_text(
            markdown,
            encoding="utf-8",
        )

        especificaciones_md.write_text(
            markdown,
            encoding="utf-8",
        )

        proyecto_json.write_text(
            json.dumps(
                asdict(
                    spec
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        archivos = [
            str(
                readme
            ),
            str(
                especificaciones_md
            ),
            str(
                proyecto_json
            ),
        ]

        pdf_generado = False
        error_pdf = None

        if crear_pdf:

            pdf = (
                carpeta
                / "ESPECIFICACIONES.pdf"
            )

            pdf_generado, error_pdf = (
                self._crear_pdf(
                    pdf,
                    spec,
                )
            )

            if pdf_generado:

                archivos.append(
                    str(
                        pdf
                    )
                )

        return ResultadoDocumentacionProyecto(
            ok=True,
            archivos=archivos,
            pdf_generado=(
                pdf_generado
            ),
            error_pdf=(
                error_pdf
            ),
        )