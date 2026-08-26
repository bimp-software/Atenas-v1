from __future__ import annotations

import re
import uuid

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .tareas_escritorio import (
    PasoTareaEscritorio,
    TipoPasoEscritorio,
)


@dataclass
class PlanTareaEscritorio:
    nombre: str
    descripcion: str

    pasos: list[PasoTareaEscritorio] = field(
        default_factory=list
    )

    prioridad: float = 0.70

    confianza: float = 0.0

    contexto: dict[str, Any] = field(
        default_factory=dict
    )

    advertencias: list[str] = field(
        default_factory=list
    )


class PlanificadorTareasEscritorio:
    """
    Convierte un objetivo amplio en una tarea de escritorio persistente.

    Esta primera versión NO necesita un LLM para ser operativa.
    Usa recetas estructuradas y contexto conocido.

    Objetivos:
    - preparar una entrega;
    - revisar/preparar un proyecto;
    - abrir un proyecto para trabajar;
    - organizar una carpeta;
    - documentar una solución;
    - preparar archivos para un cliente.

    Más adelante puede recibir un planificador LLM, pero los pasos
    siempre deben terminar convertidos a TipoPasoEscritorio permitido.
    """

    def __init__(
        self,
        carpeta_clientes: str | Path | None = None,
    ):
        home = Path.home()

        self.escritorio = (
            home
            / "Desktop"
        ).resolve()

        self.documentos = (
            home
            / "Documents"
        ).resolve()

        self.carpeta_clientes = Path(
            carpeta_clientes
            or (
                self.escritorio
                / "Clientes"
            )
        ).expanduser().resolve()

    # =========================================================
    # UTILIDADES
    # =========================================================

    @staticmethod
    def _id_paso(
        prefijo: str,
    ) -> str:

        return (
            f"{prefijo}_"
            f"{uuid.uuid4().hex[:8]}"
        )

    @staticmethod
    def _normalizar(
        texto: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            (
                texto
                or ""
            ).strip(),
        )

    @staticmethod
    def _ruta_contexto(
        contexto: dict[str, Any],
    ) -> Path | None:

        candidatos = (
            "ruta_proyecto",
            "carpeta_proyecto",
            "ruta",
            "directorio",
        )

        for clave in candidatos:

            valor = contexto.get(
                clave
            )

            if not valor:
                continue

            try:

                return Path(
                    str(
                        valor
                    )
                ).expanduser().resolve()

            except Exception:

                continue

        return None

    @staticmethod
    def _titulo_contexto(
        contexto: dict[str, Any],
    ) -> str | None:

        for clave in (
            "ventana",
            "titulo_ventana",
            "aplicacion",
        ):

            valor = contexto.get(
                clave
            )

            if valor:

                return str(
                    valor
                )

        return None

    # =========================================================
    # PASOS REUTILIZABLES
    # =========================================================

    def _pasos_abrir_proyecto(
        self,
        ruta: Path,
    ) -> list[PasoTareaEscritorio]:

        return [
            PasoTareaEscritorio(
                id=self._id_paso(
                    "verificar_carpeta"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .VERIFICAR_CARPETA
                ),
                descripcion=(
                    "Comprobar que la carpeta del proyecto existe."
                ),
                argumentos={
                    "ruta":
                        str(
                            ruta
                        )
                },
            ),

            PasoTareaEscritorio(
                id=self._id_paso(
                    "abrir_ruta"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .ABRIR_RUTA
                ),
                descripcion=(
                    "Abrir la carpeta del proyecto."
                ),
                argumentos={
                    "ruta":
                        str(
                            ruta
                        )
                },
            ),

            PasoTareaEscritorio(
                id=self._id_paso(
                    "abrir_vscode"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .ABRIR_APLICACION
                ),
                descripcion=(
                    "Abrir Visual Studio Code."
                ),
                argumentos={
                    "alias":
                        "vscode",

                    "argumentos": [
                        str(
                            ruta
                        )
                    ],
                },
            ),

            PasoTareaEscritorio(
                id=self._id_paso(
                    "esperar_vscode"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .ESPERAR_VENTANA
                ),
                descripcion=(
                    "Esperar que Visual Studio Code esté disponible."
                ),
                argumentos={
                    "titulo":
                        "Visual Studio Code",

                    "timeout":
                        12,
                },
            ),

            PasoTareaEscritorio(
                id=self._id_paso(
                    "observar"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .OBSERVAR
                ),
                descripcion=(
                    "Observar el estado visual del escritorio."
                ),
            ),

            PasoTareaEscritorio(
                id=self._id_paso(
                    "interpretar"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .INTERPRETAR_ESCENA
                ),
                descripcion=(
                    "Interpretar visualmente el entorno de trabajo."
                ),
                argumentos={
                    "usar_modelo_vision":
                        True
                },
            ),
        ]

    def _pasos_documentacion_basica(
        self,
        ruta: Path,
        descripcion: str,
    ) -> list[PasoTareaEscritorio]:

        readme = (
            ruta
            / "README_ATENAS.md"
        )

        contenido = (
            "# Documentación preparada por ATENAS\n\n"
            "## Objetivo\n\n"
            f"{descripcion}\n\n"
            "## Estado\n\n"
            "- Documento inicial generado automáticamente.\n"
            "- Requiere enriquecimiento con la documentación "
            "técnica específica del proyecto.\n"
        )

        return [
            PasoTareaEscritorio(
                id=self._id_paso(
                    "crear_documentacion"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .ESCRIBIR_ARCHIVO
                ),
                descripcion=(
                    "Crear un documento base de entrega."
                ),
                argumentos={
                    "ruta":
                        str(
                            readme
                        ),

                    "contenido":
                        contenido,

                    "sobrescribir":
                        False,
                },
            ),

            PasoTareaEscritorio(
                id=self._id_paso(
                    "verificar_documentacion"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .VERIFICAR_ARCHIVO
                ),
                descripcion=(
                    "Comprobar que la documentación fue creada."
                ),
                argumentos={
                    "ruta":
                        str(
                            readme
                        )
                },
            ),
        ]

    # =========================================================
    # RECETAS
    # =========================================================

    def _plan_preparar_entrega(
        self,
        objetivo: str,
        contexto: dict[str, Any],
    ) -> PlanTareaEscritorio:

        ruta = self._ruta_contexto(
            contexto
        )

        advertencias = []
        pasos = []

        if ruta is not None:

            pasos.extend(
                self._pasos_abrir_proyecto(
                    ruta
                )
            )

            pasos.extend(
                self._pasos_documentacion_basica(
                    ruta,
                    objetivo,
                )
            )

            pasos.append(
                PasoTareaEscritorio(
                    id=self._id_paso(
                        "verificar_proyecto"
                    ),
                    tipo=(
                        TipoPasoEscritorio
                        .VERIFICAR_CARPETA
                    ),
                    descripcion=(
                        "Verificar nuevamente la carpeta antes de finalizar."
                    ),
                    argumentos={
                        "ruta":
                            str(
                                ruta
                            )
                    },
                )
            )

            confianza = 0.92

        else:

            advertencias.append(
                (
                    "No hay una ruta de proyecto conocida. "
                    "Se creó una fase inicial de observación "
                    "antes de modificar archivos."
                )
            )

            pasos.extend([
                PasoTareaEscritorio(
                    id=self._id_paso(
                        "observar"
                    ),
                    tipo=(
                        TipoPasoEscritorio
                        .OBSERVAR
                    ),
                    descripcion=(
                        "Observar el escritorio para recuperar contexto."
                    ),
                ),

                PasoTareaEscritorio(
                    id=self._id_paso(
                        "interpretar"
                    ),
                    tipo=(
                        TipoPasoEscritorio
                        .INTERPRETAR_ESCENA
                    ),
                    descripcion=(
                        "Interpretar el entorno antes de continuar."
                    ),
                    argumentos={
                        "usar_modelo_vision":
                            True
                    },
                ),
            ])

            confianza = 0.62

        return PlanTareaEscritorio(
            nombre="Preparar entrega",
            descripcion=objetivo,
            pasos=pasos,
            prioridad=0.86,
            confianza=confianza,
            contexto=contexto,
            advertencias=advertencias,
        )

    def _plan_trabajar_proyecto(
        self,
        objetivo: str,
        contexto: dict[str, Any],
    ) -> PlanTareaEscritorio:

        ruta = self._ruta_contexto(
            contexto
        )

        if ruta is None:

            return PlanTareaEscritorio(
                nombre="Recuperar contexto del proyecto",
                descripcion=objetivo,
                pasos=[
                    PasoTareaEscritorio(
                        id=self._id_paso(
                            "observar"
                        ),
                        tipo=(
                            TipoPasoEscritorio
                            .OBSERVAR
                        ),
                        descripcion=(
                            "Observar el entorno actual."
                        ),
                    ),

                    PasoTareaEscritorio(
                        id=self._id_paso(
                            "interpretar"
                        ),
                        tipo=(
                            TipoPasoEscritorio
                            .INTERPRETAR_ESCENA
                        ),
                        descripcion=(
                            "Interpretar la escena para localizar "
                            "el proyecto activo."
                        ),
                        argumentos={
                            "usar_modelo_vision":
                                True
                        },
                    ),
                ],
                prioridad=0.78,
                confianza=0.60,
                contexto=contexto,
                advertencias=[
                    (
                        "ATENAS todavía no conoce la ruta del proyecto."
                    )
                ],
            )

        return PlanTareaEscritorio(
            nombre=(
                f"Trabajar en {ruta.name}"
            ),
            descripcion=objetivo,
            pasos=self._pasos_abrir_proyecto(
                ruta
            ),
            prioridad=0.82,
            confianza=0.93,
            contexto=contexto,
        )

    def _plan_organizar_carpeta(
        self,
        objetivo: str,
        contexto: dict[str, Any],
    ) -> PlanTareaEscritorio:

        ruta = self._ruta_contexto(
            contexto
        )

        if ruta is None:

            ruta = (
                self.documentos
                / "ATENAS_Organizacion"
            )

        pasos = [
            PasoTareaEscritorio(
                id=self._id_paso(
                    "crear_carpeta"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .CREAR_CARPETA
                ),
                descripcion=(
                    "Asegurar que la carpeta de trabajo exista."
                ),
                argumentos={
                    "ruta":
                        str(
                            ruta
                        )
                },
            ),

            PasoTareaEscritorio(
                id=self._id_paso(
                    "verificar_carpeta"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .VERIFICAR_CARPETA
                ),
                descripcion=(
                    "Verificar la carpeta de trabajo."
                ),
                argumentos={
                    "ruta":
                        str(
                            ruta
                        )
                },
            ),

            PasoTareaEscritorio(
                id=self._id_paso(
                    "abrir_carpeta"
                ),
                tipo=(
                    TipoPasoEscritorio
                    .ABRIR_RUTA
                ),
                descripcion=(
                    "Abrir la carpeta organizada."
                ),
                argumentos={
                    "ruta":
                        str(
                            ruta
                        )
                },
            ),
        ]

        return PlanTareaEscritorio(
            nombre="Organizar carpeta de trabajo",
            descripcion=objetivo,
            pasos=pasos,
            prioridad=0.72,
            confianza=0.82,
            contexto={
                **contexto,
                "ruta":
                    str(
                        ruta
                    ),
            },
        )

    # =========================================================
    # PLAN GENERAL
    # =========================================================

    def planificar(
        self,
        objetivo: str,
        contexto: dict[str, Any] | None = None,
    ) -> PlanTareaEscritorio:

        objetivo = self._normalizar(
            objetivo
        )

        contexto = dict(
            contexto
            or {}
        )

        texto = objetivo.lower()

        if any(
            frase in texto
            for frase in (
                "preparar para entregar",
                "prepara para entregar",
                "preparar entrega",
                "prepara la entrega",
                "entregar al cliente",
                "entrega del proyecto",
                "prepara este proyecto",
            )
        ):

            return self._plan_preparar_entrega(
                objetivo,
                contexto,
            )

        if any(
            frase in texto
            for frase in (
                "trabaja en el proyecto",
                "continuar trabajando",
                "continúa trabajando",
                "abre el proyecto",
                "revisa el proyecto",
                "prepara el proyecto",
            )
        ):

            return self._plan_trabajar_proyecto(
                objetivo,
                contexto,
            )

        if any(
            frase in texto
            for frase in (
                "organiza una carpeta",
                "organizar carpeta",
                "organiza los archivos",
                "prepara una carpeta",
            )
        ):

            return self._plan_organizar_carpeta(
                objetivo,
                contexto,
            )

        # Fallback conservador: primero observar e interpretar.
        return PlanTareaEscritorio(
            nombre="Analizar objetivo de escritorio",
            descripcion=objetivo,
            pasos=[
                PasoTareaEscritorio(
                    id=self._id_paso(
                        "observar"
                    ),
                    tipo=(
                        TipoPasoEscritorio
                        .OBSERVAR
                    ),
                    descripcion=(
                        "Observar el estado actual antes de actuar."
                    ),
                ),

                PasoTareaEscritorio(
                    id=self._id_paso(
                        "interpretar"
                    ),
                    tipo=(
                        TipoPasoEscritorio
                        .INTERPRETAR_ESCENA
                    ),
                    descripcion=(
                        "Interpretar visualmente el entorno."
                    ),
                    argumentos={
                        "usar_modelo_vision":
                            True
                    },
                ),
            ],
            prioridad=0.68,
            confianza=0.55,
            contexto=contexto,
            advertencias=[
                (
                    "No existe todavía una receta específica "
                    "para este objetivo; se generó una fase "
                    "inicial de percepción."
                )
            ],
        )