from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .diagnostico import (
    DiagnosticoCodigo,
    DiagnosticoError,
)

from .historial_cambios import (
    HistorialCambios,
)

from .inspector_codigo import (
    InspectorCodigo,
)

from .parche import (
    GestorParches,
    CambioCodigo,
)

from .politica import (
    PoliticaDesarrollo,
)

from .programador import (
    ProgramadorAtenas,
)

from .sandbox import (
    SandboxCodigo,
    ResultadoSandbox,
)

from .verificador import (
    VerificadorCambio,
    ResultadoVerificacion,
)


@dataclass
class ResultadoAutorreparacion:
    ok: bool

    estado: str

    diagnostico: DiagnosticoError | None = None

    cambio: CambioCodigo | None = None

    sandbox: ResultadoSandbox | None = None

    verificacion: ResultadoVerificacion | None = None

    cambio_id: str | None = None

    aplicado: bool = False

    requiere_confirmacion: bool = False

    mensajes: list[str] = field(
        default_factory=list
    )

    error: str | None = None


class Autorreparacion:

    MAX_INTENTOS = 3

    def __init__(
        self,
        raiz_proyecto: str | Path,
        inspector: InspectorCodigo,
        diagnostico: DiagnosticoCodigo,
        programador: ProgramadorAtenas,
        sandbox: SandboxCodigo,
        verificador: VerificadorCambio,
        politica: PoliticaDesarrollo,
        historial: HistorialCambios,
    ):
        self.raiz = Path(
            raiz_proyecto
        ).resolve()

        self.inspector = inspector
        self.diagnostico = diagnostico
        self.programador = programador
        self.sandbox = sandbox
        self.verificador = verificador
        self.politica = politica
        self.historial = historial

    # =========================================================
    # PROCESAR ERROR
    # =========================================================

    def reparar(
        self,
        traceback_texto: str,
        tests: list[str] | None = None,
        aplicar_bajo_riesgo: bool = True,
    ) -> ResultadoAutorreparacion:

        mensajes = []

        # =====================================================
        # 1. DIAGNÓSTICO
        # =====================================================

        diagnostico = (
            self.diagnostico
            .analizar(
                traceback_texto
            )
        )

        mensajes.append(
            (
                "[ATENAS][DIAGNOSTICO] "
                f"{diagnostico.resumen}"
            )
        )

        # =====================================================
        # 2. PROGRAMADOR
        # =====================================================

        propuesta = (
            self.programador
            .proponer_correccion(
                diagnostico
            )
        )

        if (
            not propuesta.ok
            or propuesta.cambio is None
        ):

            return ResultadoAutorreparacion(
                ok=False,
                estado="sin_propuesta",
                diagnostico=diagnostico,
                mensajes=mensajes,
                error=(
                    propuesta.error
                    or propuesta.mensaje
                ),
            )

        cambio = (
            propuesta.cambio
        )

        mensajes.append(
            (
                "[ATENAS][PROGRAMADOR] "
                "Corrección propuesta."
            )
        )

        # =====================================================
        # 3. SANDBOX
        # =====================================================

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

        if not resultado_sandbox.ok:

            mensajes.append(
                (
                    "[ATENAS][SANDBOX] "
                    "La corrección falló."
                )
            )

            return ResultadoAutorreparacion(
                ok=False,
                estado="fallo_sandbox",

                diagnostico=diagnostico,
                cambio=cambio,
                sandbox=resultado_sandbox,

                mensajes=mensajes,
            )

        mensajes.append(
            (
                "[ATENAS][SANDBOX] "
                "Corrección validada."
            )
        )

        # =====================================================
        # 4. VERIFICAR
        # =====================================================

        verificacion = (
            self.verificador
            .verificar(
                cambio=cambio,
                resultado_sandbox=(
                    resultado_sandbox
                ),
            )
        )

        if not verificacion.valido:

            mensajes.append(
                (
                    "[ATENAS][VERIFICADOR] "
                    "Cambio rechazado."
                )
            )

            return ResultadoAutorreparacion(
                ok=False,
                estado="rechazado",

                diagnostico=diagnostico,
                cambio=cambio,
                sandbox=resultado_sandbox,
                verificacion=verificacion,

                mensajes=mensajes,
            )

        mensajes.append(
            (
                "[ATENAS][VERIFICADOR] "
                f"Riesgo: "
                f"{verificacion.riesgo.value}."
            )
        )

        # =====================================================
        # 5. LEER ORIGINAL
        # =====================================================

        lectura = (
            self.inspector
            .leer_archivo(
                cambio.archivo
            )
        )

        if not lectura.get(
            "ok"
        ):

            return ResultadoAutorreparacion(
                ok=False,
                estado="lectura_original_fallida",

                diagnostico=diagnostico,
                cambio=cambio,
                sandbox=resultado_sandbox,
                verificacion=verificacion,

                mensajes=mensajes,

                error=(
                    "No fue posible leer "
                    "el archivo original."
                ),
            )

        # =====================================================
        # 6. REGISTRAR
        # =====================================================

        pruebas_json = {
            "sandbox_ok":
                resultado_sandbox.ok,

            "tests": [
                {
                    "ok":
                        prueba.ok,

                    "comando":
                        prueba.comando,

                    "returncode":
                        prueba.returncode,

                    "duracion":
                        prueba.duracion,
                }
                for prueba
                in resultado_sandbox.pruebas
            ],
        }

        cambio_id = (
            self.historial
            .registrar_propuesta(
                cambio=cambio,

                verificacion=(
                    verificacion
                ),

                contenido_original=(
                    lectura[
                        "contenido"
                    ]
                ),

                pruebas=(
                    pruebas_json
                ),
            )
        )

        # =====================================================
        # 7. ¿REQUIERE CONFIRMACIÓN?
        # =====================================================

        if (
            verificacion
            .requiere_confirmacion
            or not verificacion.autoaplicable
        ):

            mensajes.append(
                (
                    "[ATENAS][AUTORREPARACION] "
                    "El cambio necesita aprobación."
                )
            )

            return ResultadoAutorreparacion(
                ok=True,
                estado="esperando_confirmacion",

                diagnostico=diagnostico,
                cambio=cambio,
                sandbox=resultado_sandbox,
                verificacion=verificacion,

                cambio_id=cambio_id,

                aplicado=False,

                requiere_confirmacion=True,

                mensajes=mensajes,
            )

        # =====================================================
        # 8. AUTOAPLICACIÓN DE BAJO RIESGO
        # =====================================================

        if not aplicar_bajo_riesgo:

            return ResultadoAutorreparacion(
                ok=True,
                estado="validado_no_aplicado",

                diagnostico=diagnostico,
                cambio=cambio,
                sandbox=resultado_sandbox,
                verificacion=verificacion,

                cambio_id=cambio_id,

                aplicado=False,

                mensajes=mensajes,
            )

        gestor_produccion = (
            GestorParches(
                raiz_proyecto=(
                    self.raiz
                ),

                politica=(
                    self.politica
                ),
            )
        )

        aplicacion = (
            gestor_produccion
            .aplicar(
                cambio
            )
        )

        if not aplicacion.ok:

            return ResultadoAutorreparacion(
                ok=False,
                estado="fallo_aplicacion",

                diagnostico=diagnostico,
                cambio=cambio,
                sandbox=resultado_sandbox,
                verificacion=verificacion,

                cambio_id=cambio_id,

                aplicado=False,

                mensajes=mensajes,

                error=(
                    aplicacion.mensaje
                ),
            )

        self.historial.marcar_aplicado(
            cambio_id=(
                cambio_id
            ),

            hash_despues=(
                aplicacion.hash_despues
                or ""
            ),
        )

        mensajes.append(
            (
                "[ATENAS][AUTORREPARACION] "
                "Corrección aplicada."
            )
        )

        return ResultadoAutorreparacion(
            ok=True,
            estado="aplicado",

            diagnostico=diagnostico,
            cambio=cambio,
            sandbox=resultado_sandbox,
            verificacion=verificacion,

            cambio_id=cambio_id,

            aplicado=True,

            mensajes=mensajes,
        )