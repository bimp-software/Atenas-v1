from __future__ import annotations

import ast

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .inspector_codigo import (
    InspectorCodigo,
)

from .mapa_proyecto import (
    MapaProyecto,
)

from .politica import (
    NivelRiesgo,
    PoliticaDesarrollo,
)

from .historial_cambios import (
    HistorialCambios,
)


class TipoHallazgo(str, Enum):
    FUNCION_GRANDE = "funcion_grande"
    CLASE_GRANDE = "clase_grande"
    MODULO_GRANDE = "modulo_grande"
    MUCHOS_IMPORTS = "muchos_imports"
    TEST_FALTANTE = "test_faltante"
    CODIGO_DUPLICADO_SIMPLE = "codigo_duplicado_simple"
    ERROR_REPETIDO = "error_repetido"


@dataclass
class HallazgoMejora:
    tipo: TipoHallazgo

    archivo: str

    descripcion: str

    severidad: float
    confianza: float

    linea: int | None = None
    simbolo: str | None = None

    riesgo_estimado: NivelRiesgo = (
        NivelRiesgo.BAJO
    )

    requiere_confirmacion: bool = False

    datos: dict = field(
        default_factory=dict
    )


@dataclass
class InformeAutoMejora:
    total_archivos: int

    hallazgos: list[
        HallazgoMejora
    ] = field(
        default_factory=list
    )

    resumen: dict = field(
        default_factory=dict
    )


