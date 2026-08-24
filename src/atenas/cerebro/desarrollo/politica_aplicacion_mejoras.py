from __future__ import annotations

from dataclasses import dataclass

from .historial_cambios import (
    HistorialCambios,
)

from .parche import (
    GestorParches,
)

from .planificador_mejoras import (
    PropuestaMejora,
)

from .politica import (
    NivelRiesgo,
    PoliticaDesarrollo,
)


@dataclass
class DecisionAplicacionMejora:
    aplicar: bool

    motivo: str

    riesgo: NivelRiesgo

    requiere_confirmacion: bool

    lineas_modificadas: int = 0

    proporcion_cambio: float = 0.0


@dataclass
class ResultadoAplicacionMejora:
    ok: bool

    aplicada: bool

    decision: DecisionAplicacionMejora

    cambio_id: str | None = None

    mensaje: str = ""

    error: str | None = None


class PoliticaAplicacionMejoras:
    """
    Política específica para aplicar mejoras de calidad.

    Es deliberadamente más estricta que la autorreparación,
    porque una automejora modifica código que ya funcionaba.

    Una mejora solo puede ser autoaplicable cuando:

    - fue validada por PlanificadorMejoras;
    - superó sandbox;
    - superó tests;
    - superó VerificadorCambio;
    - el riesgo final es BAJO;
    - no requiere confirmación;
    - existe al menos un test ejecutado;
    - el parche es pequeño;
    - el archivo sigue permitido por PoliticaDesarrollo.

    Esta clase no aplica el cambio. Solo decide.
    """

    MAX_LINEAS_MODIFICADAS = 120
    MAX_PROPORCION_CAMBIO = 0.35
    MIN_LINEAS_ARCHIVO_PARA_PROPORCION = 40

    def __init__(
        self,
        politica: PoliticaDesarrollo,
    ):
        self.politica = politica

    # =========================================================
    # CONTAR CAMBIOS
    # =========================================================

    @staticmethod
    def _contar_lineas_modificadas(
        diff: str,
    ) -> int:

        total = 0

        for linea in (
            diff
            or ""
        ).splitlines():

            if linea.startswith(
                ("+++", "---")
            ):
                continue

            if (
                linea.startswith("+")
                or linea.startswith("-")
            ):
                total += 1

        return total

    # =========================================================
    # PROPORCIÓN
    # =========================================================

    @staticmethod
    def _proporcion_cambio(
        propuesta: PropuestaMejora,
        lineas_modificadas: int,
    ) -> float:

        if (
            propuesta.cambio
            is None
        ):
            return 1.0

        nuevo = (
            propuesta.cambio
            .contenido_nuevo
        )

        total_lineas = max(
            1,
            len(
                nuevo.splitlines()
            ),
        )

        # En archivos pequeños la proporción puede verse
        # artificialmente enorme aunque el parche solo cambie
        # unas pocas líneas. Ejemplo: 8 líneas modificadas en
        # un archivo de 10 líneas = 0.80.
        #
        # Por eso la proporción solo se considera como bloqueo
        # automático cuando el archivo tiene un tamaño mínimo.
        if (
            total_lineas
            < PoliticaAplicacionMejoras
            .MIN_LINEAS_ARCHIVO_PARA_PROPORCION
        ):
            return 0.0

        return min(
            1.0,
            lineas_modificadas
            / total_lineas,
        )

    # =========================================================
    # EVALUAR
    # =========================================================

    def evaluar(
        self,
        propuesta: PropuestaMejora,
    ) -> DecisionAplicacionMejora:

        riesgo = (
            propuesta.verificacion.riesgo
            if propuesta.verificacion
            is not None
            else NivelRiesgo.CRITICO
        )

        if (
            not propuesta.ok
            or propuesta.cambio is None
        ):

            return DecisionAplicacionMejora(
                aplicar=False,
                motivo=(
                    "La propuesta no está validada."
                ),
                riesgo=riesgo,
                requiere_confirmacion=True,
            )

        evaluacion_archivo = (
            self.politica
            .evaluar_modificacion(
                propuesta.cambio.archivo
            )
        )

        if not evaluacion_archivo.permitido:

            return DecisionAplicacionMejora(
                aplicar=False,
                motivo=(
                    "La política general bloqueó "
                    "el archivo: "
                    f"{evaluacion_archivo.motivo}"
                ),
                riesgo=(
                    evaluacion_archivo.riesgo
                ),
                requiere_confirmacion=True,
            )

        if (
            propuesta.sandbox is None
            or not propuesta.sandbox.ok
        ):

            return DecisionAplicacionMejora(
                aplicar=False,
                motivo=(
                    "La mejora no superó el sandbox."
                ),
                riesgo=riesgo,
                requiere_confirmacion=True,
            )

        if (
            propuesta.verificacion is None
            or not propuesta.verificacion.valido
        ):

            return DecisionAplicacionMejora(
                aplicar=False,
                motivo=(
                    "La mejora no superó "
                    "el verificador."
                ),
                riesgo=riesgo,
                requiere_confirmacion=True,
            )

        if (
            propuesta.verificacion.riesgo
            != NivelRiesgo.BAJO
        ):

            return DecisionAplicacionMejora(
                aplicar=False,
                motivo=(
                    "Las automejoras automáticas "
                    "solo se permiten con riesgo bajo."
                ),
                riesgo=(
                    propuesta.verificacion.riesgo
                ),
                requiere_confirmacion=True,
            )

        if (
            propuesta.verificacion
            .requiere_confirmacion
        ):

            return DecisionAplicacionMejora(
                aplicar=False,
                motivo=(
                    "El verificador exige "
                    "confirmación."
                ),
                riesgo=(
                    propuesta.verificacion.riesgo
                ),
                requiere_confirmacion=True,
            )

        # =====================================================
        # EXIGIR TESTS
        # =====================================================

        pruebas = (
            propuesta.sandbox.pruebas
        )

        if not pruebas:

            return DecisionAplicacionMejora(
                aplicar=False,
                motivo=(
                    "Una automejora no puede "
                    "autoaplicarse sin tests."
                ),
                riesgo=(
                    propuesta.verificacion.riesgo
                ),
                requiere_confirmacion=True,
            )

        if any(
            not prueba.ok
            for prueba in pruebas
        ):

            return DecisionAplicacionMejora(
                aplicar=False,
                motivo=(
                    "Uno o más tests fallaron."
                ),
                riesgo=(
                    propuesta.verificacion.riesgo
                ),
                requiere_confirmacion=True,
            )

        # =====================================================
        # TAMAÑO DEL PARCHE
        # =====================================================

        lineas_modificadas = (
            self._contar_lineas_modificadas(
                propuesta.cambio.diff
            )
        )

        proporcion = (
            self._proporcion_cambio(
                propuesta,
                lineas_modificadas,
            )
        )

        if (
            lineas_modificadas
            > self.MAX_LINEAS_MODIFICADAS
        ):

            return DecisionAplicacionMejora(
                aplicar=False,
                motivo=(
                    "El parche modifica demasiadas "
                    "líneas para una automejora "
                    "automática."
                ),
                riesgo=(
                    propuesta.verificacion.riesgo
                ),
                requiere_confirmacion=True,
                lineas_modificadas=(
                    lineas_modificadas
                ),
                proporcion_cambio=(
                    proporcion
                ),
            )

        if (
            proporcion
            > self.MAX_PROPORCION_CAMBIO
        ):

            return DecisionAplicacionMejora(
                aplicar=False,
                motivo=(
                    "El parche cambia una proporción "
                    "demasiado grande del archivo."
                ),
                riesgo=(
                    propuesta.verificacion.riesgo
                ),
                requiere_confirmacion=True,
                lineas_modificadas=(
                    lineas_modificadas
                ),
                proporcion_cambio=(
                    proporcion
                ),
            )

        return DecisionAplicacionMejora(
            aplicar=True,
            motivo=(
                "La mejora es pequeña, de riesgo bajo, "
                "superó sandbox, tests y verificación."
            ),
            riesgo=(
                propuesta.verificacion.riesgo
            ),
            requiere_confirmacion=False,
            lineas_modificadas=(
                lineas_modificadas
            ),
            proporcion_cambio=(
                proporcion
            ),
        )


