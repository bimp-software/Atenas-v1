from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .registro_propuestas import (
    EstadoPropuesta,
    PropuestaPersistida,
    RegistroPropuestasMejora,
)


@dataclass
class ResultadoReanudacionPropuesta:
    ok: bool

    propuesta_id: str

    estado: str

    aplicable: bool = False

    cambio: Any = None

    sandbox: Any = None

    verificacion: Any = None

    aplicacion: Any = None

    mensaje: str = ""

    error: str | None = None


class ReanudadorPropuestas:
    """
    Reabre una propuesta persistida después de reiniciar ATENAS.

    Nunca confía ciegamente en una propuesta antigua:

    1. comprueba que siga VALIDADA;
    2. lee el archivo actual;
    3. compara el hash con el archivo usado al generar la propuesta;
    4. reconstruye CambioCodigo;
    5. vuelve a ejecutar sandbox + tests;
    6. vuelve a ejecutar VerificadorCambio;
    7. solo después permite aplicar.

    Si el archivo cambió, la propuesta se marca OBSOLETA.
    """

    def __init__(
        self,
        raiz_proyecto: str | Path,
        registro: RegistroPropuestasMejora,
        inspector,
        gestor_parches,
        sandbox,
        verificador,
        politica_aplicacion,
        aplicador,
    ):
        self.raiz = Path(
            raiz_proyecto
        ).resolve()

        self.registro = registro
        self.inspector = inspector
        self.gestor_parches = (
            gestor_parches
        )
        self.sandbox = sandbox
        self.verificador = (
            verificador
        )
        self.politica_aplicacion = (
            politica_aplicacion
        )
        self.aplicador = aplicador

    # =========================================================
    # PREPARAR
    # =========================================================

    def preparar(
        self,
        propuesta_id: str,
        tests: list[str] | None = None,
    ) -> ResultadoReanudacionPropuesta:

        propuesta = (
            self.registro.obtener(
                propuesta_id
            )
        )

        if propuesta is None:

            return ResultadoReanudacionPropuesta(
                ok=False,
                propuesta_id=propuesta_id,
                estado="no_encontrada",
                mensaje=(
                    "La propuesta no existe."
                ),
                error="propuesta_no_encontrada",
            )

        if (
            propuesta.estado
            != EstadoPropuesta.VALIDADA
        ):

            return ResultadoReanudacionPropuesta(
                ok=False,
                propuesta_id=propuesta_id,
                estado=(
                    propuesta.estado.value
                ),
                mensaje=(
                    "La propuesta ya no está "
                    "en estado VALIDADA."
                ),
                error="estado_no_aplicable",
            )

        lectura = (
            self.inspector
            .leer_archivo(
                propuesta.archivo
            )
        )

        if not lectura.get(
            "ok",
            False,
        ):

            return ResultadoReanudacionPropuesta(
                ok=False,
                propuesta_id=propuesta_id,
                estado="fallo_lectura",
                mensaje=(
                    "No fue posible leer "
                    "el archivo actual."
                ),
                error=str(
                    lectura.get(
                        "error"
                    )
                ),
            )

        contenido_actual = (
            lectura[
                "contenido"
            ]
        )

        hash_actual = (
            self.registro
            .hash_contenido(
                contenido_actual
            )
        )

        # Las propuestas antiguas, creadas antes de incorporar
        # hash_original, no se aplican automáticamente.
        if not propuesta.hash_original:

            return ResultadoReanudacionPropuesta(
                ok=True,
                propuesta_id=propuesta_id,
                estado="requiere_regeneracion",
                aplicable=False,
                mensaje=(
                    "La propuesta fue creada por "
                    "una versión anterior y no posee "
                    "hash_original. Debe regenerarse."
                ),
            )

        if (
            hash_actual
            != propuesta.hash_original
        ):

            self.registro.marcar_obsoleta(
                propuesta_id
            )

            return ResultadoReanudacionPropuesta(
                ok=True,
                propuesta_id=propuesta_id,
                estado="obsoleta",
                aplicable=False,
                mensaje=(
                    "El archivo cambió desde que "
                    "la propuesta fue generada. "
                    "Se marcó como obsoleta."
                ),
            )

        # =====================================================
        # RECONSTRUIR CAMBIO
        # =====================================================

        try:

            cambio = (
                self.gestor_parches
                .preparar_cambio(
                    archivo=(
                        propuesta.archivo
                    ),
                    contenido_original=(
                        contenido_actual
                    ),
                    contenido_nuevo=(
                        propuesta
                        .contenido_nuevo
                    ),
                    razon=(
                        propuesta.razon
                    ),
                )
            )

        except Exception as error:

            self.registro.marcar_fallida(
                propuesta_id
            )

            return ResultadoReanudacionPropuesta(
                ok=False,
                propuesta_id=propuesta_id,
                estado="fallo_reconstruccion",
                mensaje=(
                    "No fue posible reconstruir "
                    "el cambio."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        # =====================================================
        # SANDBOX
        # =====================================================

        try:

            entorno = (
                self.sandbox.crear()
            )

            resultado_sandbox = (
                self.sandbox
                .probar_cambio(
                    entorno=entorno,
                    cambio=cambio,
                    tests=tests,
                )
            )

        except Exception as error:

            return ResultadoReanudacionPropuesta(
                ok=False,
                propuesta_id=propuesta_id,
                estado="fallo_sandbox",
                cambio=cambio,
                mensaje=(
                    "Falló la revalidación "
                    "en sandbox."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        if not resultado_sandbox.ok:

            return ResultadoReanudacionPropuesta(
                ok=True,
                propuesta_id=propuesta_id,
                estado="rechazada_sandbox",
                aplicable=False,
                cambio=cambio,
                sandbox=(
                    resultado_sandbox
                ),
                mensaje=(
                    "La propuesta persistida "
                    "ya no supera el sandbox."
                ),
            )

        # =====================================================
        # VERIFICADOR
        # =====================================================

        try:

            verificacion = (
                self.verificador
                .verificar(
                    cambio=cambio,
                    resultado_sandbox=(
                        resultado_sandbox
                    ),
                )
            )

        except Exception as error:

            return ResultadoReanudacionPropuesta(
                ok=False,
                propuesta_id=propuesta_id,
                estado="fallo_verificacion",
                cambio=cambio,
                sandbox=(
                    resultado_sandbox
                ),
                mensaje=(
                    "Falló la revalidación "
                    "de seguridad."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        if not verificacion.valido:

            return ResultadoReanudacionPropuesta(
                ok=True,
                propuesta_id=propuesta_id,
                estado="rechazada_verificador",
                aplicable=False,
                cambio=cambio,
                sandbox=(
                    resultado_sandbox
                ),
                verificacion=verificacion,
                mensaje=(
                    "La propuesta persistida "
                    "fue rechazada por el verificador."
                ),
            )

        return ResultadoReanudacionPropuesta(
            ok=True,
            propuesta_id=propuesta_id,
            estado="revalidada",
            aplicable=True,
            cambio=cambio,
            sandbox=(
                resultado_sandbox
            ),
            verificacion=verificacion,
            mensaje=(
                "La propuesta fue reconstruida "
                "y revalidada correctamente."
            ),
        )

    # =========================================================
    # APLICAR REVALIDADA
    # =========================================================

    def aplicar(
        self,
        propuesta_id: str,
        tests: list[str] | None = None,
        confirmada: bool = False,
    ) -> ResultadoReanudacionPropuesta:

        preparado = self.preparar(
            propuesta_id,
            tests=tests,
        )

        if (
            not preparado.ok
            or not preparado.aplicable
        ):

            return preparado

        propuesta_persistida = (
            self.registro.obtener(
                propuesta_id
            )
        )

        assert (
            propuesta_persistida
            is not None
        )

        # Construimos un objeto mínimo compatible con
        # PoliticaAplicacionMejoras y AplicadorMejoras.
        propuesta_runtime = type(
            "PropuestaRuntime",
            (),
            {},
        )()

        propuesta_runtime.ok = True
        propuesta_runtime.cambio = (
            preparado.cambio
        )
        propuesta_runtime.sandbox = (
            preparado.sandbox
        )
        propuesta_runtime.verificacion = (
            preparado.verificacion
        )
        propuesta_runtime.aplicada = False

        decision = (
            self.politica_aplicacion
            .evaluar(
                propuesta_runtime
            )
        )

        if (
            decision
            .requiere_confirmacion
            and not confirmada
        ):

            return ResultadoReanudacionPropuesta(
                ok=True,
                propuesta_id=propuesta_id,
                estado="requiere_confirmacion",
                aplicable=False,
                cambio=(
                    preparado.cambio
                ),
                sandbox=(
                    preparado.sandbox
                ),
                verificacion=(
                    preparado.verificacion
                ),
                mensaje=(
                    decision.motivo
                ),
            )

        if not decision.aplicar:

            return ResultadoReanudacionPropuesta(
                ok=True,
                propuesta_id=propuesta_id,
                estado="politica_bloquea",
                aplicable=False,
                cambio=(
                    preparado.cambio
                ),
                sandbox=(
                    preparado.sandbox
                ),
                verificacion=(
                    preparado.verificacion
                ),
                mensaje=(
                    decision.motivo
                ),
            )

        try:

            aplicacion = (
                self.aplicador
                .aplicar(
                    propuesta_runtime
                )
            )

        except Exception as error:

            self.registro.marcar_fallida(
                propuesta_id
            )

            return ResultadoReanudacionPropuesta(
                ok=False,
                propuesta_id=propuesta_id,
                estado="fallo_aplicacion",
                aplicable=False,
                cambio=(
                    preparado.cambio
                ),
                sandbox=(
                    preparado.sandbox
                ),
                verificacion=(
                    preparado.verificacion
                ),
                mensaje=(
                    "Falló la aplicación "
                    "de la propuesta reanudada."
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        if (
            aplicacion.ok
            and aplicacion.aplicada
            and aplicacion.cambio_id
        ):

            self.registro.marcar_aplicada(
                propuesta_id,
                cambio_id=(
                    aplicacion.cambio_id
                ),
            )

            return ResultadoReanudacionPropuesta(
                ok=True,
                propuesta_id=propuesta_id,
                estado="aplicada",
                aplicable=False,
                cambio=(
                    preparado.cambio
                ),
                sandbox=(
                    preparado.sandbox
                ),
                verificacion=(
                    preparado.verificacion
                ),
                aplicacion=aplicacion,
                mensaje=(
                    "Propuesta persistida "
                    "aplicada correctamente."
                ),
            )

        return ResultadoReanudacionPropuesta(
            ok=bool(
                aplicacion.ok
            ),
            propuesta_id=propuesta_id,
            estado="no_aplicada",
            aplicable=False,
            cambio=(
                preparado.cambio
            ),
            sandbox=(
                preparado.sandbox
            ),
            verificacion=(
                preparado.verificacion
            ),
            aplicacion=aplicacion,
            mensaje=(
                aplicacion.mensaje
            ),
            error=(
                aplicacion.error
            ),
        )