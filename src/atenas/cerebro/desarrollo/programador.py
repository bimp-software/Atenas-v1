from __future__ import annotations

import json
import re

from dataclasses import dataclass

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from .diagnostico import (
    DiagnosticoError,
    DiagnosticoCodigo,
)

from .inspector_codigo import (
    InspectorCodigo,
)

from .mapa_proyecto import (
    MapaProyecto,
)

from .parche import (
    CambioCodigo,
    GestorParches,
)

from .politica import (
    PoliticaDesarrollo,
)


@dataclass
class ResultadoProgramacion:
    ok: bool

    cambio: CambioCodigo | None

    mensaje: str

    respuesta_llm: str = ""

    error: str | None = None


class ProgramadorAtenas:
    """
    Genera propuestas de modificación de código.

    NO aplica cambios.

    El resultado siempre pasa posteriormente por:
    GestorParches -> Sandbox -> Tests -> Verificador.
    """

    MAX_CARACTERES_ARCHIVO = (
        30_000
    )

    MAX_ARCHIVOS_CONTEXTO = 5

    def __init__(
        self,
        llm: OllamaClient,
        inspector: InspectorCodigo,
        diagnostico: DiagnosticoCodigo,
        mapa: MapaProyecto,
        politica: PoliticaDesarrollo,
        gestor_parches: GestorParches,
    ):
        self.llm = llm

        self.inspector = inspector
        self.diagnostico = diagnostico
        self.mapa = mapa

        self.politica = politica

        self.gestor_parches = (
            gestor_parches
        )

    # =========================================================
    # EXTRAER JSON
    # =========================================================

    @staticmethod
    def _extraer_json(
        texto: str,
    ) -> dict:

        texto = (
            texto
            or ""
        ).strip()

        # ---------------------------------------------
        # ```json ... ```
        # ---------------------------------------------

        bloque = re.search(
            r"```(?:json)?\s*(\{.*\})\s*```",
            texto,
            re.DOTALL,
        )

        if bloque:

            texto_json = (
                bloque.group(1)
            )

        else:

            inicio = texto.find(
                "{"
            )

            fin = texto.rfind(
                "}"
            )

            if (
                inicio == -1
                or fin == -1
                or fin <= inicio
            ):

                raise ValueError(
                    "El LLM no devolvió "
                    "un objeto JSON."
                )

            texto_json = (
                texto[
                    inicio:
                    fin + 1
                ]
            )

        resultado = json.loads(
            texto_json
        )

        if not isinstance(
            resultado,
            dict,
        ):

            raise ValueError(
                "El resultado del LLM "
                "no es un objeto."
            )

        return resultado

    # =========================================================
    # LLAMAR LLM
    # =========================================================

    def _preguntar_llm(
        self,
        mensajes: list[dict],
    ) -> str:

        # Compatibilidad con clientes que ya
        # implementan chat().
        if hasattr(
            self.llm,
            "chat",
        ):

            resultado = (
                self.llm.chat(
                    mensajes
                )
            )

            if isinstance(
                resultado,
                str,
            ):
                return resultado

            if isinstance(
                resultado,
                dict,
            ):

                mensaje = (
                    resultado.get(
                        "message"
                    )
                    or {}
                )

                contenido = (
                    mensaje.get(
                        "content"
                    )
                    if isinstance(
                        mensaje,
                        dict,
                    )
                    else None
                )

                if contenido:
                    return str(
                        contenido
                    )

                if resultado.get(
                    "content"
                ):

                    return str(
                        resultado[
                            "content"
                        ]
                    )

        # ---------------------------------------------
        # Streaming
        # ---------------------------------------------

        if hasattr(
            self.llm,
            "chat_stream",
        ):

            partes = []

            for fragmento in (
                self.llm.chat_stream(
                    mensajes
                )
            ):

                partes.append(
                    str(fragmento)
                )

            return "".join(
                partes
            )

        raise RuntimeError(
            "OllamaClient no expone "
            "chat() ni chat_stream()."
        )

    # =========================================================
    # LEER CONTEXTO
    # =========================================================

    def _archivos_para_diagnostico(
        self,
        diagnostico: DiagnosticoError,
    ) -> list[dict]:

        rutas = []

        if diagnostico.archivo_principal:

            rutas.append(
                diagnostico
                .archivo_principal
            )

        rutas.extend(
            diagnostico
            .archivos_relacionados
        )

        # Quitar duplicados respetando orden.
        rutas = list(
            dict.fromkeys(
                rutas
            )
        )

        resultados = []

        for ruta in rutas[
            :self.MAX_ARCHIVOS_CONTEXTO
        ]:

            lectura = (
                self.inspector
                .leer_archivo(
                    ruta
                )
            )

            if not lectura.get(
                "ok"
            ):
                continue

            contenido = (
                lectura[
                    "contenido"
                ]
            )

            if (
                len(contenido)
                > self.MAX_CARACTERES_ARCHIVO
            ):

                contenido = (
                    contenido[
                        :self.MAX_CARACTERES_ARCHIVO
                    ]
                    + "\n\n"
                    "# [CONTENIDO RECORTADO]"
                )

            resultados.append({
                "ruta": ruta,
                "contenido": contenido,
            })

        return resultados

    # =========================================================
    # PROMPT
    # =========================================================

    def _crear_prompt(
        self,
        diagnostico: DiagnosticoError,
        archivos: list[dict],
    ) -> list[dict]:

        bloques_codigo = []

        for archivo in archivos:

            bloques_codigo.append(
                (
                    f"ARCHIVO: {archivo['ruta']}\n"
                    "```python\n"
                    f"{archivo['contenido']}\n"
                    "```"
                )
            )

        contexto_codigo = (
            "\n\n".join(
                bloques_codigo
            )
        )

        diagnostico_texto = (
            self.diagnostico
            .contexto_para_llm(
                diagnostico
            )
        )

        system = """
Eres el módulo interno ProgramadorAtenas.

Tu trabajo es PROPONER una corrección mínima
para un error detectado en el proyecto ATENAS.

No ejecutas código.
No ejecutas comandos.
No modificas archivos.
No inventas archivos que no aparecen en el contexto.

Debes modificar como máximo UN archivo por respuesta.

Prioriza:
1. corregir la causa raíz;
2. realizar el cambio mínimo;
3. conservar APIs existentes;
4. no introducir dependencias nuevas;
5. no modificar archivos protegidos;
6. no eliminar funcionalidades innecesariamente.

Devuelve ÚNICAMENTE JSON válido.

Formato obligatorio:

{
    "archivo": "ruta/archivo.py",
    "razon": "explicación breve",
    "contenido_nuevo": "contenido COMPLETO del archivo"
}

contenido_nuevo debe contener el archivo completo corregido.

No uses Markdown.
No uses ```python.
No agregues texto fuera del JSON.
""".strip()

        usuario = f"""
{diagnostico_texto}

CÓDIGO DISPONIBLE:

{contexto_codigo}

Genera la corrección mínima necesaria.
""".strip()

        return [
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": usuario,
            },
        ]

    # =========================================================
    # CREAR CORRECCIÓN
    # =========================================================

    def proponer_correccion(
        self,
        diagnostico: DiagnosticoError,
    ) -> ResultadoProgramacion:

        archivos = (
            self._archivos_para_diagnostico(
                diagnostico
            )
        )

        if not archivos:

            return ResultadoProgramacion(
                ok=False,
                cambio=None,
                mensaje=(
                    "No fue posible obtener "
                    "código relacionado."
                ),
            )

        mensajes = (
            self._crear_prompt(
                diagnostico=diagnostico,
                archivos=archivos,
            )
        )

        try:

            respuesta = (
                self._preguntar_llm(
                    mensajes
                )
            )

        except Exception as error:

            return ResultadoProgramacion(
                ok=False,
                cambio=None,

                mensaje=(
                    "Falló la comunicación "
                    "con el LLM."
                ),

                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        # =====================================================
        # JSON
        # =====================================================

        try:

            datos = (
                self._extraer_json(
                    respuesta
                )
            )

        except Exception as error:

            return ResultadoProgramacion(
                ok=False,
                cambio=None,

                mensaje=(
                    "La respuesta del LLM "
                    "no tiene formato válido."
                ),

                respuesta_llm=(
                    respuesta
                ),

                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        archivo = str(
            datos.get(
                "archivo",
                "",
            )
        ).strip()

        razon = str(
            datos.get(
                "razon",
                "",
            )
        ).strip()

        contenido_nuevo = datos.get(
            "contenido_nuevo"
        )

        if not archivo:

            return ResultadoProgramacion(
                ok=False,
                cambio=None,
                mensaje=(
                    "El LLM no indicó "
                    "el archivo."
                ),
                respuesta_llm=respuesta,
            )

        if not isinstance(
            contenido_nuevo,
            str,
        ):

            return ResultadoProgramacion(
                ok=False,
                cambio=None,
                mensaje=(
                    "contenido_nuevo "
                    "no es texto."
                ),
                respuesta_llm=respuesta,
            )

        # =====================================================
        # SOLO ARCHIVOS DEL CONTEXTO
        # =====================================================

        rutas_permitidas = {
            item["ruta"]
            for item in archivos
        }

        if archivo not in rutas_permitidas:

            return ResultadoProgramacion(
                ok=False,
                cambio=None,

                mensaje=(
                    "El LLM intentó modificar "
                    "un archivo fuera del "
                    "contexto autorizado."
                ),

                respuesta_llm=(
                    respuesta
                ),
            )

        # =====================================================
        # POLÍTICA
        # =====================================================

        evaluacion = (
            self.politica
            .evaluar_modificacion(
                archivo
            )
        )

        if not evaluacion.permitido:

            return ResultadoProgramacion(
                ok=False,
                cambio=None,

                mensaje=(
                    "La política bloqueó "
                    "la modificación: "
                    + evaluacion.motivo
                ),

                respuesta_llm=(
                    respuesta
                ),
            )

        # =====================================================
        # ORIGINAL
        # =====================================================

        original = next(
            (
                item["contenido"]
                for item in archivos
                if item["ruta"]
                == archivo
            ),
            None,
        )

        if original is None:

            return ResultadoProgramacion(
                ok=False,
                cambio=None,
                mensaje=(
                    "No se encontró "
                    "el contenido original."
                ),
                respuesta_llm=respuesta,
            )

        cambio = (
            self.gestor_parches
            .preparar_cambio(
                archivo=archivo,
                contenido_original=(
                    original
                ),
                contenido_nuevo=(
                    contenido_nuevo
                ),
                razon=(
                    razon
                    or "Corrección automática."
                ),
            )
        )

        return ResultadoProgramacion(
            ok=True,

            cambio=cambio,

            mensaje=(
                "Propuesta de corrección "
                "generada."
            ),

            respuesta_llm=(
                respuesta
            ),
        )