class AutoMejora:
    """
    Analizador estático de calidad del proyecto ATENAS.

    IMPORTANTE:

    Esta clase NO modifica código.
    Solo detecta oportunidades de mejora.

    Cualquier cambio futuro debe seguir:

        Hallazgo
        -> propuesta
        -> ProgramadorAtenas
        -> Sandbox
        -> tests
        -> VerificadorCambio
        -> política
        -> aprobación/aplicación
    """

    MAX_LINEAS_FUNCION = 80
    MAX_LINEAS_CLASE = 350
    MAX_LINEAS_MODULO = 900
    MAX_IMPORTS_MODULO = 30

    MIN_LINEAS_BLOQUE_DUPLICADO = 4

    def __init__(
        self,
        inspector: InspectorCodigo,
        mapa: MapaProyecto,
        politica: PoliticaDesarrollo,
        historial: HistorialCambios | None = None,
    ):
        self.inspector = inspector
        self.mapa = mapa
        self.politica = politica
        self.historial = historial

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _fin_nodo(
        nodo: ast.AST,
    ) -> int:

        return int(
            getattr(
                nodo,
                "end_lineno",
                getattr(
                    nodo,
                    "lineno",
                    0,
                ),
            )
            or 0
        )

    @classmethod
    def _lineas_nodo(
        cls,
        nodo: ast.AST,
    ) -> int:

        inicio = int(
            getattr(
                nodo,
                "lineno",
                0,
            )
            or 0
        )

        fin = cls._fin_nodo(
            nodo
        )

        if inicio <= 0:
            return 0

        return max(
            1,
            fin - inicio + 1,
        )

    def _riesgo_para_archivo(
        self,
        archivo: str,
    ) -> tuple[
        NivelRiesgo,
        bool,
    ]:

        evaluacion = (
            self.politica
            .evaluar_modificacion(
                archivo
            )
        )

        return (
            evaluacion.riesgo,
            evaluacion.requiere_confirmacion,
        )

    # =========================================================
    # ANALIZAR UN ARCHIVO
    # =========================================================

    def analizar_archivo(
        self,
        archivo: str,
    ) -> list[HallazgoMejora]:

        hallazgos = []

        lectura = (
            self.inspector
            .leer_archivo(
                archivo
            )
        )

        if not lectura.get(
            "ok"
        ):
            return []

        contenido = (
            lectura[
                "contenido"
            ]
        )

        lineas = (
            contenido
            .splitlines()
        )

        total_lineas = len(
            lineas
        )

        riesgo, requiere_confirmacion = (
            self._riesgo_para_archivo(
                archivo
            )
        )

        # =====================================================
        # MÓDULO GRANDE
        # =====================================================

        if (
            total_lineas
            > self.MAX_LINEAS_MODULO
        ):

            exceso = (
                total_lineas
                - self.MAX_LINEAS_MODULO
            )

            severidad = min(
                1.0,
                0.55
                + (
                    exceso
                    / max(
                        self.MAX_LINEAS_MODULO,
                        1,
                    )
                ),
            )

            hallazgos.append(
                HallazgoMejora(
                    tipo=(
                        TipoHallazgo
                        .MODULO_GRANDE
                    ),

                    archivo=archivo,

                    descripcion=(
                        f"El módulo tiene "
                        f"{total_lineas} líneas. "
                        "Conviene revisar si contiene "
                        "demasiadas responsabilidades."
                    ),

                    severidad=severidad,
                    confianza=0.98,

                    riesgo_estimado=riesgo,

                    requiere_confirmacion=(
                        requiere_confirmacion
                    ),

                    datos={
                        "lineas":
                            total_lineas,

                        "umbral":
                            self.MAX_LINEAS_MODULO,
                    },
                )
            )

        # =====================================================
        # AST
        # =====================================================

        try:

            arbol = ast.parse(
                contenido,
                filename=archivo,
            )

        except SyntaxError:
            return hallazgos

        # =====================================================
        # IMPORTS
        # =====================================================

        imports = [
            nodo
            for nodo
            in arbol.body
            if isinstance(
                nodo,
                (
                    ast.Import,
                    ast.ImportFrom,
                ),
            )
        ]

        if (
            len(imports)
            > self.MAX_IMPORTS_MODULO
        ):

            hallazgos.append(
                HallazgoMejora(
                    tipo=(
                        TipoHallazgo
                        .MUCHOS_IMPORTS
                    ),

                    archivo=archivo,

                    descripcion=(
                        f"El módulo contiene "
                        f"{len(imports)} sentencias "
                        "de importación. Puede indicar "
                        "acoplamiento elevado."
                    ),

                    severidad=min(
                        1.0,
                        0.45
                        + (
                            len(imports)
                            / 100
                        ),
                    ),

                    confianza=0.85,

                    riesgo_estimado=riesgo,

                    requiere_confirmacion=(
                        requiere_confirmacion
                    ),

                    datos={
                        "imports":
                            len(imports),

                        "umbral":
                            self.MAX_IMPORTS_MODULO,
                    },
                )
            )

        # =====================================================
        # FUNCIONES Y CLASES
        # =====================================================

        for nodo in ast.walk(
            arbol
        ):

            if isinstance(
                nodo,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):

                cantidad_lineas = (
                    self._lineas_nodo(
                        nodo
                    )
                )

                if (
                    cantidad_lineas
                    > self.MAX_LINEAS_FUNCION
                ):

                    hallazgos.append(
                        HallazgoMejora(
                            tipo=(
                                TipoHallazgo
                                .FUNCION_GRANDE
                            ),

                            archivo=archivo,

                            descripcion=(
                                f"La función "
                                f"'{nodo.name}' tiene "
                                f"{cantidad_lineas} líneas. "
                                "Conviene evaluar una "
                                "separación en unidades "
                                "más pequeñas."
                            ),

                            severidad=min(
                                1.0,
                                0.50
                                + (
                                    cantidad_lineas
                                    / 400
                                ),
                            ),

                            confianza=0.95,

                            linea=(
                                nodo.lineno
                            ),

                            simbolo=(
                                nodo.name
                            ),

                            riesgo_estimado=riesgo,

                            requiere_confirmacion=(
                                requiere_confirmacion
                            ),

                            datos={
                                "lineas":
                                    cantidad_lineas,

                                "umbral":
                                    self.MAX_LINEAS_FUNCION,
                            },
                        )
                    )

            elif isinstance(
                nodo,
                ast.ClassDef,
            ):

                cantidad_lineas = (
                    self._lineas_nodo(
                        nodo
                    )
                )

                if (
                    cantidad_lineas
                    > self.MAX_LINEAS_CLASE
                ):

                    hallazgos.append(
                        HallazgoMejora(
                            tipo=(
                                TipoHallazgo
                                .CLASE_GRANDE
                            ),

                            archivo=archivo,

                            descripcion=(
                                f"La clase "
                                f"'{nodo.name}' tiene "
                                f"{cantidad_lineas} líneas. "
                                "Puede estar concentrando "
                                "demasiadas responsabilidades."
                            ),

                            severidad=min(
                                1.0,
                                0.55
                                + (
                                    cantidad_lineas
                                    / 1200
                                ),
                            ),

                            confianza=0.95,

                            linea=(
                                nodo.lineno
                            ),

                            simbolo=(
                                nodo.name
                            ),

                            riesgo_estimado=riesgo,

                            requiere_confirmacion=(
                                requiere_confirmacion
                            ),

                            datos={
                                "lineas":
                                    cantidad_lineas,

                                "umbral":
                                    self.MAX_LINEAS_CLASE,
                            },
                        )
                    )

        # =====================================================
        # TEST FALTANTE
        # =====================================================

        if (
            archivo.startswith(
                "src/"
            )
            and archivo.endswith(
                ".py"
            )
            and not archivo.endswith(
                "__init__.py"
            )
        ):

            ruta = Path(
                archivo
            )

            nombre = (
                ruta.stem
            )

            candidatos = {
                f"tests/test_{nombre}.py",
                f"tests/{nombre}_test.py",
            }

            archivos_existentes = {
                item.ruta
                for item
                in self.inspector
                .listar_python()
            }

            if not (
                candidatos
                & archivos_existentes
            ):

                hallazgos.append(
                    HallazgoMejora(
                        tipo=(
                            TipoHallazgo
                            .TEST_FALTANTE
                        ),

                        archivo=archivo,

                        descripcion=(
                            "No se encontró un test "
                            "con nombre directo asociado "
                            f"al módulo '{nombre}'."
                        ),

                        severidad=0.45,
                        confianza=0.70,

                        riesgo_estimado=(
                            NivelRiesgo.BAJO
                        ),

                        requiere_confirmacion=False,

                        datos={
                            "candidatos":
                                sorted(
                                    candidatos
                                )
                        },
                    )
                )

        return hallazgos

    # =========================================================
    # ERRORES REPETIDOS
    # =========================================================

    def analizar_historial(
        self,
    ) -> list[HallazgoMejora]:

        if self.historial is None:
            return []

        try:

            registros = (
                self.historial
                .ultimos(
                    limite=100
                )
            )

        except Exception:
            return []

        contador: dict[
            tuple[str, str],
            int
        ] = {}

        for registro in registros:

            archivo = str(
                registro.get(
                    "archivo",
                    "",
                )
                or ""
            )

            descripcion = str(
                registro.get(
                    "descripcion",
                    "",
                )
                or ""
            )

            clave = (
                archivo,
                descripcion,
            )

            contador[
                clave
            ] = (
                contador.get(
                    clave,
                    0,
                )
                + 1
            )

        hallazgos = []

        for (
            archivo,
            descripcion,
        ), cantidad in contador.items():

            if cantidad < 3:
                continue

            riesgo, requiere_confirmacion = (
                self._riesgo_para_archivo(
                    archivo
                )
                if archivo
                else (
                    NivelRiesgo.MEDIO,
                    True,
                )
            )

            hallazgos.append(
                HallazgoMejora(
                    tipo=(
                        TipoHallazgo
                        .ERROR_REPETIDO
                    ),

                    archivo=(
                        archivo
                        or "desconocido"
                    ),

                    descripcion=(
                        f"Se registró el mismo "
                        f"tipo de cambio/error "
                        f"{cantidad} veces: "
                        f"{descripcion}"
                    ),

                    severidad=min(
                        1.0,
                        0.50
                        + (
                            cantidad
                            * 0.08
                        ),
                    ),

                    confianza=0.80,

                    riesgo_estimado=riesgo,

                    requiere_confirmacion=(
                        requiere_confirmacion
                    ),

                    datos={
                        "repeticiones":
                            cantidad
                    },
                )
            )

        return hallazgos

    # =========================================================
    # ANALIZAR PROYECTO
    # =========================================================

    def analizar_proyecto(
        self,
        limite_archivos: int | None = None,
    ) -> InformeAutoMejora:

        archivos = (
            self.inspector
            .listar_python()
        )

        if limite_archivos is not None:

            archivos = archivos[
                :max(
                    0,
                    int(
                        limite_archivos
                    ),
                )
            ]

        hallazgos = []

        for archivo in archivos:

            hallazgos.extend(
                self.analizar_archivo(
                    archivo.ruta
                )
            )

        hallazgos.extend(
            self.analizar_historial()
        )

        hallazgos.sort(
            key=lambda item: (
                item.severidad,
                item.confianza,
            ),
            reverse=True,
        )

        resumen = {}

        for hallazgo in hallazgos:

            clave = (
                hallazgo.tipo.value
            )

            resumen[
                clave
            ] = (
                resumen.get(
                    clave,
                    0,
                )
                + 1
            )

        return InformeAutoMejora(
            total_archivos=len(
                archivos
            ),

            hallazgos=hallazgos,

            resumen=resumen,
        )

    # =========================================================
    # CONTEXTO PARA LLM
    # =========================================================

    def contexto_para_llm(
        self,
        informe: InformeAutoMejora,
        limite: int = 20,
    ) -> str:

        if not informe.hallazgos:

            return (
                "ANÁLISIS DE AUTOMEJORA DE ATENAS:\n"
                "- No se detectaron oportunidades "
                "prioritarias de mejora."
            )

        lineas = [
            "ANÁLISIS DE AUTOMEJORA DE ATENAS:",
            "",
            (
                "Archivos analizados: "
                f"{informe.total_archivos}"
            ),
            (
                "Hallazgos: "
                f"{len(informe.hallazgos)}"
            ),
            "",
        ]

        for numero, hallazgo in enumerate(
            informe.hallazgos[
                :max(
                    1,
                    int(limite),
                )
            ],
            start=1,
        ):

            linea = (
                f"{numero}. "
                f"[{hallazgo.tipo.value}] "
                f"{hallazgo.archivo}"
            )

            if hallazgo.simbolo:

                linea += (
                    f" :: {hallazgo.simbolo}"
                )

            linea += (
                f" | severidad="
                f"{hallazgo.severidad:.2f}"
                f" | confianza="
                f"{hallazgo.confianza:.2f}"
                f" | riesgo="
                f"{hallazgo.riesgo_estimado.value}"
            )

            lineas.append(
                linea
            )

            lineas.append(
                "   "
                + hallazgo.descripcion
            )

        lineas.extend([
            "",
            "IMPORTANTE:",
            (
                "- Estos son hallazgos de análisis, "
                "no cambios aplicados."
            ),
            (
                "- Cualquier modificación debe pasar "
                "por sandbox, pruebas y verificación."
            ),
            (
                "- No refactorices automáticamente "
                "componentes protegidos."
            ),
        ])

        return "\n".join(
            lineas
        )