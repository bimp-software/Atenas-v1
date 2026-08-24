from __future__ import annotations

import difflib
import hashlib

from dataclasses import dataclass, field
from pathlib import Path

from .politica import (
    NivelRiesgo,
    PoliticaDesarrollo,
)


@dataclass
class CambioCodigo:
    """
    Representa una modificación propuesta por ATENAS.

    Todavía NO significa que el cambio haya sido aplicado.
    """

    archivo: str

    contenido_original_hash: str

    contenido_nuevo: str

    razon: str

    riesgo: NivelRiesgo | None = None

    requiere_confirmacion: bool | None = None

    diff: str = ""


@dataclass
class ResultadoValidacionParche:
    valido: bool

    motivo: str

    archivo: str

    riesgo: NivelRiesgo

    requiere_confirmacion: bool

    hash_actual: str | None = None

    hash_esperado: str | None = None

    errores: list[str] = field(
        default_factory=list
    )


@dataclass
class ResultadoAplicacionParche:
    ok: bool

    archivo: str

    mensaje: str

    hash_antes: str | None = None

    hash_despues: str | None = None

    diff: str = ""


class GestorParches:
    """
    Gestiona modificaciones estructuradas de código.

    IMPORTANTE:
    esta clase NO decide si un cambio es intelectualmente correcto.

    Solo:
    - calcula hashes;
    - genera diff;
    - valida política;
    - comprueba que el archivo no cambió;
    - aplica una modificación a una raíz indicada.

    Posteriormente la raíz será el SANDBOX.
    """

    def __init__(
        self,
        raiz_proyecto: str | Path = ".",
        politica: PoliticaDesarrollo | None = None,
    ):
        self.raiz = Path(
            raiz_proyecto
        ).resolve()

        self.politica = (
            politica
            or PoliticaDesarrollo(
                self.raiz
            )
        )

    # =========================================================
    # HASH
    # =========================================================

    @staticmethod
    def calcular_hash_texto(
        contenido: str,
    ) -> str:

        return hashlib.sha256(
            contenido.encode(
                "utf-8"
            )
        ).hexdigest()

    def calcular_hash_archivo(
        self,
        ruta: str | Path,
    ) -> str | None:

        try:

            relativa = (
                self.politica
                .normalizar_ruta(
                    ruta
                )
            )

            archivo = (
                self.raiz
                / relativa
            ).resolve()

        except PermissionError:
            return None

        if not archivo.exists():
            return None

        if not archivo.is_file():
            return None

        try:

            contenido = (
                archivo.read_text(
                    encoding="utf-8"
                )
            )

        except (
            UnicodeDecodeError,
            OSError,
        ):
            return None

        return (
            self.calcular_hash_texto(
                contenido
            )
        )

    # =========================================================
    # CREAR DIFF
    # =========================================================

    @staticmethod
    def crear_diff(
        archivo: str,
        contenido_original: str,
        contenido_nuevo: str,
    ) -> str:

        lineas_originales = (
            contenido_original
            .splitlines(
                keepends=True
            )
        )

        lineas_nuevas = (
            contenido_nuevo
            .splitlines(
                keepends=True
            )
        )

        diff = difflib.unified_diff(
            lineas_originales,
            lineas_nuevas,

            fromfile=(
                f"a/{archivo}"
            ),

            tofile=(
                f"b/{archivo}"
            ),
        )

        return "".join(
            diff
        )

    # =========================================================
    # PREPARAR CAMBIO
    # =========================================================

    def preparar_cambio(
        self,
        archivo: str,
        contenido_original: str,
        contenido_nuevo: str,
        razon: str,
    ) -> CambioCodigo:

        evaluacion = (
            self.politica
            .evaluar_modificacion(
                archivo
            )
        )

        hash_original = (
            self.calcular_hash_texto(
                contenido_original
            )
        )

        diff = self.crear_diff(
            archivo=archivo,
            contenido_original=(
                contenido_original
            ),
            contenido_nuevo=(
                contenido_nuevo
            ),
        )

        return CambioCodigo(
            archivo=archivo,

            contenido_original_hash=(
                hash_original
            ),

            contenido_nuevo=(
                contenido_nuevo
            ),

            razon=razon,

            riesgo=(
                evaluacion.riesgo
            ),

            requiere_confirmacion=(
                evaluacion
                .requiere_confirmacion
            ),

            diff=diff,
        )

    # =========================================================
    # VALIDAR
    # =========================================================

    def validar(
        self,
        cambio: CambioCodigo,
    ) -> ResultadoValidacionParche:

        errores = []

        evaluacion = (
            self.politica
            .evaluar_modificacion(
                cambio.archivo
            )
        )

        # =====================================================
        # POLÍTICA
        # =====================================================

        if not evaluacion.permitido:

            errores.append(
                evaluacion.motivo
            )

        # =====================================================
        # CONTENIDO
        # =====================================================

        if not cambio.contenido_nuevo:

            errores.append(
                "El nuevo contenido está vacío."
            )

        # =====================================================
        # HASH ACTUAL
        # =====================================================

        hash_actual = (
            self.calcular_hash_archivo(
                cambio.archivo
            )
        )

        if hash_actual is None:

            errores.append(
                "No fue posible obtener "
                "el archivo actual."
            )

        elif (
            hash_actual
            != cambio.contenido_original_hash
        ):

            errores.append(
                "El archivo cambió desde que "
                "ATENAS lo inspeccionó."
            )

        # =====================================================
        # NO HAY CAMBIOS
        # =====================================================

        if (
            hash_actual is not None
            and self.calcular_hash_texto(
                cambio.contenido_nuevo
            )
            == hash_actual
        ):

            errores.append(
                "El parche no produce cambios."
            )

        valido = (
            len(errores) == 0
        )

        motivo = (
            "Parche válido."
            if valido
            else "; ".join(
                errores
            )
        )

        return ResultadoValidacionParche(
            valido=valido,

            motivo=motivo,

            archivo=(
                cambio.archivo
            ),

            riesgo=(
                evaluacion.riesgo
            ),

            requiere_confirmacion=(
                evaluacion
                .requiere_confirmacion
            ),

            hash_actual=(
                hash_actual
            ),

            hash_esperado=(
                cambio
                .contenido_original_hash
            ),

            errores=errores,
        )

    # =========================================================
    # APLICAR
    # =========================================================

    def aplicar(
        self,
        cambio: CambioCodigo,
    ) -> ResultadoAplicacionParche:
        """
        Aplica un cambio dentro de self.raiz.

        IMPORTANTE:
        cuando implementemos SandboxCodigo,
        self.raiz apuntará a la copia del proyecto,
        no al proyecto principal.
        """

        validacion = (
            self.validar(
                cambio
            )
        )

        if not validacion.valido:

            return ResultadoAplicacionParche(
                ok=False,

                archivo=(
                    cambio.archivo
                ),

                mensaje=(
                    validacion.motivo
                ),

                hash_antes=(
                    validacion.hash_actual
                ),

                diff=(
                    cambio.diff
                ),
            )

        relativa = (
            self.politica
            .normalizar_ruta(
                cambio.archivo
            )
        )

        archivo = (
            self.raiz
            / relativa
        ).resolve()

        hash_antes = (
            self.calcular_hash_archivo(
                relativa
            )
        )

        try:

            archivo.write_text(
                cambio.contenido_nuevo,
                encoding="utf-8",
            )

        except OSError as error:

            return ResultadoAplicacionParche(
                ok=False,

                archivo=relativa,

                mensaje=(
                    f"No fue posible escribir "
                    f"el archivo: {error}"
                ),

                hash_antes=(
                    hash_antes
                ),

                diff=(
                    cambio.diff
                ),
            )

        hash_despues = (
            self.calcular_hash_archivo(
                relativa
            )
        )

        return ResultadoAplicacionParche(
            ok=True,

            archivo=relativa,

            mensaje=(
                "Parche aplicado correctamente."
            ),

            hash_antes=hash_antes,

            hash_despues=(
                hash_despues
            ),

            diff=(
                cambio.diff
            ),
        )