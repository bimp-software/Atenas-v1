from __future__ import annotations

import ast

from dataclasses import dataclass, field
from pathlib import Path

from .parche import (
    CambioCodigo,
)

from .politica import (
    NivelRiesgo,
    PoliticaDesarrollo,
)

from .sandbox import (
    ResultadoSandbox,
)


@dataclass
class ResultadoVerificacion:
    valido: bool

    riesgo: NivelRiesgo

    requiere_confirmacion: bool

    autoaplicable: bool

    motivos: list[str] = field(
        default_factory=list
    )

    advertencias: list[str] = field(
        default_factory=list
    )


class VerificadorCambio:
    """
    Decide si un cambio probado dentro del sandbox
    puede avanzar en el proceso de autorreparación.
    """

    IMPORTS_SENSIBLES = {
        "subprocess",
        "ctypes",
        "winreg",
        "socket",
    }

    LLAMADAS_PROHIBIDAS = {
        "eval",
        "exec",
        "compile",
        "__import__",
    }

    def __init__(
        self,
        politica: PoliticaDesarrollo,
    ):
        self.politica = politica

    # =========================================================
    # ANALIZAR CÓDIGO PYTHON
    # =========================================================

    def _analizar_python(
        self,
        contenido: str,
    ) -> tuple[list[str], list[str]]:

        errores = []
        advertencias = []

        try:

            arbol = ast.parse(
                contenido
            )

        except SyntaxError as error:

            errores.append(
                f"SyntaxError: {error}"
            )

            return (
                errores,
                advertencias,
            )

        for nodo in ast.walk(
            arbol
        ):

            # =================================================
            # EVAL / EXEC
            # =================================================

            if isinstance(
                nodo,
                ast.Call,
            ):

                if isinstance(
                    nodo.func,
                    ast.Name,
                ):

                    if (
                        nodo.func.id
                        in self.LLAMADAS_PROHIBIDAS
                    ):

                        errores.append(
                            "Llamada prohibida: "
                            f"{nodo.func.id}"
                        )

                # ---------------------------------------------
                # os.system
                # ---------------------------------------------

                if isinstance(
                    nodo.func,
                    ast.Attribute,
                ):

                    if (
                        isinstance(
                            nodo.func.value,
                            ast.Name,
                        )
                        and nodo.func.value.id
                        == "os"
                        and nodo.func.attr
                        == "system"
                    ):

                        errores.append(
                            "os.system no está "
                            "permitido."
                        )

            # =================================================
            # IMPORTS SENSIBLES
            # =================================================

            if isinstance(
                nodo,
                ast.Import,
            ):

                for alias in nodo.names:

                    raiz = (
                        alias.name
                        .split(".")[0]
                    )

                    if (
                        raiz
                        in self.IMPORTS_SENSIBLES
                    ):

                        advertencias.append(
                            "Import sensible: "
                            f"{alias.name}"
                        )

            elif isinstance(
                nodo,
                ast.ImportFrom,
            ):

                modulo = (
                    nodo.module
                    or ""
                )

                raiz = (
                    modulo
                    .split(".")[0]
                )

                if (
                    raiz
                    in self.IMPORTS_SENSIBLES
                ):

                    advertencias.append(
                        "Import sensible: "
                        f"{modulo}"
                    )

        return (
            errores,
            advertencias,
        )

    # =========================================================
    # VERIFICAR
    # =========================================================

    def verificar(
        self,
        cambio: CambioCodigo,
        resultado_sandbox: ResultadoSandbox,
    ) -> ResultadoVerificacion:

        motivos = []
        advertencias = []

        evaluacion_politica = (
            self.politica
            .evaluar_modificacion(
                cambio.archivo
            )
        )

        riesgo = (
            evaluacion_politica.riesgo
        )

        # =====================================================
        # POLÍTICA
        # =====================================================

        if not evaluacion_politica.permitido:

            motivos.append(
                evaluacion_politica.motivo
            )

        # =====================================================
        # SANDBOX
        # =====================================================

        if not resultado_sandbox.ok:

            motivos.append(
                "El cambio no superó "
                "el sandbox."
            )

            motivos.extend(
                resultado_sandbox.errores
            )

        # =====================================================
        # CAMBIO PYTHON
        # =====================================================

        if cambio.archivo.endswith(
            ".py"
        ):

            errores_python, advertencias_python = (
                self._analizar_python(
                    cambio.contenido_nuevo
                )
            )

            motivos.extend(
                errores_python
            )

            advertencias.extend(
                advertencias_python
            )

        # =====================================================
        # IMPORTS SENSIBLES SUBEN RIESGO
        # =====================================================

        if advertencias:

            if riesgo == NivelRiesgo.BAJO:

                riesgo = (
                    NivelRiesgo.MEDIO
                )

        # =====================================================
        # CONFIRMACIÓN
        # =====================================================

        requiere_confirmacion = (
            evaluacion_politica
            .requiere_confirmacion
        )

        if riesgo in {
            NivelRiesgo.MEDIO,
            NivelRiesgo.ALTO,
            NivelRiesgo.CRITICO,
        }:

            requiere_confirmacion = True

        # =====================================================
        # AUTOAPLICABLE
        # =====================================================

        valido = (
            len(motivos) == 0
        )

        autoaplicable = (
            valido
            and riesgo
            == NivelRiesgo.BAJO
            and not requiere_confirmacion
        )

        return ResultadoVerificacion(
            valido=valido,

            riesgo=riesgo,

            requiere_confirmacion=(
                requiere_confirmacion
            ),

            autoaplicable=(
                autoaplicable
            ),

            motivos=list(
                dict.fromkeys(
                    motivos
                )
            ),

            advertencias=list(
                dict.fromkeys(
                    advertencias
                )
            ),
        )