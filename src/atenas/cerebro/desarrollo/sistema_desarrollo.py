from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from .politica import (
    PoliticaDesarrollo,
)

from .inspector_codigo import (
    InspectorCodigo,
)

from .mapa_proyecto import (
    MapaProyecto,
)

from .diagnostico import (
    DiagnosticoCodigo,
)

from .pruebas import (
    EjecutorPruebas,
)

from .parche import (
    GestorParches,
)

from .programador import (
    ProgramadorAtenas,
)

from .sandbox import (
    SandboxCodigo,
)

from .verificador import (
    VerificadorCambio,
)

from .historial_cambios import (
    HistorialCambios,
)

from .rollback import (
    GestorRollback,
)

from .autoreparacion import (
    Autorreparacion,
    ResultadoAutorreparacion,
)

from .automejora import (
    AutoMejora,
    InformeAutoMejora,
)

from .planificador_mejoras import (
    PlanificadorMejoras,
    PropuestaMejora,
)

from .motor_automejora import (
    MotorAutoMejora,
    DecisionAutoMejora,
    ResultadoMotorAutoMejora,
)

from .politica_aplicacion_mejoras import (
    PoliticaAplicacionMejoras,
    AplicadorMejoras,
    ResultadoAplicacionMejora,
)

from .ciclo_automejora import (
    CicloAutoMejora,
    ResultadoCicloAutoMejora,
)

from .iniciativa_automejora import (
    IniciativaAutoMejora,
    DecisionIniciativaAutoMejora,
    ResultadoIniciativaAutoMejora,
)

from .registro_propuestas import (
    EstadoPropuesta,
    PropuestaPersistida,
    RegistroPropuestasMejora,
)

from .reanudar_propuestas import (
    ResultadoReanudacionPropuesta,
    ReanudadorPropuestas,
)

from .director_desarrollo import (
    TipoIniciativaDesarrollo,
    IniciativaDesarrollo,
    ResultadoDirectorDesarrollo,
    DirectorDesarrolloAutonomo,
)

from .ciclo_desarrollo import (
    EstadoCicloDesarrollo,
    ResultadoCicloDesarrollo,
    CicloDesarrolloAutonomo,
)

from .proyectos_internos import (
    EstadoProyecto,
    EstadoObjetivoProyecto,
    ObjetivoProyecto,
    ProyectoInterno,
    GestorProyectosInternos,
)

from .planificador_proyectos import (
    ResultadoPlanificacionProyecto,
    PlanificadorProyectosInternos,
)

from .trabajador_proyectos import (
    ResultadoTrabajoProyecto,
    TrabajadorProyectosAutonomo,
)

from .programador_objetivos import (
    ArchivoSolucion,
    ResultadoProgramacionObjetivo,
    ProgramadorObjetivosAutonomo,
)

from .router_objetivos import (
    TipoTrabajoObjetivo,
    ClasificacionObjetivo,
    RouterObjetivosProyecto,
)


@dataclass
class EstadoDesarrollo:
    disponible: bool

    inspector: bool
    mapa_proyecto: bool
    diagnostico: bool
    programador: bool
    sandbox: bool
    pruebas: bool
    verificador: bool
    historial: bool
    rollback: bool
    autorreparacion: bool
    automejora: bool
    planificador_mejoras: bool
    motor_automejora: bool
    aplicacion_segura_mejoras: bool
    ciclo_automejora: bool
    iniciativa_automejora: bool
    propuestas_persistentes: bool
    reanudacion_propuestas: bool
    director_desarrollo: bool
    ciclo_desarrollo_autonomo: bool
    proyectos_internos: bool

    raiz_proyecto: str

    cambios_registrados: int = 0

    hallazgos_automejora: int = 0


class SistemaDesarrolloAtenas:
    """
    Fachada central del sistema de desarrollo de ATENAS.

    Reúne:

    - inspección de código;
    - mapa AST;
    - diagnóstico;
    - generación de correcciones;
    - parches;
    - sandbox;
    - pruebas;
    - verificación;
    - historial;
    - rollback;
    - autorreparación;
    - automejora estática.

    El LLM nunca obtiene acceso directo al filesystem
    ni a subprocess.
    """

    def __init__(
        self,
        llm: OllamaClient,
        raiz_proyecto: str | Path = ".",
        db_historial: str | Path | None = None,
    ):
        self.raiz = Path(
            raiz_proyecto
        ).resolve()

        self.llm = llm

        # =====================================================
        # POLÍTICA
        # =====================================================

        self.politica = (
            PoliticaDesarrollo(
                raiz_proyecto=self.raiz
            )
        )

        # =====================================================
        # INSPECCIÓN
        # =====================================================

        self.inspector = (
            InspectorCodigo(
                raiz_proyecto=self.raiz,
                politica=self.politica,
            )
        )

        # =====================================================
        # MAPA DEL PROYECTO
        # =====================================================

        self.mapa = (
            MapaProyecto(
                inspector=self.inspector
            )
        )

        # =====================================================
        # DIAGNÓSTICO
        # =====================================================

        self.diagnostico = (
            DiagnosticoCodigo(
                inspector=self.inspector,
                mapa=self.mapa,
            )
        )

        # =====================================================
        # PRUEBAS
        # =====================================================

        self.pruebas = (
            EjecutorPruebas(
                raiz_proyecto=self.raiz
            )
        )

        # =====================================================
        # PARCHES
        # =====================================================

        self.gestor_parches = (
            GestorParches(
                raiz_proyecto=self.raiz,
                politica=self.politica,
            )
        )

        # =====================================================
        # PROGRAMADOR
        # =====================================================

        self.programador = (
            ProgramadorAtenas(
                llm=self.llm,
                inspector=self.inspector,
                diagnostico=self.diagnostico,
                mapa=self.mapa,
                politica=self.politica,
                gestor_parches=self.gestor_parches,
            )
        )

        # =====================================================
        # SANDBOX
        # =====================================================

        self.sandbox = (
            SandboxCodigo(
                raiz_proyecto=self.raiz
            )
        )

        # =====================================================
        # VERIFICADOR
        # =====================================================

        self.verificador = (
            VerificadorCambio(
                politica=self.politica
            )
        )

        # =====================================================
        # HISTORIAL
        # =====================================================

        if db_historial is None:

            db_historial = (
                self.raiz
                / "data"
                / "atenas_desarrollo.db"
            )

        self.historial = (
            HistorialCambios(
                db_path=db_historial
            )
        )

        # =====================================================
        # ROLLBACK
        # =====================================================

        self.rollback = (
            GestorRollback(
                raiz_proyecto=self.raiz,
                historial=self.historial,
                politica=self.politica,
            )
        )

        # =====================================================
        # AUTORREPARACIÓN
        # =====================================================

        self.autorreparacion = (
            Autorreparacion(
                raiz_proyecto=self.raiz,
                inspector=self.inspector,
                diagnostico=self.diagnostico,
                programador=self.programador,
                sandbox=self.sandbox,
                verificador=self.verificador,
                politica=self.politica,
                historial=self.historial,
            )
        )

        # =====================================================
        # AUTOMEJORA
        # =====================================================

        self.automejora = (
            AutoMejora(
                inspector=self.inspector,
                mapa=self.mapa,
                politica=self.politica,
                historial=self.historial,
            )
        )

        self._ultimo_informe_automejora: (
            InformeAutoMejora | None
        ) = None

        # =====================================================
        # PLANIFICADOR DE MEJORAS
        # =====================================================

        self.planificador_mejoras = (
            PlanificadorMejoras(
                llm=self.llm,
                inspector=self.inspector,
                politica=self.politica,
                gestor_parches=self.gestor_parches,
                sandbox=self.sandbox,
                verificador=self.verificador,
            )
        )

        # =====================================================
        # MOTOR DE AUTOMEJORA
        # =====================================================

        self.motor_automejora = (
            MotorAutoMejora(
                politica=self.politica,
                planificador=self.planificador_mejoras,
                severidad_minima=0.55,
                confianza_minima=0.75,
                permitir_riesgo_medio=False,
            )
        )

        # =====================================================
        # APLICACIÓN SEGURA DE MEJORAS
        # =====================================================

        self.politica_aplicacion_mejoras = (
            PoliticaAplicacionMejoras(
                politica=self.politica
            )
        )

        self.aplicador_mejoras = (
            AplicadorMejoras(
                politica_aplicacion=(
                    self.politica_aplicacion_mejoras
                ),
                gestor_parches=(
                    self.gestor_parches
                ),
                historial=self.historial,
            )
        )

        # =====================================================
        # REGISTRO PERSISTENTE DE PROPUESTAS
        # =====================================================

        self.registro_propuestas = (
            RegistroPropuestasMejora(
                db_path=(
                    self.raiz
                    / "data"
                    / "atenas_propuestas.db"
                )
            )
        )

        # =====================================================
        # REANUDADOR DE PROPUESTAS
        # =====================================================

        self.reanudador_propuestas = (
            ReanudadorPropuestas(
                raiz_proyecto=self.raiz,
                registro=self.registro_propuestas,
                inspector=self.inspector,
                gestor_parches=self.gestor_parches,
                sandbox=self.sandbox,
                verificador=self.verificador,
                politica_aplicacion=(
                    self.politica_aplicacion_mejoras
                ),
                aplicador=self.aplicador_mejoras,
            )
        )

        # =====================================================
        # CICLO AUTÓNOMO DE AUTOMEJORA
        # =====================================================

        self.ciclo_automejora = (
            CicloAutoMejora(
                analizador=self.automejora,
                motor=self.motor_automejora,
                politica_aplicacion=(
                    self.politica_aplicacion_mejoras
                ),
                aplicador=self.aplicador_mejoras,
                registro_propuestas=(
                    self.registro_propuestas
                ),
            )
        )

        # =====================================================
        # INICIATIVA DE AUTOMEJORA
        # =====================================================

        self.iniciativa_automejora = (
            IniciativaAutoMejora(
                ciclo=self.ciclo_automejora,
                estado_path=(
                    self.raiz
                    / "data"
                    / "automejora_estado.json"
                ),
                cooldown_minutos=360,
                max_ciclos_diarios=3,
                autoaplicar=False,
            )
        )

        # =====================================================
        # DIRECTOR AUTÓNOMO DE DESARROLLO
        # =====================================================

        self.director_desarrollo = (
            DirectorDesarrolloAutonomo(
                desarrollo=self,
                supervisor_errores=None,
                severidad_minima=0.55,
                confianza_minima=0.70,
            )
        )

        # =====================================================
        # CICLO AUTÓNOMO GENERAL DE DESARROLLO
        # =====================================================

        self.ciclo_desarrollo_autonomo = (
            CicloDesarrolloAutonomo(
                desarrollo=self,
                estado_path=(
                    self.raiz
                    / "data"
                    / "desarrollo_autonomo_estado.json"
                ),
                revisar_cada_turnos=10,
                cooldown_minutos=30,
                max_ejecuciones_diarias=12,
                permitir_aplicacion_automatica=False,
            )
        )

        # =====================================================
        # PROYECTOS INTERNOS DE ATENAS
        # =====================================================

        self.proyectos_internos = (
            GestorProyectosInternos(
                db_path=(
                    self.raiz
                    / "data"
                    / "atenas_proyectos.db"
                )
            )
        )

        self.planificador_proyectos = (
            PlanificadorProyectosInternos(
                llm=self.llm,
                gestor=(
                    self.proyectos_internos
                ),
            )
        )

        self.trabajador_proyectos = (
            TrabajadorProyectosAutonomo(
                llm=self.llm,
                gestor=self.proyectos_internos,
                desarrollo=self,
                raiz_resultados=(
                    self.raiz
                    / "data"
                    / "proyectos_internos"
                ),
            )
        )

        self.programador_objetivos = (
            ProgramadorObjetivosAutonomo(
                llm=self.llm,
                gestor=self.proyectos_internos,
                desarrollo=self,
                raiz_soluciones=(
                    self.raiz
                    / "data"
                    / "soluciones_objetivos"
                ),
            )
        )

        self.router_objetivos = (
            RouterObjetivosProyecto()
        )

        self.director_desarrollo.trabajador_proyectos = (
            self.trabajador_proyectos
        )

    # =========================================================
    # ESTADO
    # =========================================================

    def estado(
        self,
    ) -> EstadoDesarrollo:

        hallazgos = 0

        if (
            self._ultimo_informe_automejora
            is not None
        ):

            hallazgos = len(
                self._ultimo_informe_automejora
                .hallazgos
            )

        return EstadoDesarrollo(
            disponible=True,

            inspector=True,
            mapa_proyecto=True,
            diagnostico=True,
            programador=True,
            sandbox=True,
            pruebas=True,
            verificador=True,
            historial=True,
            rollback=True,
            autorreparacion=True,
            automejora=True,
            planificador_mejoras=True,
            motor_automejora=True,
            aplicacion_segura_mejoras=True,
            ciclo_automejora=True,
            iniciativa_automejora=True,
            propuestas_persistentes=True,
            reanudacion_propuestas=True,
            director_desarrollo=True,
            ciclo_desarrollo_autonomo=True,
            proyectos_internos=True,

            raiz_proyecto=str(
                self.raiz
            ),

            cambios_registrados=(
                self.historial.contar()
            ),

            hallazgos_automejora=hallazgos,
        )

    # =========================================================
    # CONTEXTO PARA LLM
    # =========================================================

    def contexto_para_llm(
        self,
        incluir_automejora: bool = False,
        limite_hallazgos: int = 10,
    ) -> str:

        estado = self.estado()

        bloques = [
            f"""
SISTEMA DE DESARROLLO DE ATENAS:

Disponible: {"sí" if estado.disponible else "no"}

Capacidades:

- Inspección de código: {"sí" if estado.inspector else "no"}
- Mapa AST del proyecto: {"sí" if estado.mapa_proyecto else "no"}
- Diagnóstico de errores: {"sí" if estado.diagnostico else "no"}
- Generación de correcciones: {"sí" if estado.programador else "no"}
- Sandbox: {"sí" if estado.sandbox else "no"}
- Ejecución de pruebas: {"sí" if estado.pruebas else "no"}
- Verificación de cambios: {"sí" if estado.verificador else "no"}
- Historial de cambios: {"sí" if estado.historial else "no"}
- Rollback: {"sí" if estado.rollback else "no"}
- Autorreparación: {"sí" if estado.autorreparacion else "no"}
- Automejora estática: {"sí" if estado.automejora else "no"}
- Planificación de mejoras: {"sí" if estado.planificador_mejoras else "no"}
- Motor de automejora: {"sí" if estado.motor_automejora else "no"}
- Aplicación segura de mejoras: {"sí" if estado.aplicacion_segura_mejoras else "no"}
- Ciclo autónomo de automejora: {"sí" if estado.ciclo_automejora else "no"}
- Iniciativa de automejora: {"sí" if estado.iniciativa_automejora else "no"}
- Propuestas persistentes: {"sí" if estado.propuestas_persistentes else "no"}
- Reanudación segura de propuestas: {"sí" if estado.reanudacion_propuestas else "no"}
- Director autónomo de desarrollo: {"sí" if estado.director_desarrollo else "no"}
- Ciclo autónomo general de desarrollo: {"sí" if estado.ciclo_desarrollo_autonomo else "no"}
- Proyectos internos persistentes: {"sí" if estado.proyectos_internos else "no"}

Cambios registrados:
{estado.cambios_registrados}

Hallazgos de automejora del último análisis:
{estado.hallazgos_automejora}

REGLAS:

- Las correcciones se prueban primero en sandbox.
- Los cambios de riesgo medio o alto requieren aprobación.
- Los archivos protegidos no pueden modificarse automáticamente.
- El LLM no ejecuta comandos arbitrarios.
- Una corrección solo se considera aplicada cuando el sistema
  de desarrollo confirma su aplicación.
- Un hallazgo de automejora NO significa que exista un error.
- La automejora puede proponer cambios, pero no saltarse
  sandbox, pruebas, verificación ni política.
""".strip()
        ]

        if (
            incluir_automejora
            and self._ultimo_informe_automejora
            is not None
        ):

            bloques.append(
                self.automejora
                .contexto_para_llm(
                    self._ultimo_informe_automejora,
                    limite=limite_hallazgos,
                )
            )

        try:

            contexto_propuestas = (
                self.registro_propuestas
                .contexto_para_llm(
                    limite=10
                )
            )

            if contexto_propuestas:

                bloques.append(
                    contexto_propuestas
                )

        except Exception as error:

            bloques.append(
                "PROPUESTAS DE AUTOMEJORA PENDIENTES:\n"
                f"- No fue posible consultarlas: {error}"
            )

        try:

            bloques.append(
                self.ciclo_desarrollo_autonomo
                .contexto_para_llm()
            )

        except Exception:
            pass

        try:

            bloques.append(
                self.proyectos_internos
                .contexto_para_llm(
                    limite=10
                )
            )

        except Exception:
            pass

        return "\n\n".join(
            bloques
        )

    # =========================================================
    # PROYECTOS INTERNOS
    # =========================================================

    def crear_proyecto_interno(
        self,
        nombre: str,
        descripcion: str,
        prioridad: float = 0.5,
        autonomia: bool = True,
        requiere_confirmacion: bool = False,
    ) -> ResultadoPlanificacionProyecto:

        return (
            self.planificador_proyectos
            .crear_desde_meta(
                nombre=nombre,
                descripcion=descripcion,
                prioridad=prioridad,
                origen="atenas",
                autonomia=autonomia,
                requiere_confirmacion=(
                    requiere_confirmacion
                ),
            )
        )

    def trabajar_siguiente_objetivo_interno(
        self,
        proyecto_id: str | None = None,
    ):

        if proyecto_id:

            proyecto = (
                self.proyectos_internos
                .obtener_proyecto(
                    proyecto_id
                )
            )

        else:

            proyecto = (
                self.proyectos_internos
                .proyecto_prioritario()
            )

        if proyecto is None:

            return (
                self.trabajador_proyectos
                .ejecutar_siguiente(
                    proyecto_id=(
                        proyecto_id
                    )
                )
            )

        objetivo = (
            self.proyectos_internos
            .siguiente_objetivo(
                proyecto.id
            )
        )

        if objetivo is None:

            return (
                self.trabajador_proyectos
                .ejecutar_siguiente(
                    proyecto_id=(
                        proyecto.id
                    )
                )
            )

        clasificacion = (
            self.router_objetivos
            .clasificar(
                objetivo
            )
        )

        if (
            clasificacion.tipo
            == TipoTrabajoObjetivo.PROGRAMACION
        ):

            return (
                self.programador_objetivos
                .programar_objetivo(
                    proyecto=proyecto,
                    objetivo=objetivo,
                )
            )

        return (
            self.trabajador_proyectos
            .ejecutar_objetivo(
                proyecto=proyecto,
                objetivo=objetivo,
            )
        )

    def listar_proyectos_internos(
        self,
    ) -> list[ProyectoInterno]:

        return (
            self.proyectos_internos
            .listar_proyectos()
        )

    def proyecto_interno_prioritario(
        self,
    ) -> ProyectoInterno | None:

        return (
            self.proyectos_internos
            .proyecto_prioritario()
        )

    def siguiente_objetivo_proyecto(
        self,
        proyecto_id: str,
    ) -> ObjetivoProyecto | None:

        return (
            self.proyectos_internos
            .siguiente_objetivo(
                proyecto_id
            )
        )

    # =========================================================
    # CICLO AUTÓNOMO GENERAL DE DESARROLLO
    # =========================================================

    def registrar_turno_desarrollo(
        self,
    ) -> None:

        (
            self.ciclo_desarrollo_autonomo
            .registrar_turno()
        )

    def procesar_ciclo_desarrollo(
        self,
        tests: list[str] | None = None,
        forzar: bool = False,
        permitir_aplicacion: bool | None = None,
    ) -> ResultadoCicloDesarrollo:

        return (
            self.ciclo_desarrollo_autonomo
            .revisar_si_corresponde(
                tests=tests,
                forzar=forzar,
                permitir_aplicacion=(
                    permitir_aplicacion
                ),
            )
        )

    # =========================================================
    # DIRECTOR AUTÓNOMO DE DESARROLLO
    # =========================================================

    def conectar_supervisor_desarrollo(
        self,
        supervisor,
    ) -> None:
        """
        Conecta SupervisorErrores al director una vez que el
        núcleo conversacional haya creado ambos componentes.
        """

        self.director_desarrollo.supervisor_errores = (
            supervisor
        )

    def decidir_siguiente_trabajo_desarrollo(
        self,
    ) -> IniciativaDesarrollo:
        """
        ATENAS observa su estado y decide qué trabajo de
        ingeniería conviene atender a continuación.
        """

        return (
            self.director_desarrollo
            .decidir()
        )

    def ejecutar_siguiente_trabajo_desarrollo(
        self,
        tests: list[str] | None = None,
        permitir_aplicacion: bool = False,
    ) -> ResultadoDirectorDesarrollo:
        """
        Ejecuta una sola iniciativa de desarrollo prioritaria.

        permitir_aplicacion=False mantiene el modo conservador:
        ATENAS puede diagnosticar, organizar, planificar,
        programar una solución y validarla, pero no necesariamente
        aplicarla al proyecto real.
        """

        return (
            self.director_desarrollo
            .ejecutar(
                tests=tests,
                permitir_aplicacion=(
                    permitir_aplicacion
                ),
            )
        )

    # =========================================================
    # REANUDAR PROPUESTAS PERSISTIDAS
    # =========================================================

    def reanudar_propuesta(
        self,
        propuesta_id: str,
        tests: list[str] | None = None,
    ) -> ResultadoReanudacionPropuesta:

        return (
            self.reanudador_propuestas
            .preparar(
                propuesta_id=propuesta_id,
                tests=tests,
            )
        )

    def aplicar_propuesta_persistida(
        self,
        propuesta_id: str,
        tests: list[str] | None = None,
        confirmada: bool = False,
    ) -> ResultadoReanudacionPropuesta:

        return (
            self.reanudador_propuestas
            .aplicar(
                propuesta_id=propuesta_id,
                tests=tests,
                confirmada=confirmada,
            )
        )

    # =========================================================
    # PROPUESTAS PERSISTENTES
    # =========================================================

    def propuestas_pendientes(
        self,
        limite: int = 50,
    ) -> list[PropuestaPersistida]:

        return (
            self.registro_propuestas
            .pendientes(
                limite=limite
            )
        )

    def obtener_propuesta_persistida(
        self,
        propuesta_id: str,
    ) -> PropuestaPersistida | None:

        return (
            self.registro_propuestas
            .obtener(
                propuesta_id
            )
        )

    def rechazar_propuesta_persistida(
        self,
        propuesta_id: str,
    ) -> PropuestaPersistida:

        return (
            self.registro_propuestas
            .rechazar(
                propuesta_id
            )
        )

    def descartar_propuesta_persistida(
        self,
        propuesta_id: str,
    ) -> PropuestaPersistida:

        return (
            self.registro_propuestas
            .descartar(
                propuesta_id
            )
        )

    # =========================================================
    # INSPECCIÓN
    # =========================================================

    def leer_codigo(
        self,
        ruta: str,
    ) -> dict:

        return (
            self.inspector
            .leer_archivo(
                ruta
            )
        )

    def buscar_simbolo(
        self,
        nombre: str,
    ) -> list[dict]:

        return (
            self.inspector
            .buscar_simbolo(
                nombre
            )
        )

    # =========================================================
    # DIAGNÓSTICO
    # =========================================================

    def diagnosticar(
        self,
        traceback_texto: str,
    ):

        return (
            self.diagnostico
            .analizar(
                traceback_texto
            )
        )

    # =========================================================
    # AUTORREPARACIÓN
    # =========================================================

    def reparar_error(
        self,
        traceback_texto: str,
        tests: list[str] | None = None,
        aplicar_bajo_riesgo: bool = False,
    ) -> ResultadoAutorreparacion:

        return (
            self.autorreparacion
            .reparar(
                traceback_texto=(
                    traceback_texto
                ),
                tests=tests,
                aplicar_bajo_riesgo=(
                    aplicar_bajo_riesgo
                ),
            )
        )

    # =========================================================
    # AUTOMEJORA
    # =========================================================

    def analizar_mejoras(
        self,
        limite_archivos: int | None = None,
    ) -> InformeAutoMejora:

        informe = (
            self.automejora
            .analizar_proyecto(
                limite_archivos=(
                    limite_archivos
                )
            )
        )

        self._ultimo_informe_automejora = (
            informe
        )

        return informe

    def ultimo_informe_mejoras(
        self,
    ) -> InformeAutoMejora | None:

        return (
            self._ultimo_informe_automejora
        )

    def contexto_mejoras_para_llm(
        self,
        limite: int = 20,
        ejecutar_si_falta: bool = True,
    ) -> str:

        informe = (
            self._ultimo_informe_automejora
        )

        if (
            informe is None
            and ejecutar_si_falta
        ):

            informe = (
                self.analizar_mejoras()
            )

        if informe is None:

            return (
                "ANÁLISIS DE AUTOMEJORA DE ATENAS:\n"
                "- Todavía no se ha ejecutado un análisis."
            )

        return (
            self.automejora
            .contexto_para_llm(
                informe,
                limite=limite,
            )
        )

    def mejoras_prioritarias(
        self,
        limite: int = 10,
        severidad_minima: float = 0.50,
    ):

        informe = (
            self._ultimo_informe_automejora
            or self.analizar_mejoras()
        )

        hallazgos = [
            hallazgo
            for hallazgo
            in informe.hallazgos
            if (
                hallazgo.severidad
                >= severidad_minima
            )
        ]

        return hallazgos[
            :max(
                1,
                int(limite),
            )
        ]

    # =========================================================
    # EJECUTAR INICIATIVA DE AUTOMEJORA
    # =========================================================

    def ejecutar_iniciativa_automejora(
        self,
        tests: list[str] | None = None,
        forzar: bool = False,
        permitir_aplicacion: bool | None = None,
        limite_archivos: int | None = None,
    ) -> ResultadoIniciativaAutoMejora:

        resultado = (
            self.iniciativa_automejora
            .ejecutar_si_corresponde(
                tests=tests,
                forzar=forzar,
                permitir_aplicacion=(
                    permitir_aplicacion
                ),
                limite_archivos=(
                    limite_archivos
                ),
            )
        )

        if (
            resultado.ciclo is not None
            and resultado.ciclo.informe is not None
        ):

            self._ultimo_informe_automejora = (
                resultado.ciclo.informe
            )

        return resultado

    # =========================================================
    # EJECUTAR CICLO AUTÓNOMO DE AUTOMEJORA
    # =========================================================

    def ejecutar_ciclo_automejora(
        self,
        tests: list[str] | None = None,
        permitir_aplicacion: bool = False,
        limite_archivos: int | None = None,
    ) -> ResultadoCicloAutoMejora:

        resultado = (
            self.ciclo_automejora
            .ejecutar(
                tests=tests,
                permitir_aplicacion=(
                    permitir_aplicacion
                ),
                limite_archivos=(
                    limite_archivos
                ),
            )
        )

        if (
            resultado.informe
            is not None
        ):

            self._ultimo_informe_automejora = (
                resultado.informe
            )

        return resultado

    # =========================================================
    # ELEGIR Y PREPARAR MEJORA AUTÓNOMAMENTE
    # =========================================================

    def preparar_mejora_autonoma(
        self,
        tests: list[str] | None = None,
        ejecutar_analisis: bool = True,
    ) -> ResultadoMotorAutoMejora:

        informe = (
            self._ultimo_informe_automejora
        )

        if (
            informe is None
            or ejecutar_analisis
        ):

            informe = (
                self.analizar_mejoras()
            )

        return (
            self.motor_automejora
            .procesar(
                informe=informe,
                tests=tests,
            )
        )

    # =========================================================
    # APLICAR PROPUESTA DE MEJORA
    # =========================================================

    def aplicar_propuesta_mejora(
        self,
        propuesta: PropuestaMejora,
        permitir_aplicacion: bool = False,
    ) -> ResultadoAplicacionMejora:
        """
        Aplica una mejora validada únicamente cuando el llamador
        habilita explícitamente la aplicación y la política
        específica de automejora la considera segura.
        """

        if not permitir_aplicacion:

            decision = (
                self.politica_aplicacion_mejoras
                .evaluar(
                    propuesta
                )
            )

            return ResultadoAplicacionMejora(
                ok=True,
                aplicada=False,
                decision=decision,
                mensaje=(
                    "La propuesta fue evaluada, "
                    "pero la aplicación no está "
                    "habilitada para esta llamada."
                ),
            )

        return (
            self.aplicador_mejoras
            .aplicar(
                propuesta
            )
        )

    # =========================================================
    # PROPONER MEJORA
    # =========================================================

    def proponer_mejora(
        self,
        hallazgo,
        tests: list[str] | None = None,
    ) -> PropuestaMejora:
        """
        Genera y valida una propuesta de mejora en sandbox.

        Nunca aplica la propuesta al proyecto real.
        """

        return (
            self.planificador_mejoras
            .proponer(
                hallazgo=hallazgo,
                tests=tests,
            )
        )

    # =========================================================
    # ROLLBACK
    # =========================================================

    def revertir_cambio(
        self,
        cambio_id: str,
    ):

        return (
            self.rollback
            .revertir(
                cambio_id
            )
        )

    # =========================================================
    # HISTORIAL
    # =========================================================

    def ultimos_cambios(
        self,
        limite: int = 20,
    ) -> list[dict]:

        return (
            self.historial
            .ultimos(
                limite=limite
            )
        )