class AplicadorMejoras:
    """
    Aplica una PropuestaMejora validada al proyecto real.

    Antes de modificar:

    - vuelve a comprobar la política;
    - vuelve a validar el hash del archivo;
    - registra el contenido original en HistorialCambios.

    Esto permite rollback posterior.
    """

    def __init__(
        self,
        politica_aplicacion: PoliticaAplicacionMejoras,
        gestor_parches: GestorParches,
        historial: HistorialCambios,
    ):
        self.politica_aplicacion = (
            politica_aplicacion
        )

        self.gestor_parches = (
            gestor_parches
        )

        self.historial = historial

    # =========================================================
    # APLICAR
    # =========================================================

    def aplicar(
        self,
        propuesta: PropuestaMejora,
    ) -> ResultadoAplicacionMejora:

        decision = (
            self.politica_aplicacion
            .evaluar(
                propuesta
            )
        )

        if (
            not decision.aplicar
            or propuesta.cambio is None
            or propuesta.verificacion is None
        ):

            return ResultadoAplicacionMejora(
                ok=True,
                aplicada=False,
                decision=decision,
                mensaje=(
                    "La mejora no fue aplicada: "
                    f"{decision.motivo}"
                ),
            )

        # =====================================================
        # LEER ORIGINAL ACTUAL
        # =====================================================

        ruta = (
            self.gestor_parches.raiz
            / propuesta.cambio.archivo
        ).resolve()

        try:

            contenido_original = (
                ruta.read_text(
                    encoding="utf-8"
                )
            )

        except OSError as error:

            return ResultadoAplicacionMejora(
                ok=False,
                aplicada=False,
                decision=decision,
                mensaje=(
                    "No fue posible leer "
                    "el archivo original."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        # =====================================================
        # HISTORIAL / SNAPSHOT
        # =====================================================

        pruebas_json = {
            "tipo": "automejora",

            "sandbox_ok": bool(
                propuesta.sandbox
                and propuesta.sandbox.ok
            ),

            "tests": [
                {
                    "ok": prueba.ok,
                    "comando": prueba.comando,
                    "returncode": prueba.returncode,
                    "duracion": prueba.duracion,
                }
                for prueba
                in (
                    propuesta.sandbox.pruebas
                    if propuesta.sandbox
                    else []
                )
            ],
        }

        cambio_id = (
            self.historial
            .registrar_propuesta(
                cambio=(
                    propuesta.cambio
                ),
                verificacion=(
                    propuesta.verificacion
                ),
                contenido_original=(
                    contenido_original
                ),
                pruebas=(
                    pruebas_json
                ),
            )
        )

        # =====================================================
        # APLICAR
        # =====================================================

        aplicacion = (
            self.gestor_parches
            .aplicar(
                propuesta.cambio
            )
        )

        if not aplicacion.ok:

            try:
                self.historial.marcar_fallido(
                    cambio_id
                )
            except Exception:
                pass

            return ResultadoAplicacionMejora(
                ok=False,
                aplicada=False,
                decision=decision,
                cambio_id=cambio_id,
                mensaje=(
                    "Falló la aplicación de "
                    "la mejora."
                ),
                error=(
                    aplicacion.mensaje
                ),
            )

        self.historial.marcar_aplicado(
            cambio_id=cambio_id,
            hash_despues=(
                aplicacion.hash_despues
                or ""
            ),
        )

        propuesta.aplicada = True

        return ResultadoAplicacionMejora(
            ok=True,
            aplicada=True,
            decision=decision,
            cambio_id=cambio_id,
            mensaje=(
                "Mejora aplicada correctamente "
                "con snapshot para rollback."
            ),
        )