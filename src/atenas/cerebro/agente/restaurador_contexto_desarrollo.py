from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.atenas.cerebro.desarrollo.analista_requisitos import (
    AnalisisRequisitos,
    Requisito,
    TipoSolucion,
)

from src.atenas.cerebro.desarrollo.arquitecto_software import (
    ArquitecturaSoftware,
    ComponenteArquitectura,
)

from src.atenas.cerebro.desarrollo.disenador_base_datos import (
    CampoBD,
    ModeloBaseDatos,
    RelacionBD,
    TablaBD,
)

from src.atenas.cerebro.desarrollo.planificador_sistema_software import (
    EpicaSoftware,
    EstadoTarea,
    FaseSoftware,
    PlanSistemaSoftware,
    TareaSoftware,
)

from src.atenas.cerebro.desarrollo.orquestador_desarrollo import (
    ResultadoInicioDesarrollo,
)

from src.atenas.cerebro.desarrollo.gestor_estado_proyecto_software import (
    GestorEstadoProyectoSoftware,
)


@dataclass
class ResultadoRestauracionDesarrollo:
    ok: bool
    proyecto_id: str
    carpeta_proyecto: str

    contexto: ResultadoInicioDesarrollo | None = None
    error: str | None = None


class RestauradorContextoDesarrollo:
    """
    Reconstruye el contexto completo de un proyecto de Desarrollo
    usando los archivos persistidos dentro de:

        <proyecto>/.atenas/

    Archivos esperados:
        analisis_requisitos.json
        arquitectura.json
        modelo_datos.json
        plan_software.json
        estado_proyecto.json

    Permite cerrar ATENAS, reiniciarla y continuar proyectos sin
    depender de objetos que solo existían en memoria.
    """

    def __init__(self):
        pass

    # =========================================================
    # JSON
    # =========================================================

    @staticmethod
    def _leer_json(
        ruta: Path,
        requerido: bool = True,
    ) -> Any:

        if not ruta.exists():

            if requerido:
                raise FileNotFoundError(
                    f"No existe: {ruta}"
                )

            return None

        contenido = ruta.read_text(
            encoding="utf-8"
        )

        return json.loads(
            contenido
        )

    # =========================================================
    # REQUISITOS
    # =========================================================

    @staticmethod
    def _requisito(
        datos: dict,
        prefijo: str,
        indice: int,
    ) -> Requisito:

        return Requisito(
            id=str(
                datos.get(
                    "id",
                    f"{prefijo}-{indice:03d}",
                )
            ),
            descripcion=str(
                datos.get(
                    "descripcion",
                    "",
                )
            ),
            prioridad=str(
                datos.get(
                    "prioridad",
                    "media",
                )
            ),
            obligatorio=bool(
                datos.get(
                    "obligatorio",
                    True,
                )
            ),
        )

    @classmethod
    def _analisis(
        cls,
        datos: dict,
    ) -> AnalisisRequisitos:

        tipo_raw = str(
            datos.get(
                "tipo_solucion",
                "desconocido",
            )
        )

        try:
            tipo = TipoSolucion(
                tipo_raw
            )
        except ValueError:
            tipo = TipoSolucion.DESCONOCIDO

        funcionales = [
            cls._requisito(
                item,
                "RF",
                indice,
            )
            for indice, item in enumerate(
                datos.get(
                    "requisitos_funcionales",
                    [],
                )
                or [],
                start=1,
            )
            if isinstance(
                item,
                dict,
            )
        ]

        no_funcionales = [
            cls._requisito(
                item,
                "RNF",
                indice,
            )
            for indice, item in enumerate(
                datos.get(
                    "requisitos_no_funcionales",
                    [],
                )
                or [],
                start=1,
            )
            if isinstance(
                item,
                dict,
            )
        ]

        return AnalisisRequisitos(
            nombre_proyecto=str(
                datos.get(
                    "nombre_proyecto",
                    "Proyecto",
                )
            ),
            tipo_solucion=tipo,
            resumen=str(
                datos.get(
                    "resumen",
                    "",
                )
            ),
            actores=[
                str(item)
                for item in (
                    datos.get(
                        "actores",
                        [],
                    )
                    or []
                )
            ],
            requisitos_funcionales=funcionales,
            requisitos_no_funcionales=no_funcionales,
            entidades_negocio=[
                str(item)
                for item in (
                    datos.get(
                        "entidades_negocio",
                        [],
                    )
                    or []
                )
            ],
            integraciones=[
                str(item)
                for item in (
                    datos.get(
                        "integraciones",
                        [],
                    )
                    or []
                )
            ],
            restricciones=[
                str(item)
                for item in (
                    datos.get(
                        "restricciones",
                        [],
                    )
                    or []
                )
            ],
            necesita_base_datos=bool(
                datos.get(
                    "necesita_base_datos",
                    False,
                )
            ),
            necesita_autenticacion=bool(
                datos.get(
                    "necesita_autenticacion",
                    False,
                )
            ),
            necesita_roles=bool(
                datos.get(
                    "necesita_roles",
                    False,
                )
            ),
            necesita_api=bool(
                datos.get(
                    "necesita_api",
                    False,
                )
            ),
            necesita_archivos=bool(
                datos.get(
                    "necesita_archivos",
                    False,
                )
            ),
            necesita_tiempo_real=bool(
                datos.get(
                    "necesita_tiempo_real",
                    False,
                )
            ),
            necesita_offline=bool(
                datos.get(
                    "necesita_offline",
                    False,
                )
            ),
            complejidad=str(
                datos.get(
                    "complejidad",
                    "media",
                )
            ),
            riesgos_iniciales=[
                str(item)
                for item in (
                    datos.get(
                        "riesgos_iniciales",
                        [],
                    )
                    or []
                )
            ],
            preguntas_abiertas=[
                str(item)
                for item in (
                    datos.get(
                        "preguntas_abiertas",
                        [],
                    )
                    or []
                )
            ],
        )

    # =========================================================
    # ARQUITECTURA
    # =========================================================

    @staticmethod
    def _arquitectura(
        datos: dict,
    ) -> ArquitecturaSoftware:

        componentes = []

        for item in (
            datos.get(
                "componentes",
                [],
            )
            or []
        ):

            if not isinstance(
                item,
                dict,
            ):
                continue

            componentes.append(
                ComponenteArquitectura(
                    nombre=str(
                        item.get(
                            "nombre",
                            "",
                        )
                    ),
                    responsabilidad=str(
                        item.get(
                            "responsabilidad",
                            "",
                        )
                    ),
                    tecnologia=str(
                        item.get(
                            "tecnologia",
                            "",
                        )
                    ),
                    lenguaje=str(
                        item.get(
                            "lenguaje",
                            "",
                        )
                    ),
                    depende_de=[
                        str(dep)
                        for dep in (
                            item.get(
                                "depende_de",
                                [],
                            )
                            or []
                        )
                    ],
                )
            )

        return ArquitecturaSoftware(
            estilo=str(
                datos.get(
                    "estilo",
                    "monolito_modular",
                )
            ),
            tipo_solucion=str(
                datos.get(
                    "tipo_solucion",
                    "desconocido",
                )
            ),
            frontend=datos.get(
                "frontend"
            ),
            backend=datos.get(
                "backend"
            ),
            desktop=datos.get(
                "desktop"
            ),
            movil=datos.get(
                "movil"
            ),
            embebido=datos.get(
                "embebido"
            ),
            api=datos.get(
                "api"
            ),
            base_datos=datos.get(
                "base_datos"
            ),
            cache=datos.get(
                "cache"
            ),
            colas=datos.get(
                "colas"
            ),
            autenticacion=datos.get(
                "autenticacion"
            ),
            componentes=componentes,
            despliegue=(
                datos.get(
                    "despliegue",
                    {},
                )
                or {}
            ),
            pruebas=(
                datos.get(
                    "pruebas",
                    {},
                )
                or {}
            ),
            seguridad=[
                str(item)
                for item in (
                    datos.get(
                        "seguridad",
                        [],
                    )
                    or []
                )
            ],
            decisiones=[
                str(item)
                for item in (
                    datos.get(
                        "decisiones",
                        [],
                    )
                    or []
                )
            ],
        )

    # =========================================================
    # BASE DE DATOS
    # =========================================================

    @staticmethod
    def _modelo_bd(
        datos: dict | None,
    ) -> ModeloBaseDatos | None:

        if not isinstance(
            datos,
            dict,
        ):
            return None

        tablas = []

        for tabla_data in (
            datos.get(
                "tablas",
                [],
            )
            or []
        ):

            if not isinstance(
                tabla_data,
                dict,
            ):
                continue

            campos = []

            for campo_data in (
                tabla_data.get(
                    "campos",
                    [],
                )
                or []
            ):

                if not isinstance(
                    campo_data,
                    dict,
                ):
                    continue

                default_raw = (
                    campo_data.get(
                        "default"
                    )
                )

                campos.append(
                    CampoBD(
                        nombre=str(
                            campo_data.get(
                                "nombre",
                                "",
                            )
                        ),
                        tipo=str(
                            campo_data.get(
                                "tipo",
                                "",
                            )
                        ),
                        nullable=bool(
                            campo_data.get(
                                "nullable",
                                False,
                            )
                        ),
                        unique=bool(
                            campo_data.get(
                                "unique",
                                False,
                            )
                        ),
                        default=(
                            str(
                                default_raw
                            )
                            if default_raw
                            is not None
                            else None
                        ),
                        descripcion=str(
                            campo_data.get(
                                "descripcion",
                                "",
                            )
                        ),
                    )
                )

            tablas.append(
                TablaBD(
                    nombre=str(
                        tabla_data.get(
                            "nombre",
                            "",
                        )
                    ),
                    descripcion=str(
                        tabla_data.get(
                            "descripcion",
                            "",
                        )
                    ),
                    campos=campos,
                    clave_primaria=[
                        str(item)
                        for item in (
                            tabla_data.get(
                                "clave_primaria",
                                [],
                            )
                            or []
                        )
                    ],
                    indices=[
                        [
                            str(campo)
                            for campo in indice
                        ]
                        for indice in (
                            tabla_data.get(
                                "indices",
                                [],
                            )
                            or []
                        )
                        if isinstance(
                            indice,
                            list,
                        )
                    ],
                )
            )

        relaciones = []

        for relacion_data in (
            datos.get(
                "relaciones",
                [],
            )
            or []
        ):

            if not isinstance(
                relacion_data,
                dict,
            ):
                continue

            relaciones.append(
                RelacionBD(
                    origen_tabla=str(
                        relacion_data.get(
                            "origen_tabla",
                            "",
                        )
                    ),
                    origen_campo=str(
                        relacion_data.get(
                            "origen_campo",
                            "",
                        )
                    ),
                    destino_tabla=str(
                        relacion_data.get(
                            "destino_tabla",
                            "",
                        )
                    ),
                    destino_campo=str(
                        relacion_data.get(
                            "destino_campo",
                            "",
                        )
                    ),
                    tipo=str(
                        relacion_data.get(
                            "tipo",
                            "",
                        )
                    ),
                    on_delete=str(
                        relacion_data.get(
                            "on_delete",
                            "restrict",
                        )
                    ),
                    on_update=str(
                        relacion_data.get(
                            "on_update",
                            "cascade",
                        )
                    ),
                )
            )

        return ModeloBaseDatos(
            motor=str(
                datos.get(
                    "motor",
                    "sqlite",
                )
            ),
            nombre=str(
                datos.get(
                    "nombre",
                    "app_db",
                )
            ),
            tablas=tablas,
            relaciones=relaciones,
            decisiones=[
                str(item)
                for item in (
                    datos.get(
                        "decisiones",
                        [],
                    )
                    or []
                )
            ],
            estrategia_migraciones=str(
                datos.get(
                    "estrategia_migraciones",
                    "",
                )
            ),
            estrategia_backup=str(
                datos.get(
                    "estrategia_backup",
                    "",
                )
            ),
            estrategia_integridad=[
                str(item)
                for item in (
                    datos.get(
                        "estrategia_integridad",
                        [],
                    )
                    or []
                )
            ],
        )

    # =========================================================
    # PLAN
    # =========================================================

    @staticmethod
    def _estado_tarea(
        valor: str,
    ) -> EstadoTarea:

        try:
            return EstadoTarea(
                str(
                    valor
                )
            )
        except ValueError:
            return EstadoTarea.PENDIENTE

    @classmethod
    def _tarea(
        cls,
        datos: dict,
    ) -> TareaSoftware:

        return TareaSoftware(
            id=str(
                datos.get(
                    "id",
                    "",
                )
            ),
            titulo=str(
                datos.get(
                    "titulo",
                    "Tarea",
                )
            ),
            descripcion=str(
                datos.get(
                    "descripcion",
                    "",
                )
            ),
            tipo=str(
                datos.get(
                    "tipo",
                    "implementacion",
                )
            ),
            prioridad=float(
                datos.get(
                    "prioridad",
                    0.5,
                )
                or 0.5
            ),
            depende_de=[
                str(item)
                for item in (
                    datos.get(
                        "depende_de",
                        [],
                    )
                    or []
                )
            ],
            criterios_aceptacion=[
                str(item)
                for item in (
                    datos.get(
                        "criterios_aceptacion",
                        [],
                    )
                    or []
                )
            ],
            archivos_estimados=[
                str(item)
                for item in (
                    datos.get(
                        "archivos_estimados",
                        [],
                    )
                    or []
                )
            ],
            lenguaje=(
                str(
                    datos[
                        "lenguaje"
                    ]
                )
                if datos.get(
                    "lenguaje"
                )
                else None
            ),
            tecnologia=(
                str(
                    datos[
                        "tecnologia"
                    ]
                )
                if datos.get(
                    "tecnologia"
                )
                else None
            ),
            requiere_pruebas=bool(
                datos.get(
                    "requiere_pruebas",
                    True,
                )
            ),
            requiere_documentacion=bool(
                datos.get(
                    "requiere_documentacion",
                    False,
                )
            ),
            estado=cls._estado_tarea(
                str(
                    datos.get(
                        "estado",
                        "pendiente",
                    )
                )
            ),
        )

    @classmethod
    def _plan(
        cls,
        datos: dict,
        ruta_plan: Path,
    ) -> PlanSistemaSoftware:

        fases = []

        for fase_data in (
            datos.get(
                "fases",
                [],
            )
            or []
        ):

            if not isinstance(
                fase_data,
                dict,
            ):
                continue

            epicas = []

            for epica_data in (
                fase_data.get(
                    "epicas",
                    [],
                )
                or []
            ):

                if not isinstance(
                    epica_data,
                    dict,
                ):
                    continue

                tareas = [
                    cls._tarea(
                        tarea_data
                    )
                    for tarea_data in (
                        epica_data.get(
                            "tareas",
                            [],
                        )
                        or []
                    )
                    if isinstance(
                        tarea_data,
                        dict,
                    )
                ]

                epicas.append(
                    EpicaSoftware(
                        id=str(
                            epica_data.get(
                                "id",
                                "",
                            )
                        ),
                        nombre=str(
                            epica_data.get(
                                "nombre",
                                "Épica",
                            )
                        ),
                        descripcion=str(
                            epica_data.get(
                                "descripcion",
                                "",
                            )
                        ),
                        prioridad=float(
                            epica_data.get(
                                "prioridad",
                                0.5,
                            )
                            or 0.5
                        ),
                        tareas=tareas,
                    )
                )

            fases.append(
                FaseSoftware(
                    id=str(
                        fase_data.get(
                            "id",
                            "",
                        )
                    ),
                    nombre=str(
                        fase_data.get(
                            "nombre",
                            "Fase",
                        )
                    ),
                    objetivo=str(
                        fase_data.get(
                            "objetivo",
                            "",
                        )
                    ),
                    orden=int(
                        fase_data.get(
                            "orden",
                            len(
                                fases
                            )
                            + 1,
                        )
                        or (
                            len(
                                fases
                            )
                            + 1
                        )
                    ),
                    epicas=epicas,
                )
            )

        return PlanSistemaSoftware(
            id=str(
                datos.get(
                    "id",
                    "",
                )
            ),
            nombre_proyecto=str(
                datos.get(
                    "nombre_proyecto",
                    "Proyecto",
                )
            ),
            tipo_solucion=str(
                datos.get(
                    "tipo_solucion",
                    "desconocido",
                )
            ),
            arquitectura=str(
                datos.get(
                    "arquitectura",
                    "monolito_modular",
                )
            ),
            complejidad=str(
                datos.get(
                    "complejidad",
                    "media",
                )
            ),
            fases=fases,
            ruta_persistencia=str(
                ruta_plan
            ),
        )

    # =========================================================
    # RESTAURAR
    # =========================================================

    def restaurar(
        self,
        carpeta_proyecto: str | Path,
        proyecto_id: str,
    ) -> ResultadoRestauracionDesarrollo:

        carpeta = Path(
            carpeta_proyecto
        ).resolve()

        carpeta_atenas = (
            carpeta
            / ".atenas"
        )

        if not carpeta.exists():

            return ResultadoRestauracionDesarrollo(
                ok=False,
                proyecto_id=proyecto_id,
                carpeta_proyecto=str(
                    carpeta
                ),
                error=(
                    "carpeta_proyecto_no_existe"
                ),
            )

        if not carpeta_atenas.exists():

            return ResultadoRestauracionDesarrollo(
                ok=False,
                proyecto_id=proyecto_id,
                carpeta_proyecto=str(
                    carpeta
                ),
                error=(
                    "carpeta_atenas_no_existe"
                ),
            )

        try:

            datos_analisis = (
                self._leer_json(
                    carpeta_atenas
                    / "analisis_requisitos.json"
                )
            )

            datos_arquitectura = (
                self._leer_json(
                    carpeta_atenas
                    / "arquitectura.json"
                )
            )

            datos_bd = (
                self._leer_json(
                    carpeta_atenas
                    / "modelo_datos.json",
                    requerido=False,
                )
            )

            ruta_plan = (
                carpeta_atenas
                / "plan_software.json"
            )

            datos_plan = (
                self._leer_json(
                    ruta_plan
                )
            )

            analisis = (
                self._analisis(
                    datos_analisis
                )
            )

            arquitectura = (
                self._arquitectura(
                    datos_arquitectura
                )
            )

            modelo_bd = (
                self._modelo_bd(
                    datos_bd
                )
            )

            plan = (
                self._plan(
                    datos_plan,
                    ruta_plan,
                )
            )

            gestor_estado = (
                GestorEstadoProyectoSoftware(
                    carpeta
                )
            )

            estado = (
                gestor_estado.cargar()
            )

            contexto = (
                ResultadoInicioDesarrollo(
                    ok=True,
                    proyecto_id=proyecto_id,
                    carpeta_proyecto=str(
                        carpeta
                    ),
                    analisis=analisis,
                    arquitectura=arquitectura,
                    modelo_bd=modelo_bd,
                    plan=plan,
                    estado=estado,
                    base_datos=None,
                    documentacion=None,
                )
            )

            return ResultadoRestauracionDesarrollo(
                ok=True,
                proyecto_id=proyecto_id,
                carpeta_proyecto=str(
                    carpeta
                ),
                contexto=contexto,
            )

        except Exception as error:

            return ResultadoRestauracionDesarrollo(
                ok=False,
                proyecto_id=proyecto_id,
                carpeta_proyecto=str(
                    carpeta
                ),
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )