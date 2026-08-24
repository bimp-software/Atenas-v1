from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TipoIniciativaDesarrollo(str, Enum):
    REPARAR_ERROR = "reparar_error"
    REVISAR_CODIGO = "revisar_codigo"
    PREPARAR_MEJORA = "preparar_mejora"
    REANUDAR_PROPUESTA = "reanudar_propuesta"
    CREAR_SOLUCION_SIMPLE = "crear_solucion_simple"
    CREAR_TEST = "crear_test"
    ORGANIZAR_PROYECTO = "organizar_proyecto"
    CONTINUAR_PROYECTO = "continuar_proyecto"
    SIN_ACCION = "sin_accion"


@dataclass
class IniciativaDesarrollo:
    tipo: TipoIniciativaDesarrollo
    descripcion: str
    prioridad: float
    confianza: float
    origen: str
    datos: dict[str, Any] = field(default_factory=dict)
    puede_ejecutarse_sola: bool = False
    requiere_confirmacion: bool = False


@dataclass
class ResultadoDirectorDesarrollo:
    ok: bool
    iniciativa: IniciativaDesarrollo
    ejecutada: bool = False
    resultado: Any = None
    mensaje: str = ""
    error: str | None = None


class DirectorDesarrolloAutonomo:
    """
    Director ejecutivo del desarrollo interno de ATENAS.

    Decide qué trabajo de ingeniería conviene hacer sin esperar
    necesariamente una orden del usuario.

    Puede priorizar:
    - errores internos;
    - propuestas persistidas;
    - oportunidades de automejora;
    - creación de tests;
    - organización/refactorización;
    - soluciones sencillas.

    No ejecuta Python arbitrario ni shell. Toda modificación
    real sigue pasando por política, sandbox, tests, historial
    y rollback.
    """

    def __init__(
        self,
        desarrollo,
        supervisor_errores=None,
        severidad_minima: float = 0.55,
        confianza_minima: float = 0.70,
    ):
        self.desarrollo = desarrollo
        self.supervisor_errores = supervisor_errores
        self.trabajador_proyectos = None
        self.severidad_minima = max(0.0, min(float(severidad_minima), 1.0))
        self.confianza_minima = max(0.0, min(float(confianza_minima), 1.0))

    @staticmethod
    def _sin_accion(motivo: str) -> IniciativaDesarrollo:
        return IniciativaDesarrollo(
            tipo=TipoIniciativaDesarrollo.SIN_ACCION,
            descripcion=motivo,
            prioridad=0.0,
            confianza=1.0,
            origen="director_desarrollo",
        )

    def _candidato_error(self) -> IniciativaDesarrollo | None:
        if self.supervisor_errores is None:
            return None
        try:
            pendientes = self.supervisor_errores.pendientes_reparacion()
        except Exception:
            return None
        if not pendientes:
            return None

        evento = pendientes[-1]
        diagnostico = getattr(evento, "diagnostico", None)
        confianza = float(getattr(diagnostico, "confianza", 0.70) or 0.70)

        return IniciativaDesarrollo(
            tipo=TipoIniciativaDesarrollo.REPARAR_ERROR,
            descripcion="Existe un error interno diagnosticado y no resuelto.",
            prioridad=1.0,
            confianza=min(1.0, confianza),
            origen="supervisor_errores",
            datos={
                "evento_id": getattr(evento, "id", None),
                "tipo_error": getattr(evento, "tipo", None),
                "archivo": getattr(diagnostico, "archivo_principal", None),
            },
            puede_ejecutarse_sola=True,
        )

    def _candidato_propuesta(self) -> IniciativaDesarrollo | None:
        registro = getattr(self.desarrollo, "registro_propuestas", None)
        if registro is None:
            return None
        try:
            pendientes = registro.pendientes(limite=10)
        except Exception:
            return None
        if not pendientes:
            return None

        propuesta = max(
            pendientes,
            key=lambda item: (float(item.severidad), float(item.confianza)),
        )
        prioridad = min(
            0.95,
            float(propuesta.severidad) * 0.60
            + float(propuesta.confianza) * 0.40,
        )

        return IniciativaDesarrollo(
            tipo=TipoIniciativaDesarrollo.REANUDAR_PROPUESTA,
            descripcion="Existe una propuesta validada que debe revalidarse.",
            prioridad=prioridad,
            confianza=float(propuesta.confianza),
            origen="registro_propuestas",
            datos={
                "propuesta_id": propuesta.id,
                "archivo": propuesta.archivo,
                "tipo_hallazgo": propuesta.tipo_hallazgo,
                "riesgo": propuesta.riesgo,
            },
            puede_ejecutarse_sola=True,
            requiere_confirmacion=bool(propuesta.requiere_confirmacion),
        )

    def _candidato_proyecto_interno(
        self,
    ) -> IniciativaDesarrollo | None:

        gestor = getattr(
            self.desarrollo,
            "proyectos_internos",
            None,
        )

        if gestor is None:
            return None

        try:
            proyecto = gestor.proyecto_prioritario()
        except Exception:
            return None

        if proyecto is None:
            return None

        objetivo = gestor.siguiente_objetivo(
            proyecto.id
        )

        if objetivo is None:
            return None

        prioridad = min(
            0.98,
            float(proyecto.prioridad) * 0.65
            + float(objetivo.prioridad) * 0.35
            + 0.03,
        )

        return IniciativaDesarrollo(
            tipo=TipoIniciativaDesarrollo.CONTINUAR_PROYECTO,
            descripcion=(
                "Existe un proyecto interno activo "
                "con un objetivo ejecutable."
            ),
            prioridad=prioridad,
            confianza=0.95,
            origen="proyectos_internos",
            datos={
                "proyecto_id": proyecto.id,
                "proyecto": proyecto.nombre,
                "objetivo_id": objetivo.id,
                "objetivo": objetivo.descripcion,
            },
            puede_ejecutarse_sola=(
                proyecto.autonomia
                and not proyecto.requiere_confirmacion
            ),
            requiere_confirmacion=(
                proyecto.requiere_confirmacion
            ),
        )

    def _candidato_automejora(self) -> IniciativaDesarrollo | None:
        try:
            informe = self.desarrollo.analizar_mejoras()
        except Exception:
            return None
        if not informe.hallazgos:
            return None

        candidatos = [
            h for h in informe.hallazgos
            if h.severidad >= self.severidad_minima
            and h.confianza >= self.confianza_minima
        ]
        if not candidatos:
            return None

        hallazgo = max(
            candidatos,
            key=lambda h: (h.severidad, h.confianza),
        )

        tipo_hallazgo = hallazgo.tipo.value
        if tipo_hallazgo == "test_faltante":
            tipo = TipoIniciativaDesarrollo.CREAR_TEST
            descripcion = "Se detectó un módulo sin cobertura de test directa."
        elif tipo_hallazgo in {
            "funcion_grande",
            "clase_grande",
            "modulo_grande",
            "muchos_imports",
        }:
            tipo = TipoIniciativaDesarrollo.ORGANIZAR_PROYECTO
            descripcion = "Se detectó una oportunidad prioritaria de refactorización."
        else:
            tipo = TipoIniciativaDesarrollo.PREPARAR_MEJORA
            descripcion = "Se detectó una oportunidad de mejora verificable."

        riesgo = getattr(
            hallazgo.riesgo_estimado,
            "value",
            str(hallazgo.riesgo_estimado),
        )

        return IniciativaDesarrollo(
            tipo=tipo,
            descripcion=descripcion,
            prioridad=float(hallazgo.severidad),
            confianza=float(hallazgo.confianza),
            origen="automejora",
            datos={
                "archivo": hallazgo.archivo,
                "simbolo": hallazgo.simbolo,
                "tipo_hallazgo": tipo_hallazgo,
                "riesgo": riesgo,
            },
            puede_ejecutarse_sola=(
                riesgo == "bajo"
                and not hallazgo.requiere_confirmacion
            ),
            requiere_confirmacion=bool(hallazgo.requiere_confirmacion),
        )

    def decidir(self) -> IniciativaDesarrollo:
        candidatos = []

        for candidato in (
            self._candidato_error(),
            self._candidato_propuesta(),
            self._candidato_proyecto_interno(),
            self._candidato_automejora(),
        ):
            if candidato is not None:
                candidatos.append(candidato)

        if not candidatos:
            return self._sin_accion(
                "No existe trabajo de desarrollo prioritario en este momento."
            )

        candidatos.sort(
            key=lambda item: (item.prioridad, item.confianza),
            reverse=True,
        )
        return candidatos[0]

    def ejecutar(
        self,
        tests: list[str] | None = None,
        permitir_aplicacion: bool = False,
    ) -> ResultadoDirectorDesarrollo:
        iniciativa = self.decidir()

        if iniciativa.tipo == TipoIniciativaDesarrollo.SIN_ACCION:
            return ResultadoDirectorDesarrollo(
                ok=True,
                iniciativa=iniciativa,
                ejecutada=False,
                mensaje=iniciativa.descripcion,
            )

        if iniciativa.tipo == TipoIniciativaDesarrollo.REPARAR_ERROR:
            if self.supervisor_errores is None:
                return ResultadoDirectorDesarrollo(
                    ok=False,
                    iniciativa=iniciativa,
                    error="supervisor_no_disponible",
                    mensaje="Supervisor de errores no disponible.",
                )
            pendientes = self.supervisor_errores.pendientes_reparacion()
            if not pendientes:
                return ResultadoDirectorDesarrollo(
                    ok=True,
                    iniciativa=iniciativa,
                    ejecutada=False,
                    mensaje="El error ya no está pendiente.",
                )
            resultado = self.supervisor_errores.procesar_reparacion(
                evento=pendientes[-1],
                tests=tests,
            )
            return ResultadoDirectorDesarrollo(
                ok=True,
                iniciativa=iniciativa,
                ejecutada=resultado is not None,
                resultado=resultado,
                mensaje="Se procesó el error interno pendiente.",
            )

        if iniciativa.tipo == TipoIniciativaDesarrollo.REANUDAR_PROPUESTA:
            reanudador = getattr(self.desarrollo, "reanudador_propuestas", None)
            if reanudador is None:
                return ResultadoDirectorDesarrollo(
                    ok=False,
                    iniciativa=iniciativa,
                    error="reanudador_no_disponible",
                    mensaje="El reanudador de propuestas no está integrado.",
                )

            propuesta_id = iniciativa.datos["propuesta_id"]

            if permitir_aplicacion:
                resultado = reanudador.aplicar(
                    propuesta_id=propuesta_id,
                    tests=tests,
                    confirmada=False,
                )
            else:
                resultado = reanudador.preparar(
                    propuesta_id=propuesta_id,
                    tests=tests,
                )

            return ResultadoDirectorDesarrollo(
                ok=bool(resultado.ok),
                iniciativa=iniciativa,
                ejecutada=True,
                resultado=resultado,
                mensaje=resultado.mensaje,
                error=resultado.error,
            )

        if (
            iniciativa.tipo
            == TipoIniciativaDesarrollo.CONTINUAR_PROYECTO
        ):

            if not hasattr(
                self.desarrollo,
                "trabajar_siguiente_objetivo_interno",
            ):

                return ResultadoDirectorDesarrollo(
                    ok=False,
                    iniciativa=iniciativa,
                    ejecutada=False,
                    error=(
                        "trabajador_proyectos_no_disponible"
                    ),
                    mensaje=(
                        "El sistema de trabajo de "
                        "proyectos no está disponible."
                    ),
                )

            resultado = (
                self.desarrollo
                .trabajar_siguiente_objetivo_interno(
                    proyecto_id=(
                        iniciativa
                        .datos[
                            "proyecto_id"
                        ]
                    )
                )
            )

            return ResultadoDirectorDesarrollo(
                ok=bool(resultado.ok),
                iniciativa=iniciativa,
                ejecutada=True,
                resultado=resultado,
                mensaje=resultado.resumen,
                error=resultado.error,
            )

        resultado = self.desarrollo.ejecutar_ciclo_automejora(
            tests=tests,
            permitir_aplicacion=(
                permitir_aplicacion
                and iniciativa.puede_ejecutarse_sola
                and not iniciativa.requiere_confirmacion
            ),
        )

        return ResultadoDirectorDesarrollo(
            ok=bool(resultado.ok),
            iniciativa=iniciativa,
            ejecutada=True,
            resultado=resultado,
            mensaje=resultado.mensaje,
            error=resultado.error,
        )