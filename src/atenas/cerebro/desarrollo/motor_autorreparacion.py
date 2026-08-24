from __future__ import annotations

import time

from dataclasses import dataclass
from typing import Any

from .politica import (
    NivelRiesgo,
)

from .sistema_desarrollo import (
    SistemaDesarrolloAtenas,
)


@dataclass
class DecisionAutorreparacion:
    intentar: bool

    motivo: str

    confianza: float

    categoria: str | None = None

    archivo: str | None = None

    autoaplicar_bajo_riesgo: bool = False


@dataclass
class ResultadoMotorAutorreparacion:
    procesado: bool

    decision: DecisionAutorreparacion

    resultado_reparacion: Any = None

    error: str | None = None


class MotorAutorreparacion:
    """
    Decide cuándo ATENAS debe intentar reparar
    automáticamente un error interno.

    IMPORTANTE:

    Este motor NO modifica archivos directamente.

    Toda reparación pasa por:

        DiagnosticoCodigo
        -> ProgramadorAtenas
        -> GestorParches
        -> SandboxCodigo
        -> Tests
        -> VerificadorCambio
        -> Política
        -> aplicación opcional
    """

    # =========================================================
    # CATEGORÍAS QUE PUEDEN SER REPARABLES
    # =========================================================

    CATEGORIAS_REPARABLES = {
        "import",
        "import_circular",
        "atributo",
        "tipo",
        "nombre",
        "sintaxis",
        "test",
    }

    # =========================================================
    # CATEGORÍAS QUE PUEDEN INICIAR REPARACIÓN AUTOMÁTICA
    # =========================================================

    CATEGORIAS_AUTOMATICAS = {
        "import",
        "import_circular",
        "atributo",
        "nombre",
        "test",
    }

    # =========================================================
    # COMPONENTES QUE NO DEBEN AUTORREPARARSE RECURSIVAMENTE
    # =========================================================

    COMPONENTES_BLOQUEADOS = {
        "supervisor",
        "autorreparacion",
        "desarrollo",
        "sandbox",
        "verificador",
        "rollback",
        "politica",
    }

    # =========================================================
    # ARCHIVOS DEL SISTEMA DE SEGURIDAD
    # =========================================================

    ARCHIVOS_BLOQUEADOS = {
        "src/atenas/cerebro/desarrollo/politica.py",
        "src/atenas/cerebro/desarrollo/sandbox.py",
        "src/atenas/cerebro/desarrollo/verificador.py",
        "src/atenas/cerebro/desarrollo/rollback.py",
        "src/atenas/cerebro/desarrollo/motor_autorreparacion.py",
    }

    def __init__(
        self,
        desarrollo: SistemaDesarrolloAtenas | None,
        max_intentos_por_error: int = 2,
        cooldown_segundos: float = 60.0,
        autoaplicar_bajo_riesgo: bool = True,
    ):
        self.desarrollo = desarrollo

        self.max_intentos_por_error = max(
            1,
            int(
                max_intentos_por_error
            ),
        )

        self.cooldown_segundos = max(
            0.0,
            float(
                cooldown_segundos
            ),
        )

        self.autoaplicar_bajo_riesgo = bool(
            autoaplicar_bajo_riesgo
        )

        # Firma error -> cantidad de intentos
        self._intentos: dict[
            str,
            int
        ] = {}

        # Firma error -> timestamp último intento
        self._ultimo_intento: dict[
            str,
            float
        ] = {}

        self._procesando = False

    # =========================================================
    # FIRMA
    # =========================================================

    @staticmethod
    def _firma_evento(
        evento,
    ) -> str:

        diagnostico = getattr(
            evento,
            "diagnostico",
            None,
        )

        categoria = getattr(
            diagnostico,
            "categoria",
            "",
        )

        archivo = getattr(
            diagnostico,
            "archivo_principal",
            "",
        )

        linea = getattr(
            diagnostico,
            "linea_principal",
            "",
        )

        tipo = getattr(
            evento,
            "tipo",
            "",
        )

        mensaje = getattr(
            evento,
            "mensaje",
            "",
        )

        return (
            f"{tipo}|"
            f"{categoria}|"
            f"{archivo}|"
            f"{linea}|"
            f"{mensaje}"
        )

    # =========================================================
    # NORMALIZAR RUTA
    # =========================================================

    @staticmethod
    def _normalizar_ruta(
        ruta: str | None,
    ) -> str:

        return (
            ruta
            or ""
        ).replace(
            "\\",
            "/",
        ).strip()

    # =========================================================
    # ¿ARCHIVO DE ATENAS?
    # =========================================================

    def _es_archivo_propio(
        self,
        archivo: str | None,
    ) -> bool:

        archivo = (
            self._normalizar_ruta(
                archivo
            )
        )

        if not archivo:
            return False

        return (
            archivo.startswith(
                "src/atenas/"
            )
            or archivo.startswith(
                "tests/"
            )
            or archivo in {
                "main.py",
                "app.py",
            }
        )

    # =========================================================
    # ¿ARCHIVO BLOQUEADO?
    # =========================================================

    def _archivo_bloqueado(
        self,
        archivo: str | None,
    ) -> bool:

        archivo = (
            self._normalizar_ruta(
                archivo
            )
        )

        return (
            archivo
            in self.ARCHIVOS_BLOQUEADOS
        )

    # =========================================================
    # COOLDOWN
    # =========================================================

    def _en_cooldown(
        self,
        firma: str,
    ) -> bool:

        ultimo = (
            self._ultimo_intento
            .get(
                firma
            )
        )

        if ultimo is None:
            return False

        transcurrido = (
            time.monotonic()
            - ultimo
        )

        return (
            transcurrido
            < self.cooldown_segundos
        )

    # =========================================================
    # EVALUAR
    # =========================================================

    def evaluar(
        self,
        evento,
    ) -> DecisionAutorreparacion:

        # =====================================================
        # SISTEMA DISPONIBLE
        # =====================================================

        if self.desarrollo is None:

            return DecisionAutorreparacion(
                intentar=False,
                motivo=(
                    "El sistema de desarrollo "
                    "no está disponible."
                ),
                confianza=1.0,
            )

        # =====================================================
        # EVITAR RECURSIÓN
        # =====================================================

        if self._procesando:

            return DecisionAutorreparacion(
                intentar=False,
                motivo=(
                    "Ya hay una reparación "
                    "en ejecución."
                ),
                confianza=1.0,
            )

        # =====================================================
        # YA RESUELTO
        # =====================================================

        if getattr(
            evento,
            "resuelto",
            False,
        ):

            return DecisionAutorreparacion(
                intentar=False,
                motivo=(
                    "El error ya fue marcado "
                    "como resuelto."
                ),
                confianza=1.0,
            )

        # =====================================================
        # COMPONENTE
        # =====================================================

        componente = (
            getattr(
                evento,
                "componente",
                None,
            )
            or ""
        ).lower()

        if componente in (
            self.COMPONENTES_BLOQUEADOS
        ):

            return DecisionAutorreparacion(
                intentar=False,
                motivo=(
                    "El error pertenece a un "
                    "componente protegido del "
                    "sistema de reparación."
                ),
                confianza=1.0,
            )

        # =====================================================
        # DIAGNÓSTICO
        # =====================================================

        diagnostico = getattr(
            evento,
            "diagnostico",
            None,
        )

        if diagnostico is None:

            return DecisionAutorreparacion(
                intentar=False,
                motivo=(
                    "El error todavía no tiene "
                    "un diagnóstico válido."
                ),
                confianza=0.95,
            )

        categoria = getattr(
            diagnostico,
            "categoria",
            None,
        )

        archivo = (
            self._normalizar_ruta(
                getattr(
                    diagnostico,
                    "archivo_principal",
                    None,
                )
            )
        )

        # =====================================================
        # CATEGORÍA
        # =====================================================

        if (
            categoria
            not in self.CATEGORIAS_REPARABLES
        ):

            return DecisionAutorreparacion(
                intentar=False,

                motivo=(
                    "La categoría del error no "
                    "está habilitada para "
                    "autorreparación."
                ),

                confianza=0.95,

                categoria=categoria,

                archivo=(
                    archivo
                    or None
                ),
            )

        # =====================================================
        # ARCHIVO
        # =====================================================

        if not self._es_archivo_propio(
            archivo
        ):

            return DecisionAutorreparacion(
                intentar=False,

                motivo=(
                    "El error no apunta a un "
                    "archivo del proyecto ATENAS."
                ),

                confianza=0.95,

                categoria=categoria,

                archivo=(
                    archivo
                    or None
                ),
            )

        # =====================================================
        # PROTECCIÓN
        # =====================================================

        if self._archivo_bloqueado(
            archivo
        ):

            return DecisionAutorreparacion(
                intentar=False,

                motivo=(
                    "El archivo pertenece al "
                    "núcleo protegido del sistema "
                    "de autorreparación."
                ),

                confianza=1.0,

                categoria=categoria,
                archivo=archivo,
            )

        # =====================================================
        # POLÍTICA DEL PROYECTO
        # =====================================================

        evaluacion_politica = (
            self.desarrollo
            .politica
            .evaluar_modificacion(
                archivo
            )
        )

        if not evaluacion_politica.permitido:

            return DecisionAutorreparacion(
                intentar=False,

                motivo=(
                    "La política de desarrollo "
                    "bloqueó el archivo: "
                    f"{evaluacion_politica.motivo}"
                ),

                confianza=1.0,

                categoria=categoria,
                archivo=archivo,
            )

        # =====================================================
        # FIRMA / INTENTOS
        # =====================================================

        firma = (
            self._firma_evento(
                evento
            )
        )

        intentos = (
            self._intentos
            .get(
                firma,
                0,
            )
        )

        if (
            intentos
            >= self.max_intentos_por_error
        ):

            return DecisionAutorreparacion(
                intentar=False,

                motivo=(
                    "Se alcanzó el número máximo "
                    "de intentos para este error."
                ),

                confianza=1.0,

                categoria=categoria,
                archivo=archivo,
            )

        # =====================================================
        # COOLDOWN
        # =====================================================

        if self._en_cooldown(
            firma
        ):

            return DecisionAutorreparacion(
                intentar=False,

                motivo=(
                    "El mismo error fue procesado "
                    "recientemente."
                ),

                confianza=1.0,

                categoria=categoria,
                archivo=archivo,
            )

        # =====================================================
        # DECIDIR AUTOMATIZACIÓN
        # =====================================================

        categoria_automatica = (
            categoria
            in self.CATEGORIAS_AUTOMATICAS
        )

        # No confundimos:
        #
        # iniciar reparación
        #
        # con:
        #
        # aplicar automáticamente.
        #
        # El cambio final todavía será revisado
        # por VerificadorCambio.

        autoaplicar = (
            self.autoaplicar_bajo_riesgo
            and categoria_automatica
        )

        confianza = 0.75

        confianza_diagnostico = float(
            getattr(
                diagnostico,
                "confianza",
                0.5,
            )
            or 0.5
        )

        confianza += (
            confianza_diagnostico
            * 0.20
        )

        confianza = min(
            confianza,
            0.98,
        )

        return DecisionAutorreparacion(
            intentar=True,

            motivo=(
                "El error pertenece al proyecto, "
                "tiene una categoría reparable y "
                "puede evaluarse de forma aislada "
                "en el sandbox."
            ),

            confianza=confianza,

            categoria=categoria,
            archivo=archivo,

            autoaplicar_bajo_riesgo=(
                autoaplicar
            ),
        )

    # =========================================================
    # PROCESAR
    # =========================================================

    def procesar(
        self,
        evento,
        tests: list[str] | None = None,
    ) -> ResultadoMotorAutorreparacion:

        decision = (
            self.evaluar(
                evento
            )
        )

        if not decision.intentar:

            return ResultadoMotorAutorreparacion(
                procesado=False,

                decision=decision,

                resultado_reparacion=None,
            )

        firma = (
            self._firma_evento(
                evento
            )
        )

        self._intentos[
            firma
        ] = (
            self._intentos.get(
                firma,
                0,
            )
            + 1
        )

        self._ultimo_intento[
            firma
        ] = time.monotonic()

        self._procesando = True

        try:

            resultado = (
                self.desarrollo
                .reparar_error(
                    traceback_texto=(
                        evento.traceback
                    ),

                    tests=tests,

                    aplicar_bajo_riesgo=(
                        decision
                        .autoaplicar_bajo_riesgo
                    ),
                )
            )

            aplicado = bool(
                getattr(
                    resultado,
                    "aplicado",
                    False,
                )
            )

            if isinstance(
                resultado,
                dict,
            ):

                aplicado = bool(
                    resultado.get(
                        "aplicado",
                        False,
                    )
                )

            evento.reparacion_iniciada = True

            evento.resultado_reparacion = (
                resultado
            )

            evento.resuelto = (
                aplicado
            )

            return ResultadoMotorAutorreparacion(
                procesado=True,

                decision=decision,

                resultado_reparacion=(
                    resultado
                ),
            )

        except Exception as error:

            return ResultadoMotorAutorreparacion(
                procesado=True,

                decision=decision,

                resultado_reparacion=None,

                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        finally:

            self._procesando = False

    # =========================================================
    # INTENTOS
    # =========================================================

    def intentos_para(
        self,
        evento,
    ) -> int:

        firma = (
            self._firma_evento(
                evento
            )
        )

        return (
            self._intentos
            .get(
                firma,
                0,
            )
        )