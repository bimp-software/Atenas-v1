from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analista_requisitos import AnalisisRequisitos
from .arquitecto_software import ArquitecturaSoftware
from .disenador_base_datos import ModeloBaseDatos
from .planificador_sistema_software import PlanSistemaSoftware
from .gestor_estado_proyecto_software import EstadoIntegralProyecto


@dataclass
class DocumentoGenerado:
    nombre: str
    ruta: str
    tipo: str
    generado: bool
    error: str | None = None


@dataclass
class ResultadoDocumentacionProfesional:
    ok: bool
    carpeta: str

    documentos: list[DocumentoGenerado] = field(
        default_factory=list
    )

    dossier_pdf: str | None = None
    indice_json: str | None = None

    error: str | None = None


class GeneradorDocumentacionProfesional:
    """
    Genera documentación técnica y ejecutiva profesional para un
    proyecto completo desarrollado por ATENAS.

    Produce:
    - resumen ejecutivo;
    - especificación de requisitos;
    - arquitectura;
    - modelo de datos;
    - plan de desarrollo;
    - estado del proyecto;
    - dossier consolidado PDF;
    - archivos Markdown equivalentes;
    - índice JSON para futura web.

    La documentación se deriva de estructuras reales del proyecto,
    no de texto inventado por separado.
    """

    def __init__(
        self,
        nombre_autor: str = "ATENAS",
        organizacion: str = "ATENAS",
    ):
        self.nombre_autor = nombre_autor
        self.organizacion = organizacion

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _ahora() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _texto(valor: Any) -> str:
        if valor is None:
            return "No definido"

        if isinstance(
            valor,
            (dict, list, tuple),
        ):
            return json.dumps(
                valor,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

        return str(valor)

    @staticmethod
    def _md_lista(
        items: list[str],
    ) -> str:
        if not items:
            return "- Sin elementos registrados.\n"

        return "".join(
            f"- {item}\n"
            for item in items
        )

    # =========================================================
    # MARKDOWN
    # =========================================================

    def _md_resumen(
        self,
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
        estado: EstadoIntegralProyecto | None,
    ) -> str:

        return f"""# Resumen Ejecutivo

**Proyecto:** {analisis.nombre_proyecto}  
**Tipo de solución:** {analisis.tipo_solucion.value}  
**Arquitectura:** {arquitectura.estilo}  
**Complejidad:** {analisis.complejidad}  
**Estado:** {estado.estado.value if estado else "No disponible"}  
**Progreso:** {estado.progreso if estado else 0.0}%  
**Versión:** {estado.version if estado else "0.1.0"}  
**Generado por:** {self.nombre_autor}  
**Fecha:** {self._ahora()}

## Visión general

{analisis.resumen or "Sin resumen disponible."}

## Actores principales

{self._md_lista(analisis.actores)}

## Riesgos iniciales

{self._md_lista(analisis.riesgos_iniciales)}

## Decisiones principales de arquitectura

{self._md_lista(arquitectura.decisiones)}

## Estado actual

- Fase actual: {estado.fase_actual if estado else "No definida"}
- Épica actual: {estado.epica_actual if estado else "No definida"}
- Tarea actual: {estado.tarea_actual_titulo if estado else "No definida"}
- Última validación correcta: {estado.ultima_validacion_ok if estado else "No disponible"}
"""

    def _md_requisitos(
        self,
        analisis: AnalisisRequisitos,
    ) -> str:

        lineas = [
            "# Especificación de Requisitos",
            "",
            f"Proyecto: **{analisis.nombre_proyecto}**",
            "",
            "## Requisitos funcionales",
            "",
        ]

        if analisis.requisitos_funcionales:

            lineas.extend([
                "| ID | Prioridad | Obligatorio | Descripción |",
                "|---|---|---|---|",
            ])

            for req in analisis.requisitos_funcionales:

                lineas.append(
                    f"| {req.id} | {req.prioridad} | "
                    f"{'Sí' if req.obligatorio else 'No'} | "
                    f"{req.descripcion} |"
                )

        else:
            lineas.append(
                "No se registraron requisitos funcionales."
            )

        lineas.extend([
            "",
            "## Requisitos no funcionales",
            "",
        ])

        if analisis.requisitos_no_funcionales:

            lineas.extend([
                "| ID | Prioridad | Obligatorio | Descripción |",
                "|---|---|---|---|",
            ])

            for req in analisis.requisitos_no_funcionales:

                lineas.append(
                    f"| {req.id} | {req.prioridad} | "
                    f"{'Sí' if req.obligatorio else 'No'} | "
                    f"{req.descripcion} |"
                )

        else:
            lineas.append(
                "No se registraron requisitos no funcionales."
            )

        lineas.extend([
            "",
            "## Entidades de negocio",
            "",
            self._md_lista(
                analisis.entidades_negocio
            ),
            "",
            "## Integraciones",
            "",
            self._md_lista(
                analisis.integraciones
            ),
            "",
            "## Restricciones",
            "",
            self._md_lista(
                analisis.restricciones
            ),
            "",
            "## Capacidades requeridas",
            "",
            f"- Base de datos: {analisis.necesita_base_datos}",
            f"- Autenticación: {analisis.necesita_autenticacion}",
            f"- Roles: {analisis.necesita_roles}",
            f"- API: {analisis.necesita_api}",
            f"- Archivos: {analisis.necesita_archivos}",
            f"- Tiempo real: {analisis.necesita_tiempo_real}",
            f"- Offline: {analisis.necesita_offline}",
            "",
            "## Preguntas abiertas",
            "",
            self._md_lista(
                analisis.preguntas_abiertas
            ),
        ])

        return "\n".join(
            lineas
        )

    def _md_arquitectura(
        self,
        arquitectura: ArquitecturaSoftware,
    ) -> str:

        lineas = [
            "# Arquitectura de Software",
            "",
            f"**Estilo:** {arquitectura.estilo}",
            f"**Tipo de solución:** {arquitectura.tipo_solucion}",
            "",
            "## Componentes tecnológicos",
            "",
            f"### Frontend\n\n```json\n{self._texto(arquitectura.frontend)}\n```",
            "",
            f"### Backend\n\n```json\n{self._texto(arquitectura.backend)}\n```",
            "",
            f"### Escritorio\n\n```json\n{self._texto(arquitectura.desktop)}\n```",
            "",
            f"### Móvil\n\n```json\n{self._texto(arquitectura.movil)}\n```",
            "",
            f"### API\n\n```json\n{self._texto(arquitectura.api)}\n```",
            "",
            f"### Base de datos\n\n```json\n{self._texto(arquitectura.base_datos)}\n```",
            "",
            "## Componentes lógicos",
            "",
        ]

        if arquitectura.componentes:

            lineas.extend([
                "| Componente | Responsabilidad | Tecnología | Lenguaje | Dependencias |",
                "|---|---|---|---|---|",
            ])

            for componente in arquitectura.componentes:

                lineas.append(
                    f"| {componente.nombre} | "
                    f"{componente.responsabilidad} | "
                    f"{componente.tecnologia} | "
                    f"{componente.lenguaje} | "
                    f"{', '.join(componente.depende_de)} |"
                )

        else:
            lineas.append(
                "No hay componentes registrados."
            )

        lineas.extend([
            "",
            "## Seguridad",
            "",
            self._md_lista(
                arquitectura.seguridad
            ),
            "",
            "## Estrategia de pruebas",
            "",
            "```json",
            self._texto(
                arquitectura.pruebas
            ),
            "```",
            "",
            "## Despliegue",
            "",
            "```json",
            self._texto(
                arquitectura.despliegue
            ),
            "```",
            "",
            "## Decisiones de arquitectura",
            "",
            self._md_lista(
                arquitectura.decisiones
            ),
        ])

        return "\n".join(
            lineas
        )

    def _md_base_datos(
        self,
        modelo: ModeloBaseDatos | None,
    ) -> str:

        if modelo is None:

            return """# Modelo de Datos

Este proyecto no requiere una base de datos según el análisis actual.
"""

        lineas = [
            "# Modelo de Datos",
            "",
            f"**Motor:** {modelo.motor}",
            f"**Nombre lógico:** {modelo.nombre}",
            "",
            "## Tablas",
            "",
        ]

        for tabla in modelo.tablas:

            lineas.extend([
                f"### {tabla.nombre}",
                "",
                tabla.descripcion or "",
                "",
                "| Campo | Tipo | Nullable | Unique | Default | Descripción |",
                "|---|---|---|---|---|---|",
            ])

            for campo in tabla.campos:

                lineas.append(
                    f"| {campo.nombre} | {campo.tipo} | "
                    f"{campo.nullable} | {campo.unique} | "
                    f"{campo.default or ''} | "
                    f"{campo.descripcion} |"
                )

            lineas.extend([
                "",
                (
                    "**Clave primaria:** "
                    + (
                        ", ".join(
                            tabla.clave_primaria
                        )
                        or "No definida"
                    )
                ),
                "",
            ])

        lineas.extend([
            "## Relaciones",
            "",
        ])

        if modelo.relaciones:

            lineas.extend([
                "| Origen | Campo | Destino | Campo | Tipo | On Delete | On Update |",
                "|---|---|---|---|---|---|---|",
            ])

            for relacion in modelo.relaciones:

                lineas.append(
                    f"| {relacion.origen_tabla} | "
                    f"{relacion.origen_campo} | "
                    f"{relacion.destino_tabla} | "
                    f"{relacion.destino_campo} | "
                    f"{relacion.tipo} | "
                    f"{relacion.on_delete} | "
                    f"{relacion.on_update} |"
                )

        else:
            lineas.append(
                "No hay relaciones registradas."
            )

        lineas.extend([
            "",
            "## Migraciones",
            "",
            modelo.estrategia_migraciones
            or "No definida.",
            "",
            "## Respaldo",
            "",
            modelo.estrategia_backup
            or "No definido.",
            "",
            "## Integridad",
            "",
            self._md_lista(
                modelo.estrategia_integridad
            ),
            "",
            "## Decisiones",
            "",
            self._md_lista(
                modelo.decisiones
            ),
        ])

        return "\n".join(
            lineas
        )

    def _md_plan(
        self,
        plan: PlanSistemaSoftware,
    ) -> str:

        lineas = [
            "# Plan de Desarrollo",
            "",
            f"**Proyecto:** {plan.nombre_proyecto}",
            f"**Arquitectura:** {plan.arquitectura}",
            f"**Complejidad:** {plan.complejidad}",
            "",
        ]

        for fase in sorted(
            plan.fases,
            key=lambda item: item.orden,
        ):

            lineas.extend([
                f"## Fase {fase.orden}: {fase.nombre}",
                "",
                fase.objetivo,
                "",
            ])

            for epica in fase.epicas:

                lineas.extend([
                    f"### Épica: {epica.nombre}",
                    "",
                    epica.descripcion,
                    "",
                ])

                for tarea in epica.tareas:

                    lineas.extend([
                        f"#### {tarea.titulo}",
                        "",
                        f"- Estado: {tarea.estado.value}",
                        f"- Tipo: {tarea.tipo}",
                        f"- Prioridad: {tarea.prioridad}",
                        f"- Lenguaje: {tarea.lenguaje or 'No definido'}",
                        f"- Tecnología: {tarea.tecnologia or 'No definida'}",
                        (
                            "- Dependencias: "
                            + (
                                ", ".join(
                                    tarea.depende_de
                                )
                                or "Ninguna"
                            )
                        ),
                        "",
                        tarea.descripcion,
                        "",
                        "**Criterios de aceptación**",
                        "",
                        self._md_lista(
                            tarea.criterios_aceptacion
                        ),
                        "",
                    ])

        return "\n".join(
            lineas
        )

    def _md_estado(
        self,
        estado: EstadoIntegralProyecto | None,
    ) -> str:

        if estado is None:

            return """# Estado del Proyecto

No existe un estado integral disponible.
"""

        lineas = [
            "# Estado del Proyecto",
            "",
            f"**Proyecto:** {estado.nombre}",
            f"**Estado:** {estado.estado.value}",
            f"**Progreso:** {estado.progreso}%",
            f"**Versión:** {estado.version}",
            f"**Actualizado:** {estado.actualizado_en}",
            "",
            "## Tarea actual",
            "",
            f"- Fase: {estado.fase_actual or 'No definida'}",
            f"- Épica: {estado.epica_actual or 'No definida'}",
            f"- Tarea: {estado.tarea_actual_titulo or 'No definida'}",
            "",
            "## Resumen de tareas",
            "",
            "| Total | Pendientes | Bloqueadas | En progreso | Completadas | Fallidas | Canceladas |",
            "|---|---|---|---|---|---|---|",
            (
                f"| {estado.tareas.total} | "
                f"{estado.tareas.pendientes} | "
                f"{estado.tareas.bloqueadas} | "
                f"{estado.tareas.en_progreso} | "
                f"{estado.tareas.completadas} | "
                f"{estado.tareas.fallidas} | "
                f"{estado.tareas.canceladas} |"
            ),
            "",
            "## Bloqueos",
            "",
        ]

        if estado.bloqueos:

            for bloqueo in estado.bloqueos:

                lineas.append(
                    (
                        f"- [{bloqueo.tipo}] "
                        f"{bloqueo.descripcion} "
                        f"(confirmación: "
                        f"{bloqueo.requiere_confirmacion})"
                    )
                )

        else:
            lineas.append(
                "- Sin bloqueos activos."
            )

        lineas.extend([
            "",
            "## Entregables",
            "",
        ])

        if estado.entregables:

            lineas.extend([
                "| Nombre | Tipo | Generado | Versión | Ruta |",
                "|---|---|---|---|---|",
            ])

            for entregable in estado.entregables:

                lineas.append(
                    f"| {entregable.nombre} | "
                    f"{entregable.tipo} | "
                    f"{entregable.generado} | "
                    f"{entregable.version or ''} | "
                    f"{entregable.ruta} |"
                )

        else:
            lineas.append(
                "No hay entregables registrados."
            )

        return "\n".join(
            lineas
        )

    # =========================================================
    # PDF
    # =========================================================

    @staticmethod
    def _importar_reportlab():
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import (
            ParagraphStyle,
            getSampleStyleSheet,
        )
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            KeepTogether,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )

        return {
            "colors": colors,
            "TA_CENTER": TA_CENTER,
            "A4": A4,
            "ParagraphStyle": ParagraphStyle,
            "getSampleStyleSheet": getSampleStyleSheet,
            "cm": cm,
            "KeepTogether": KeepTogether,
            "PageBreak": PageBreak,
            "Paragraph": Paragraph,
            "SimpleDocTemplate": SimpleDocTemplate,
            "Spacer": Spacer,
            "Table": Table,
            "TableStyle": TableStyle,
        }

    def _crear_dossier_pdf(
        self,
        ruta: Path,
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
        modelo: ModeloBaseDatos | None,
        plan: PlanSistemaSoftware,
        estado: EstadoIntegralProyecto | None,
    ) -> None:

        rl = self._importar_reportlab()

        colors = rl["colors"]
        A4 = rl["A4"]
        cm = rl["cm"]
        Paragraph = rl["Paragraph"]
        Spacer = rl["Spacer"]
        Table = rl["Table"]
        TableStyle = rl["TableStyle"]
        PageBreak = rl["PageBreak"]
        SimpleDocTemplate = rl["SimpleDocTemplate"]
        ParagraphStyle = rl["ParagraphStyle"]
        getSampleStyleSheet = rl["getSampleStyleSheet"]
        TA_CENTER = rl["TA_CENTER"]

        styles = getSampleStyleSheet()

        titulo = ParagraphStyle(
            "TituloAtenas",
            parent=styles["Title"],
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            spaceAfter=18,
        )

        subtitulo = ParagraphStyle(
            "SubtituloAtenas",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            alignment=TA_CENTER,
            spaceAfter=12,
        )

        h1 = ParagraphStyle(
            "H1Atenas",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            spaceBefore=14,
            spaceAfter=10,
        )

        h2 = ParagraphStyle(
            "H2Atenas",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            spaceBefore=10,
            spaceAfter=6,
        )

        body = ParagraphStyle(
            "BodyAtenas",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=13,
            spaceAfter=6,
        )

        small = ParagraphStyle(
            "SmallAtenas",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
        )

        doc = SimpleDocTemplate(
            str(ruta),
            pagesize=A4,
            rightMargin=1.7 * cm,
            leftMargin=1.7 * cm,
            topMargin=1.7 * cm,
            bottomMargin=1.7 * cm,
            title=f"Dossier - {analisis.nombre_proyecto}",
            author=self.nombre_autor,
            subject="Documentación técnica del proyecto",
        )

        story = []

        # Portada
        story.extend([
            Spacer(1, 3.3 * cm),
            Paragraph(
                analisis.nombre_proyecto,
                titulo,
            ),
            Paragraph(
                "Dossier Técnico y Ejecutivo",
                subtitulo,
            ),
            Spacer(1, 1.2 * cm),
        ])

        portada = [
            ["Tipo de solución", analisis.tipo_solucion.value],
            ["Arquitectura", arquitectura.estilo],
            ["Complejidad", analisis.complejidad],
            [
                "Estado",
                (
                    estado.estado.value
                    if estado
                    else "No disponible"
                ),
            ],
            [
                "Versión",
                (
                    estado.version
                    if estado
                    else "0.1.0"
                ),
            ],
            ["Generado por", self.nombre_autor],
            ["Fecha", self._ahora()],
        ]

        tabla_portada = Table(
            portada,
            colWidths=[
                5 * cm,
                9 * cm,
            ],
        )

        tabla_portada.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.whitesmoke,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ])
        )

        story.append(
            tabla_portada
        )

        story.append(
            PageBreak()
        )

        # Índice manual
        story.append(
            Paragraph(
                "Contenido",
                h1,
            )
        )

        secciones = [
            "1. Resumen ejecutivo",
            "2. Requisitos",
            "3. Arquitectura de software",
            "4. Modelo de datos",
            "5. Plan de desarrollo",
            "6. Estado del proyecto",
        ]

        for item in secciones:

            story.append(
                Paragraph(
                    item,
                    body,
                )
            )

        story.append(
            PageBreak()
        )

        # 1 Resumen ejecutivo
        story.append(
            Paragraph(
                "1. Resumen ejecutivo",
                h1,
            )
        )

        story.append(
            Paragraph(
                analisis.resumen
                or "Sin resumen disponible.",
                body,
            )
        )

        datos_resumen = [
            ["Aspecto", "Valor"],
            ["Tipo", analisis.tipo_solucion.value],
            ["Complejidad", analisis.complejidad],
            ["Arquitectura", arquitectura.estilo],
            [
                "Progreso",
                (
                    f"{estado.progreso}%"
                    if estado
                    else "No disponible"
                ),
            ],
        ]

        tabla = Table(
            datos_resumen,
            colWidths=[
                5 * cm,
                9 * cm,
            ],
            repeatRows=1,
        )

        tabla.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8.5,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
            ])
        )

        story.append(
            tabla
        )

        story.append(
            Spacer(
                1,
                0.4 * cm,
            )
        )

        story.append(
            Paragraph(
                "Actores",
                h2,
            )
        )

        for actor in (
            analisis.actores
            or ["Sin actores registrados."]
        ):

            story.append(
                Paragraph(
                    f"- {actor}",
                    body,
                )
            )

        # 2 Requisitos
        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "2. Especificación de requisitos",
                h1,
            )
        )

        requisitos = [
            [
                "ID",
                "Tipo",
                "Prioridad",
                "Oblig.",
                "Descripción",
            ]
        ]

        for req in (
            analisis.requisitos_funcionales
        ):

            requisitos.append([
                req.id,
                "Funcional",
                req.prioridad,
                (
                    "Sí"
                    if req.obligatorio
                    else "No"
                ),
                req.descripcion,
            ])

        for req in (
            analisis
            .requisitos_no_funcionales
        ):

            requisitos.append([
                req.id,
                "No funcional",
                req.prioridad,
                (
                    "Sí"
                    if req.obligatorio
                    else "No"
                ),
                req.descripcion,
            ])

        if len(requisitos) == 1:

            requisitos.append([
                "-",
                "-",
                "-",
                "-",
                "Sin requisitos registrados.",
            ])

        tabla_req = Table(
            [
                [
                    Paragraph(
                        str(celda),
                        small,
                    )
                    for celda
                    in fila
                ]
                for fila
                in requisitos
            ],
            colWidths=[
                1.4 * cm,
                2.3 * cm,
                1.8 * cm,
                1.4 * cm,
                8.2 * cm,
            ],
            repeatRows=1,
        )

        tabla_req.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.3,
                    colors.grey,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
            ])
        )

        story.append(
            tabla_req
        )

        # 3 Arquitectura
        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "3. Arquitectura de software",
                h1,
            )
        )

        story.append(
            Paragraph(
                (
                    f"El sistema utiliza una arquitectura "
                    f"<b>{arquitectura.estilo}</b>."
                ),
                body,
            )
        )

        for componente in (
            arquitectura.componentes
        ):

            story.append(
                Paragraph(
                    componente.nombre,
                    h2,
                )
            )

            story.append(
                Paragraph(
                    componente.responsabilidad
                    or "Sin descripción.",
                    body,
                )
            )

            story.append(
                Paragraph(
                    (
                        f"Tecnología: "
                        f"{componente.tecnologia or 'No definida'} | "
                        f"Lenguaje: "
                        f"{componente.lenguaje or 'No definido'}"
                    ),
                    small,
                )
            )

        story.append(
            Paragraph(
                "Seguridad",
                h2,
            )
        )

        for item in (
            arquitectura.seguridad
            or ["Sin controles de seguridad registrados."]
        ):

            story.append(
                Paragraph(
                    f"- {item}",
                    body,
                )
            )

        # 4 Datos
        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "4. Modelo de datos",
                h1,
            )
        )

        if modelo is None:

            story.append(
                Paragraph(
                    "El proyecto no requiere una base de datos.",
                    body,
                )
            )

        else:

            story.append(
                Paragraph(
                    (
                        f"Motor: <b>{modelo.motor}</b> - "
                        f"Nombre lógico: "
                        f"<b>{modelo.nombre}</b>"
                    ),
                    body,
                )
            )

            for tabla_bd in modelo.tablas:

                story.append(
                    Paragraph(
                        tabla_bd.nombre,
                        h2,
                    )
                )

                filas = [
                    [
                        "Campo",
                        "Tipo",
                        "Null",
                        "Unique",
                        "Descripción",
                    ]
                ]

                for campo in tabla_bd.campos:

                    filas.append([
                        campo.nombre,
                        campo.tipo,
                        str(
                            campo.nullable
                        ),
                        str(
                            campo.unique
                        ),
                        campo.descripcion,
                    ])

                tabla_pdf = Table(
                    [
                        [
                            Paragraph(
                                str(c),
                                small,
                            )
                            for c in fila
                        ]
                        for fila
                        in filas
                    ],
                    colWidths=[
                        3 * cm,
                        2.8 * cm,
                        1.3 * cm,
                        1.5 * cm,
                        6.3 * cm,
                    ],
                    repeatRows=1,
                )

                tabla_pdf.setStyle(
                    TableStyle([
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.lightgrey,
                        ),
                        (
                            "GRID",
                            (0, 0),
                            (-1, -1),
                            0.3,
                            colors.grey,
                        ),
                        (
                            "FONTNAME",
                            (0, 0),
                            (-1, 0),
                            "Helvetica-Bold",
                        ),
                        (
                            "VALIGN",
                            (0, 0),
                            (-1, -1),
                            "TOP",
                        ),
                    ])
                )

                story.append(
                    tabla_pdf
                )

                story.append(
                    Spacer(
                        1,
                        0.3 * cm,
                    )
                )

        # 5 Plan
        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "5. Plan de desarrollo",
                h1,
            )
        )

        for fase in sorted(
            plan.fases,
            key=lambda item: item.orden,
        ):

            story.append(
                Paragraph(
                    (
                        f"Fase {fase.orden}: "
                        f"{fase.nombre}"
                    ),
                    h2,
                )
            )

            story.append(
                Paragraph(
                    fase.objetivo
                    or "Sin objetivo registrado.",
                    body,
                )
            )

            for epica in fase.epicas:

                story.append(
                    Paragraph(
                        (
                            f"Épica: "
                            f"{epica.nombre}"
                        ),
                        body,
                    )
                )

                for tarea in epica.tareas:

                    story.append(
                        Paragraph(
                            (
                                f"- {tarea.titulo} "
                                f"[{tarea.estado.value}]"
                            ),
                            small,
                        )
                    )

        # 6 Estado
        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "6. Estado del proyecto",
                h1,
            )
        )

        if estado is None:

            story.append(
                Paragraph(
                    "No existe estado integral disponible.",
                    body,
                )
            )

        else:

            filas_estado = [
                ["Métrica", "Valor"],
                ["Estado", estado.estado.value],
                ["Progreso", f"{estado.progreso}%"],
                ["Versión", estado.version],
                [
                    "Fase actual",
                    estado.fase_actual
                    or "No definida",
                ],
                [
                    "Épica actual",
                    estado.epica_actual
                    or "No definida",
                ],
                [
                    "Tarea actual",
                    estado.tarea_actual_titulo
                    or "No definida",
                ],
                [
                    "Última validación",
                    str(
                        estado.ultima_validacion_ok
                    ),
                ],
            ]

            tabla_estado = Table(
                filas_estado,
                colWidths=[
                    5 * cm,
                    9 * cm,
                ],
            )

            tabla_estado.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.lightgrey,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.3,
                        colors.grey,
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold",
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),
                ])
            )

            story.append(
                tabla_estado
            )

        doc.build(
            story
        )

    # =========================================================
    # GENERAR TODO
    # =========================================================

    def generar(
        self,
        carpeta_proyecto: str | Path,
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
        modelo_bd: ModeloBaseDatos | None,
        plan: PlanSistemaSoftware,
        estado: EstadoIntegralProyecto | None,
    ) -> ResultadoDocumentacionProfesional:

        raiz = Path(
            carpeta_proyecto
        ).resolve()

        docs = (
            raiz
            / "docs"
        )

        docs.mkdir(
            parents=True,
            exist_ok=True,
        )

        documentos: list[
            DocumentoGenerado
        ] = []

        fuentes = {
            "00_RESUMEN_EJECUTIVO.md":
                self._md_resumen(
                    analisis,
                    arquitectura,
                    estado,
                ),

            "01_ESPECIFICACION_REQUISITOS.md":
                self._md_requisitos(
                    analisis
                ),

            "02_ARQUITECTURA_SOFTWARE.md":
                self._md_arquitectura(
                    arquitectura
                ),

            "03_MODELO_DATOS.md":
                self._md_base_datos(
                    modelo_bd
                ),

            "04_PLAN_DESARROLLO.md":
                self._md_plan(
                    plan
                ),

            "05_ESTADO_PROYECTO.md":
                self._md_estado(
                    estado
                ),
        }

        for nombre, contenido in fuentes.items():

            ruta = (
                docs
                / nombre
            )

            ruta.write_text(
                contenido,
                encoding="utf-8",
            )

            documentos.append(
                DocumentoGenerado(
                    nombre=nombre,
                    ruta=str(
                        ruta
                    ),
                    tipo="markdown",
                    generado=True,
                )
            )

        dossier = (
            docs
            / "DOSSIER_PROYECTO.pdf"
        )

        dossier_error = None

        try:

            self._crear_dossier_pdf(
                ruta=dossier,
                analisis=analisis,
                arquitectura=arquitectura,
                modelo=modelo_bd,
                plan=plan,
                estado=estado,
            )

            dossier_generado = (
                dossier.exists()
                and dossier.stat().st_size > 0
            )

        except Exception as error:

            dossier_generado = False

            dossier_error = (
                f"{type(error).__name__}: "
                f"{error}"
            )

        documentos.append(
            DocumentoGenerado(
                nombre=(
                    "DOSSIER_PROYECTO.pdf"
                ),
                ruta=str(
                    dossier
                ),
                tipo="pdf",
                generado=(
                    dossier_generado
                ),
                error=(
                    dossier_error
                ),
            )
        )

        indice = (
            docs
            / "documentacion.json"
        )

        indice.write_text(
            json.dumps(
                {
                    "proyecto":
                        analisis.nombre_proyecto,

                    "version": (
                        estado.version
                        if estado
                        else "0.1.0"
                    ),

                    "generado_en":
                        self._ahora(),

                    "autor":
                        self.nombre_autor,

                    "organizacion":
                        self.organizacion,

                    "documentos": [
                        asdict(
                            documento
                        )
                        for documento
                        in documentos
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return ResultadoDocumentacionProfesional(
            ok=all(
                documento.generado
                for documento
                in documentos
                if documento.tipo
                == "markdown"
            ),
            carpeta=str(
                docs
            ),
            documentos=documentos,
            dossier_pdf=(
                str(
                    dossier
                )
                if dossier_generado
                else None
            ),
            indice_json=str(
                indice
            ),
            error=(
                dossier_error
            ),
        )