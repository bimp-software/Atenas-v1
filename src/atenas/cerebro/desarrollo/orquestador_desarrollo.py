from __future__ import annotations

import json
import uuid

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .analista_requisitos import (
    AnalistaRequisitos,
    AnalisisRequisitos,
)

from .arquitecto_software import (
    ArquitectoSoftware,
    ArquitecturaSoftware,
)

from .disenador_base_datos import (
    DisenadorBaseDatos,
    ModeloBaseDatos,
)

from .generador_artefactos_base_datos import (
    GeneradorArtefactosBaseDatos,
    ResultadoGeneracionBaseDatos,
)

from .planificador_sistema_software import (
    PlanificadorSistemaSoftware,
    PlanSistemaSoftware,
)

from .gestor_estado_proyecto_software import (
    EstadoIntegralProyecto,
    EstadoProyectoSoftware,
    GestorEstadoProyectoSoftware,
)

from .gestor_entornos_proyecto import (
    GestorEntornosProyecto,
)

from .gestor_seguro_dependencias import (
    GestorSeguroDependencias,
)

from .coordinador_dependencias_tarea import (
    CoordinadorDependenciasTarea,
    EstadoDependenciasTarea,
)

from .programador_tarea_software import (
    ProgramadorTareaSoftware,
)

from .validador_tarea_software import (
    ValidadorTareaSoftware,
)

from .reparador_tarea_software import (
    ReparadorTareaSoftware,
)

from .ejecutor_plan_software import (
    EjecutorPlanSoftware,
)

from .generador_documentacion_profesional import (
    GeneradorDocumentacionProfesional,
    ResultadoDocumentacionProfesional,
)


@dataclass
class ResultadoInicioDesarrollo:
    ok: bool
    proyecto_id: str
    carpeta_proyecto: str

    analisis: AnalisisRequisitos | None = None
    arquitectura: ArquitecturaSoftware | None = None
    modelo_bd: ModeloBaseDatos | None = None
    plan: PlanSistemaSoftware | None = None
    estado: EstadoIntegralProyecto | None = None

    base_datos: ResultadoGeneracionBaseDatos | None = None
    documentacion: ResultadoDocumentacionProfesional | None = None

    error: str | None = None


@dataclass
class ResultadoCicloDesarrollo:
    ok: bool
    estado: str

    proyecto_id: str
    carpeta_proyecto: str

    tarea: str | None = None

    progreso: float = 0.0
    plan_completado: bool = False

    requiere_confirmacion: bool = False
    dependencias_pendientes: list[str] = None

    mensaje: str = ""
    error: str | None = None

    def __post_init__(
        self,
    ):
        if self.dependencias_pendientes is None:
            self.dependencias_pendientes = []


