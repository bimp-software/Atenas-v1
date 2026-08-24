from __future__ import annotations

import json
import shutil
import uuid

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .parche import (
    CambioCodigo,
    GestorParches,
    ResultadoAplicacionParche,
)

from .politica import (
    PoliticaDesarrollo,
)

from .pruebas import (
    EjecutorPruebas,
    ResultadoPrueba,
)


@dataclass
class EntornoSandbox:
    id: str

    raiz: Path
    proyecto: Path

    creado_en: str

    diagnostico_path: Path
    parche_path: Path
    pruebas_path: Path
    resultado_path: Path


@dataclass
class ResultadoSandbox:
    ok: bool

    sandbox_id: str

    entorno: EntornoSandbox

    aplicacion: ResultadoAplicacionParche | None = None

    sintaxis: ResultadoPrueba | None = None

    pruebas: list[ResultadoPrueba] = field(
        default_factory=list
    )

    mensaje: str = ""

    errores: list[str] = field(
        default_factory=list
    )


class SandboxCodigo:
    """
    Entorno aislado de desarrollo para ATENAS.

    Copia el proyecto a:

        .atenas/sandbox/<uuid>/proyecto/

    y aplica modificaciones únicamente allí.

    Nunca modifica directamente el proyecto original.
    """

    DIRECTORIOS_EXCLUIDOS = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".idea",
        ".vscode",
        "node_modules",
        ".atenas",
    }

    ARCHIVOS_EXCLUIDOS = {
        ".DS_Store",
    }

    def __init__(
        self,
        raiz_proyecto: str | Path = ".",
        raiz_sandboxes: str | Path | None = None,
    ):
        self.raiz_proyecto = Path(
            raiz_proyecto
        ).resolve()

        if raiz_sandboxes is None:

            self.raiz_sandboxes = (
                self.raiz_proyecto
                / ".atenas"
                / "sandbox"
            )

        else:

            self.raiz_sandboxes = Path(
                raiz_sandboxes
            ).resolve()

        self.raiz_sandboxes.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =========================================================
    # IGNORAR COPIA
    # =========================================================

    def _ignorar(
        self,
        directorio: str,
        nombres: list[str],
    ) -> set[str]:

        ignorados = set()

        for nombre in nombres:

            if nombre in self.DIRECTORIOS_EXCLUIDOS:
                ignorados.add(
                    nombre
                )

            if nombre in self.ARCHIVOS_EXCLUIDOS:
                ignorados.add(
                    nombre
                )

            if nombre.endswith(
                ".pyc"
            ):
                ignorados.add(
                    nombre
                )

        return ignorados

    # =========================================================
    # CREAR ENTORNO
    # =========================================================

    def crear(
        self,
    ) -> EntornoSandbox:

        identificador = str(
            uuid.uuid4()
        )

        raiz = (
            self.raiz_sandboxes
            / identificador
        )

        proyecto = (
            raiz
            / "proyecto"
        )

        raiz.mkdir(
            parents=True,
            exist_ok=False,
        )

        shutil.copytree(
            self.raiz_proyecto,
            proyecto,
            ignore=self._ignorar,
        )

        creado_en = (
            datetime.now()
            .astimezone()
            .isoformat()
        )

        entorno = EntornoSandbox(
            id=identificador,

            raiz=raiz,
            proyecto=proyecto,

            creado_en=creado_en,

            diagnostico_path=(
                raiz
                / "diagnostico.json"
            ),

            parche_path=(
                raiz
                / "parche.diff"
            ),

            pruebas_path=(
                raiz
                / "pruebas.json"
            ),

            resultado_path=(
                raiz
                / "resultado.json"
            ),
        )

        self._guardar_json(
            entorno.resultado_path,
            {
                "sandbox_id":
                    entorno.id,

                "estado":
                    "creado",

                "creado_en":
                    entorno.creado_en,
            },
        )

        return entorno

    # =========================================================
    # GUARDAR JSON
    # =========================================================

    @staticmethod
    def _guardar_json(
        ruta: Path,
        datos: dict,
    ) -> None:

        ruta.write_text(
            json.dumps(
                datos,
                ensure_ascii=False,
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )

    # =========================================================
    # GUARDAR DIAGNÓSTICO
    # =========================================================

    def guardar_diagnostico(
        self,
        entorno: EntornoSandbox,
        diagnostico: dict,
    ) -> None:

        self._guardar_json(
            entorno.diagnostico_path,
            diagnostico,
        )

    # =========================================================
    # APLICAR CAMBIO
    # =========================================================

    def aplicar_cambio(
        self,
        entorno: EntornoSandbox,
        cambio: CambioCodigo,
    ) -> ResultadoAplicacionParche:

        politica = (
            PoliticaDesarrollo(
                entorno.proyecto
            )
        )

        gestor = (
            GestorParches(
                raiz_proyecto=(
                    entorno.proyecto
                ),
                politica=politica,
            )
        )

        resultado = (
            gestor.aplicar(
                cambio
            )
        )

        entorno.parche_path.write_text(
            cambio.diff,
            encoding="utf-8",
        )

        return resultado

    # =========================================================
    # PROBAR CAMBIO
    # =========================================================

    def probar_cambio(
        self,
        entorno: EntornoSandbox,
        cambio: CambioCodigo,
        tests: list[str] | None = None,
        timeout_test: int = 60,
    ) -> ResultadoSandbox:

        errores = []

        # =====================================================
        # APLICAR
        # =====================================================

        aplicacion = (
            self.aplicar_cambio(
                entorno=entorno,
                cambio=cambio,
            )
        )

        if not aplicacion.ok:

            errores.append(
                aplicacion.mensaje
            )

            resultado = ResultadoSandbox(
                ok=False,

                sandbox_id=(
                    entorno.id
                ),

                entorno=entorno,

                aplicacion=aplicacion,

                mensaje=(
                    "No fue posible aplicar "
                    "el cambio al sandbox."
                ),

                errores=errores,
            )

            self._guardar_resultado(
                resultado
            )

            return resultado

        # =====================================================
        # EJECUTOR
        # =====================================================

        ejecutor = (
            EjecutorPruebas(
                raiz_proyecto=(
                    entorno.proyecto
                )
            )
        )

        # =====================================================
        # SINTAXIS
        # =====================================================

        sintaxis = None

        if cambio.archivo.endswith(
            ".py"
        ):

            sintaxis = (
                ejecutor
                .comprobar_sintaxis(
                    cambio.archivo,
                    cwd=(
                        entorno.proyecto
                    ),
                )
            )

            if not sintaxis.ok:

                errores.append(
                    "El archivo modificado "
                    "no compila correctamente."
                )

        # =====================================================
        # TESTS
        # =====================================================

        resultados_tests = []

        if (
            not errores
            and tests
        ):

            for modulo_test in tests:

                resultado_test = (
                    ejecutor.ejecutar_test(
                        modulo_test=(
                            modulo_test
                        ),
                        timeout=(
                            timeout_test
                        ),
                        cwd=(
                            entorno.proyecto
                        ),
                    )
                )

                resultados_tests.append(
                    resultado_test
                )

                if not resultado_test.ok:

                    errores.append(
                        "Falló el test: "
                        f"{modulo_test}"
                    )

                    # No seguimos generando ruido
                    # si un test crítico ya falló.
                    break

        ok = (
            aplicacion.ok
            and (
                sintaxis is None
                or sintaxis.ok
            )
            and not errores
        )

        mensaje = (
            "Cambio validado dentro "
            "del sandbox."
            if ok
            else
            "El cambio falló dentro "
            "del sandbox."
        )

        resultado = ResultadoSandbox(
            ok=ok,

            sandbox_id=(
                entorno.id
            ),

            entorno=entorno,

            aplicacion=aplicacion,

            sintaxis=sintaxis,

            pruebas=(
                resultados_tests
            ),

            mensaje=mensaje,

            errores=errores,
        )

        self._guardar_resultado(
            resultado
        )

        return resultado

    # =========================================================
    # GUARDAR RESULTADO
    # =========================================================

    def _guardar_resultado(
        self,
        resultado: ResultadoSandbox,
    ) -> None:

        pruebas = []

        for prueba in resultado.pruebas:

            pruebas.append({
                "ok":
                    prueba.ok,

                "comando":
                    prueba.comando,

                "returncode":
                    prueba.returncode,

                "stdout":
                    prueba.stdout,

                "stderr":
                    prueba.stderr,

                "duracion":
                    prueba.duracion,

                "timeout":
                    prueba.timeout,

                "error":
                    prueba.error,
            })

        self._guardar_json(
            resultado.entorno.pruebas_path,
            {
                "pruebas":
                    pruebas,
            },
        )

        self._guardar_json(
            resultado.entorno.resultado_path,
            {
                "sandbox_id":
                    resultado.sandbox_id,

                "ok":
                    resultado.ok,

                "mensaje":
                    resultado.mensaje,

                "errores":
                    resultado.errores,

                "aplicacion": (
                    {
                        "ok":
                            resultado.aplicacion.ok,

                        "archivo":
                            resultado.aplicacion.archivo,

                        "mensaje":
                            resultado.aplicacion.mensaje,

                        "hash_antes":
                            resultado.aplicacion.hash_antes,

                        "hash_despues":
                            resultado.aplicacion.hash_despues,
                    }
                    if resultado.aplicacion
                    else None
                ),

                "sintaxis": (
                    {
                        "ok":
                            resultado.sintaxis.ok,

                        "returncode":
                            resultado.sintaxis.returncode,

                        "stdout":
                            resultado.sintaxis.stdout,

                        "stderr":
                            resultado.sintaxis.stderr,
                    }
                    if resultado.sintaxis
                    else None
                ),

                "tests":
                    pruebas,
            },
        )

    # =========================================================
    # DESTRUIR SANDBOX
    # =========================================================

    def eliminar(
        self,
        entorno: EntornoSandbox,
    ) -> bool:

        try:

            if entorno.raiz.exists():

                shutil.rmtree(
                    entorno.raiz
                )

            return True

        except OSError:

            return False