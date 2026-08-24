from __future__ import annotations

import ast

from dataclasses import (
    dataclass,
    field,
)

from .inspector_codigo import (
    InspectorCodigo,
)


@dataclass
class FuncionProyecto:
    nombre: str
    linea: int
    argumentos: list[str] = field(
        default_factory=list
    )

    async_: bool = False


@dataclass
class ClaseProyecto:
    nombre: str
    linea: int

    bases: list[str] = field(
        default_factory=list
    )

    metodos: list[
        FuncionProyecto
    ] = field(
        default_factory=list
    )


@dataclass
class ArchivoProyecto:
    ruta: str

    imports: list[str] = field(
        default_factory=list
    )

    clases: list[
        ClaseProyecto
    ] = field(
        default_factory=list
    )

    funciones: list[
        FuncionProyecto
    ] = field(
        default_factory=list
    )

    error_sintaxis: str | None = None


class MapaProyecto:
    """
    Construye un mapa AST de los archivos Python
    del proyecto ATENAS.
    """

    def __init__(
        self,
        inspector: InspectorCodigo,
    ):
        self.inspector = inspector

    # =========================================================
    # NOMBRE AST
    # =========================================================

    @staticmethod
    def _nombre_ast(
        nodo: ast.AST,
    ) -> str:

        if isinstance(
            nodo,
            ast.Name,
        ):
            return nodo.id

        if isinstance(
            nodo,
            ast.Attribute,
        ):

            base = (
                MapaProyecto
                ._nombre_ast(
                    nodo.value
                )
            )

            if base:
                return (
                    f"{base}.{nodo.attr}"
                )

            return nodo.attr

        return ""

    # =========================================================
    # FUNCIÓN
    # =========================================================

    @staticmethod
    def _funcion_desde_ast(
        nodo: (
            ast.FunctionDef
            | ast.AsyncFunctionDef
        ),
    ) -> FuncionProyecto:

        argumentos = []

        for argumento in (
            list(
                nodo.args.posonlyargs
            )
            + list(
                nodo.args.args
            )
            + list(
                nodo.args.kwonlyargs
            )
        ):

            argumentos.append(
                argumento.arg
            )

        if nodo.args.vararg:

            argumentos.append(
                "*" + nodo.args.vararg.arg
            )

        if nodo.args.kwarg:

            argumentos.append(
                "**" + nodo.args.kwarg.arg
            )

        return FuncionProyecto(
            nombre=nodo.name,
            linea=nodo.lineno,
            argumentos=argumentos,
            async_=isinstance(
                nodo,
                ast.AsyncFunctionDef,
            ),
        )

    # =========================================================
    # ANALIZAR ARCHIVO
    # =========================================================

    def analizar_archivo(
        self,
        ruta: str,
    ) -> ArchivoProyecto:

        lectura = (
            self.inspector
            .leer_archivo(
                ruta
            )
        )

        if not lectura.get(
            "ok"
        ):

            return ArchivoProyecto(
                ruta=ruta,
                error_sintaxis=(
                    lectura.get(
                        "error",
                        "lectura_fallida",
                    )
                ),
            )

        contenido = lectura[
            "contenido"
        ]

        try:

            arbol = ast.parse(
                contenido,
                filename=ruta,
            )

        except SyntaxError as error:

            return ArchivoProyecto(
                ruta=ruta,
                error_sintaxis=(
                    f"{error.msg} "
                    f"(línea {error.lineno})"
                ),
            )

        archivo = ArchivoProyecto(
            ruta=ruta
        )

        # =====================================================
        # IMPORTS
        # =====================================================

        for nodo in arbol.body:

            if isinstance(
                nodo,
                ast.Import,
            ):

                for alias in nodo.names:

                    archivo.imports.append(
                        alias.name
                    )

            elif isinstance(
                nodo,
                ast.ImportFrom,
            ):

                modulo = (
                    nodo.module
                    or ""
                )

                prefijo = (
                    "." * nodo.level
                )

                archivo.imports.append(
                    prefijo + modulo
                )

        # =====================================================
        # FUNCIONES Y CLASES DE PRIMER NIVEL
        # =====================================================

        for nodo in arbol.body:

            if isinstance(
                nodo,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):

                archivo.funciones.append(
                    self._funcion_desde_ast(
                        nodo
                    )
                )

            elif isinstance(
                nodo,
                ast.ClassDef,
            ):

                bases = []

                for base in nodo.bases:

                    nombre = self._nombre_ast(
                        base
                    )

                    if nombre:
                        bases.append(
                            nombre
                        )

                clase = ClaseProyecto(
                    nombre=nodo.name,
                    linea=nodo.lineno,
                    bases=bases,
                )

                for elemento in nodo.body:

                    if isinstance(
                        elemento,
                        (
                            ast.FunctionDef,
                            ast.AsyncFunctionDef,
                        ),
                    ):

                        clase.metodos.append(
                            self._funcion_desde_ast(
                                elemento
                            )
                        )

                archivo.clases.append(
                    clase
                )

        archivo.imports = sorted(
            set(
                archivo.imports
            )
        )

        return archivo

    # =========================================================
    # CONSTRUIR MAPA
    # =========================================================

    def construir(
        self,
    ) -> dict[str, ArchivoProyecto]:

        mapa = {}

        for archivo in (
            self.inspector
            .listar_python()
        ):

            mapa[
                archivo.ruta
            ] = (
                self.analizar_archivo(
                    archivo.ruta
                )
            )

        return mapa

    # =========================================================
    # RESUMEN PARA LLM
    # =========================================================

    def contexto_para_llm(
        self,
        max_archivos: int = 100,
    ) -> str:

        mapa = self.construir()

        lineas = [
            "MAPA DEL PROYECTO ATENAS:"
        ]

        for numero, (
            ruta,
            info,
        ) in enumerate(
            mapa.items(),
            start=1,
        ):

            if numero > max_archivos:
                break

            lineas.append(
                f"\nARCHIVO: {ruta}"
            )

            if info.error_sintaxis:

                lineas.append(
                    "ERROR DE SINTAXIS: "
                    + info.error_sintaxis
                )

                continue

            if info.imports:

                lineas.append(
                    "Imports: "
                    + ", ".join(
                        info.imports
                    )
                )

            if info.clases:

                lineas.append(
                    "Clases: "
                    + ", ".join(
                        clase.nombre
                        for clase
                        in info.clases
                    )
                )

            if info.funciones:

                lineas.append(
                    "Funciones: "
                    + ", ".join(
                        funcion.nombre
                        for funcion
                        in info.funciones
                    )
                )

        return "\n".join(
            lineas
        )