class OrquestadorDesarrollo:
    """
    Orquestador maestro del subsistema de Desarrollo de ATENAS.

    Responsabilidades:
    - analizar una necesidad;
    - diseñar arquitectura;
    - diseñar base de datos;
    - generar artefactos SQL;
    - planificar el sistema;
    - crear estado persistente;
    - preparar entorno;
    - detectar dependencias faltantes;
    - ejecutar una tarea por ciclo;
    - validar y reparar;
    - actualizar progreso;
    - regenerar documentación profesional;
    - permitir reanudación.

    No intenta hacer todo en una sola llamada.
    """

    def __init__(
        self,
        llm: Any,
        raiz_planes: str | Path,
    ):
        self.llm = llm

        self.analista = (
            AnalistaRequisitos(
                llm=llm
            )
        )

        self.arquitecto = (
            ArquitectoSoftware(
                llm=llm
            )
        )

        self.disenador_bd = (
            DisenadorBaseDatos(
                llm=llm
            )
        )

        self.generador_bd = (
            GeneradorArtefactosBaseDatos()
        )

        self.planificador = (
            PlanificadorSistemaSoftware(
                llm=llm,
                raiz_planes=raiz_planes,
            )
        )

        self.gestor_entornos = (
            GestorEntornosProyecto()
        )

        self.gestor_dependencias = (
            GestorSeguroDependencias()
        )

        self.coordinador_dependencias = (
            CoordinadorDependenciasTarea(
                gestor_entornos=(
                    self.gestor_entornos
                ),
                gestor_dependencias=(
                    self.gestor_dependencias
                ),
            )
        )

        self.programador = (
            ProgramadorTareaSoftware(
                llm=llm
            )
        )

        self.validador = (
            ValidadorTareaSoftware()
        )

        self.reparador = (
            ReparadorTareaSoftware(
                llm=llm,
                validador=(
                    self.validador
                ),
                max_intentos=3,
            )
        )

        self.ejecutor = (
            EjecutorPlanSoftware(
                programador=(
                    self.programador
                ),
                validador=(
                    self.validador
                ),
                reparador=(
                    self.reparador
                ),
            )
        )

        self.documentador = (
            GeneradorDocumentacionProfesional()
        )

    # =========================================================
    # PERSISTENCIA ESTRUCTURAL
    # =========================================================

    @staticmethod
    def _carpeta_atenas(
        carpeta_proyecto: Path,
    ) -> Path:

        carpeta = (
            carpeta_proyecto
            / ".atenas"
        )

        carpeta.mkdir(
            parents=True,
            exist_ok=True,
        )

        return carpeta

    def _guardar_contexto(
        self,
        carpeta_proyecto: Path,
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
        modelo_bd: ModeloBaseDatos | None,
        plan: PlanSistemaSoftware,
    ) -> None:

        carpeta = (
            self._carpeta_atenas(
                carpeta_proyecto
            )
        )

        (
            carpeta
            / "analisis_requisitos.json"
        ).write_text(
            json.dumps(
                asdict(
                    analisis
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        (
            carpeta
            / "arquitectura.json"
        ).write_text(
            json.dumps(
                asdict(
                    arquitectura
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        (
            carpeta
            / "modelo_datos.json"
        ).write_text(
            json.dumps(
                (
                    asdict(
                        modelo_bd
                    )
                    if modelo_bd is not None
                    else None
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        (
            carpeta
            / "plan_software.json"
        ).write_text(
            json.dumps(
                asdict(
                    plan
                ),
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

        plan.ruta_persistencia = str(
            carpeta
            / "plan_software.json"
        )

    # =========================================================
    # INICIAR PROYECTO
    # =========================================================

    def iniciar(
        self,
        descripcion: str,
        carpeta_proyecto: str | Path,
    ) -> ResultadoInicioDesarrollo:

        carpeta = Path(
            carpeta_proyecto
        ).resolve()

        carpeta.mkdir(
            parents=True,
            exist_ok=True,
        )

        proyecto_id = str(
            uuid.uuid4()
        )

        try:

            analisis = (
                self.analista
                .analizar(
                    descripcion
                )
            )

            arquitectura = (
                self.arquitecto
                .diseñar(
                    analisis
                )
            )

            modelo_bd = (
                self.disenador_bd
                .diseñar(
                    analisis=analisis,
                    arquitectura=arquitectura,
                )
            )

            plan = (
                self.planificador
                .planificar(
                    analisis=analisis,
                    arquitectura=arquitectura,
                    modelo_bd=modelo_bd,
                )
            )

            self._guardar_contexto(
                carpeta_proyecto=carpeta,
                analisis=analisis,
                arquitectura=arquitectura,
                modelo_bd=modelo_bd,
                plan=plan,
            )

            gestor_estado = (
                GestorEstadoProyectoSoftware(
                    carpeta
                )
            )

            estado = (
                gestor_estado
                .cargar_o_crear(
                    proyecto_id=(
                        proyecto_id
                    ),
                    nombre=(
                        analisis
                        .nombre_proyecto
                    ),
                )
            )

            estado.estado = (
                EstadoProyectoSoftware
                .PLANIFICADO
            )

            gestor_estado.actualizar_tecnologias(
                estado,
                {
                    "arquitectura":
                        arquitectura.estilo,

                    "frontend":
                        arquitectura.frontend,

                    "backend":
                        arquitectura.backend,

                    "desktop":
                        arquitectura.desktop,

                    "movil":
                        arquitectura.movil,

                    "api":
                        arquitectura.api,
                },
            )

            gestor_estado.actualizar_base_datos(
                estado,
                (
                    asdict(
                        modelo_bd
                    )
                    if modelo_bd is not None
                    else None
                ),
            )

            resultado_bd = None

            if modelo_bd is not None:

                resultado_bd = (
                    self.generador_bd
                    .generar(
                        carpeta_proyecto=(
                            carpeta
                        ),
                        modelo=modelo_bd,
                    )
                )

            estado = (
                gestor_estado
                .sincronizar_plan(
                    estado=estado,
                    plan=plan,
                )
            )

            documentacion = (
                self.documentador
                .generar(
                    carpeta_proyecto=(
                        carpeta
                    ),
                    analisis=analisis,
                    arquitectura=arquitectura,
                    modelo_bd=modelo_bd,
                    plan=plan,
                    estado=estado,
                )
            )

            if documentacion.dossier_pdf:

                gestor_estado.registrar_entregable(
                    estado=estado,
                    nombre=(
                        "Dossier del proyecto"
                    ),
                    ruta=(
                        documentacion
                        .dossier_pdf
                    ),
                    tipo="pdf",
                    version=(
                        estado.version
                    ),
                )

            return ResultadoInicioDesarrollo(
                ok=True,
                proyecto_id=(
                    proyecto_id
                ),
                carpeta_proyecto=str(
                    carpeta
                ),
                analisis=analisis,
                arquitectura=arquitectura,
                modelo_bd=modelo_bd,
                plan=plan,
                estado=estado,
                base_datos=resultado_bd,
                documentacion=(
                    documentacion
                ),
            )

        except Exception as error:

            return ResultadoInicioDesarrollo(
                ok=False,
                proyecto_id=(
                    proyecto_id
                ),
                carpeta_proyecto=str(
                    carpeta
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

    # =========================================================
    # CICLO
    # =========================================================

    def ejecutar_ciclo(
        self,
        carpeta_proyecto: str | Path,
        proyecto_id: str,
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
        modelo_bd: ModeloBaseDatos | None,
        plan: PlanSistemaSoftware,
    ) -> ResultadoCicloDesarrollo:

        carpeta = Path(
            carpeta_proyecto
        ).resolve()

        gestor_estado = (
            GestorEstadoProyectoSoftware(
                carpeta
            )
        )

        estado = (
            gestor_estado
            .cargar_o_crear(
                proyecto_id=(
                    proyecto_id
                ),
                nombre=(
                    analisis
                    .nombre_proyecto
                ),
            )
        )

        # =====================================================
        # PREPARAR ENTORNO / DEPENDENCIAS
        # =====================================================

        estado.estado = (
            EstadoProyectoSoftware
            .PREPARANDO_ENTORNO
        )

        gestor_estado.guardar(
            estado
        )

        preparacion = (
            self.coordinador_dependencias
            .preparar(
                carpeta
            )
        )

        if preparacion.plan_entorno is not None:

            gestor_estado.actualizar_entorno(
                estado,
                asdict(
                    preparacion
                    .plan_entorno
                ),
            )

        if (
            preparacion.estado
            == EstadoDependenciasTarea
            .REQUIERE_CONFIRMACION
        ):

            nombres = [
                pendiente
                .dependencia
                .nombre
                for pendiente
                in preparacion.pendientes
            ]

            gestor_estado.agregar_bloqueo(
                estado=estado,
                tipo="dependencias",
                descripcion=(
                    "Dependencias pendientes: "
                    + ", ".join(
                        nombres
                    )
                ),
                requiere_confirmacion=True,
            )

            return ResultadoCicloDesarrollo(
                ok=False,
                estado=(
                    "requiere_confirmacion_dependencias"
                ),
                proyecto_id=(
                    proyecto_id
                ),
                carpeta_proyecto=str(
                    carpeta
                ),
                progreso=(
                    estado.progreso
                ),
                requiere_confirmacion=True,
                dependencias_pendientes=(
                    nombres
                ),
                mensaje=(
                    "El desarrollo quedó pausado "
                    "hasta resolver dependencias."
                ),
            )

        if not preparacion.ok:

            gestor_estado.agregar_bloqueo(
                estado=estado,
                tipo="entorno",
                descripcion=(
                    "; ".join(
                        preparacion.mensajes
                    )
                ),
                requiere_confirmacion=False,
            )

            return ResultadoCicloDesarrollo(
                ok=False,
                estado=(
                    "bloqueado_entorno"
                ),
                proyecto_id=(
                    proyecto_id
                ),
                carpeta_proyecto=str(
                    carpeta
                ),
                progreso=(
                    estado.progreso
                ),
                mensaje=(
                    "; ".join(
                        preparacion.mensajes
                    )
                ),
            )

        gestor_estado.limpiar_bloqueos(
            estado,
            tipo="entorno",
        )

        gestor_estado.limpiar_bloqueos(
            estado,
            tipo="dependencias",
        )

        # =====================================================
        # EJECUTAR UNA TAREA
        # =====================================================

        estado.estado = (
            EstadoProyectoSoftware
            .EN_DESARROLLO
        )

        gestor_estado.guardar(
            estado
        )

        resultado = (
            self.ejecutor
            .ejecutar_siguiente(
                carpeta_proyecto=(
                    carpeta
                ),
                analisis=analisis,
                arquitectura=arquitectura,
                modelo_bd=modelo_bd,
                plan=plan,
            )
        )

        estado = (
            gestor_estado
            .sincronizar_plan(
                estado=estado,
                plan=plan,
            )
        )

        if resultado.validacion is not None:

            gestor_estado.registrar_validacion(
                estado=estado,
                ok=(
                    resultado
                    .validacion
                    .ok
                ),
                resumen=(
                    resultado
                    .validacion
                    .resumen
                ),
            )

        # =====================================================
        # REGENERAR DOCUMENTACIÓN
        # =====================================================

        documentacion = (
            self.documentador
            .generar(
                carpeta_proyecto=(
                    carpeta
                ),
                analisis=analisis,
                arquitectura=arquitectura,
                modelo_bd=modelo_bd,
                plan=plan,
                estado=estado,
            )
        )

        if (
            resultado.plan_completado
        ):

            estado.estado = (
                EstadoProyectoSoftware
                .COMPLETADO
            )

            estado.progreso = 100.0

            gestor_estado.guardar(
                estado
            )

        tarea_titulo = (
            resultado.tarea.titulo
            if resultado.tarea
            else None
        )

        return ResultadoCicloDesarrollo(
            ok=(
                resultado.ok
            ),
            estado=(
                resultado.estado
            ),
            proyecto_id=(
                proyecto_id
            ),
            carpeta_proyecto=str(
                carpeta
            ),
            tarea=(
                tarea_titulo
            ),
            progreso=(
                estado.progreso
            ),
            plan_completado=(
                resultado
                .plan_completado
            ),
            mensaje=(
                resultado.mensaje
            ),
            error=(
                resultado.error
            ),
        )

    # =========================================================
    # EJECUTAR HASTA PAUSA / FIN
    # =========================================================

    def ejecutar_hasta_pausa(
        self,
        carpeta_proyecto: str | Path,
        proyecto_id: str,
        analisis: AnalisisRequisitos,
        arquitectura: ArquitecturaSoftware,
        modelo_bd: ModeloBaseDatos | None,
        plan: PlanSistemaSoftware,
        max_ciclos: int = 25,
    ) -> list[ResultadoCicloDesarrollo]:

        resultados = []

        for _ in range(
            max(
                1,
                int(max_ciclos),
            )
        ):

            resultado = (
                self.ejecutar_ciclo(
                    carpeta_proyecto=(
                        carpeta_proyecto
                    ),
                    proyecto_id=(
                        proyecto_id
                    ),
                    analisis=(
                        analisis
                    ),
                    arquitectura=(
                        arquitectura
                    ),
                    modelo_bd=(
                        modelo_bd
                    ),
                    plan=plan,
                )
            )

            resultados.append(
                resultado
            )

            if (
                resultado.plan_completado
                or resultado.requiere_confirmacion
                or not resultado.ok
            ):

                break

        return resultados