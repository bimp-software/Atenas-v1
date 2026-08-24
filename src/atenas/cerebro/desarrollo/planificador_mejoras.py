from __future__ import annotations

import json
import re

from dataclasses import dataclass
from typing import Any

from .automejora import (
    HallazgoMejora,
)

from .inspector_codigo import (
    InspectorCodigo,
)

from .parche import (
    CambioCodigo,
    GestorParches,
)

from .politica import (
    PoliticaDesarrollo,
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
class PropuestaMejora:
    ok: bool

    hallazgo: HallazgoMejora

    cambio: CambioCodigo | None = None

    sandbox: ResultadoSandbox | None = None

    verificacion: ResultadoVerificacion | None = None

    mensaje: str = ""

    respuesta_llm: str = ""

    error: str | None = None

    aplicada: bool = False


class PlanificadorMejoras:
    """
    Convierte un HallazgoMejora en una propuesta verificable.

    Flujo:

        HallazgoMejora
            ↓
        leer archivo real
            ↓
        Qwen propone refactor
            ↓
        CambioCodigo
            ↓
        SandboxCodigo
            ↓
        tests
            ↓
        VerificadorCambio
            ↓
        PropuestaMejora

    IMPORTANTE:

    - NO aplica cambios al proyecto real.
    - Solo puede modificar el archivo del hallazgo.
    - Respeta PoliticaDesarrollo.
    - Toda propuesta debe superar sandbox y verificación.
    """

    MAX_CARACTERES_ARCHIVO = 40_000

    def __init__(
        self,
        llm: Any,
        inspector: InspectorCodigo,
        politica: PoliticaDesarrollo,
        gestor_parches: GestorParches,
        sandbox: SandboxCodigo,
        verificador: VerificadorCambio,
    ):
        self.llm = llm
        self.inspector = inspector
        self.politica = politica
        self.gestor_parches = gestor_parches
        self.sandbox = sandbox
        self.verificador = verificador

    # =========================================================
    # JSON
    # =========================================================

    @staticmethod
    def _extraer_json(
        texto: str,
    ) -> dict:

        texto = (
            texto
            or ""
        ).strip()

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

            inicio = texto.find("{")
            fin = texto.rfind("}")

            if (
                inicio == -1
                or fin == -1
                or fin <= inicio
            ):

                raise ValueError(
                    "El LLM no devolvió JSON válido."
                )

            texto_json = (
                texto[
                    inicio:
                    fin + 1
                ]
            )

        datos = json.loads(
            texto_json
        )

        if not isinstance(
            datos,
            dict,
        ):

            raise ValueError(
                "La respuesta debe ser un objeto JSON."
            )

        return datos

    # =========================================================
    # LLM
    # =========================================================

    def _preguntar_llm(
        self,
        mensajes: list[dict],
    ) -> str:

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

                message = (
                    resultado.get(
                        "message"
                    )
                    or {}
                )

                if isinstance(
                    message,
                    dict,
                ):

                    contenido = (
                        message.get(
                            "content"
                        )
                    )

                    if contenido:
                        return str(
                            contenido
                        )

                contenido = (
                    resultado.get(
                        "content"
                    )
                )

                if contenido:
                    return str(
                        contenido
                    )

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
            "El cliente LLM no expone "
            "chat() ni chat_stream()."
        )

    # =========================================================
    # PROMPT
    # =========================================================

    def _crear_prompt(
        self,
        hallazgo: HallazgoMejora,
        contenido: str,
    ) -> list[dict]:

        system = """
Eres el módulo interno de mejora de código de ATENAS.

Tu tarea es proponer una mejora PEQUEÑA, CONSERVADORA
y VERIFICABLE a partir de un hallazgo estático.

REGLAS:

- Modifica únicamente el archivo indicado.
- Conserva el comportamiento observable existente.
- No cambies APIs públicas sin necesidad.
- No elimines funciones necesarias.
- No introduzcas dependencias nuevas.
- No uses eval, exec, os.system ni mecanismos equivalentes.
- No modifiques archivos protegidos.
- No afirmes que el cambio fue aplicado.
- Devuelve el archivo COMPLETO.
- Si el hallazgo no puede corregirse de forma segura en un
  solo archivo, responde con "puede_mejorarse": false.

Devuelve ÚNICAMENTE JSON válido:

{
    "puede_mejorarse": true,
    "archivo": "ruta/al/archivo.py",
    "razon": "motivo breve",
    "contenido_nuevo": "archivo completo corregido"
}

o:

{
    "puede_mejorarse": false,
    "archivo": "ruta/al/archivo.py",
    "razon": "por qué no es seguro hacerlo automáticamente",
    "contenido_nuevo": ""
}
""".strip()

        usuario = f"""
HALLAZGO:

Tipo:
{hallazgo.tipo.value}

Archivo:
{hallazgo.archivo}

Símbolo:
{hallazgo.simbolo or "no especificado"}

Línea:
{hallazgo.linea or "no especificada"}

Descripción:
{hallazgo.descripcion}

Severidad:
{hallazgo.severidad:.2f}

Confianza:
{hallazgo.confianza:.2f}

Riesgo estimado:
{hallazgo.riesgo_estimado.value}

ARCHIVO ACTUAL:

```python
{contenido}
```

Propón una mejora mínima que preserve el comportamiento.
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
    # PROPONER
    # =========================================================

    def proponer(
        self,
        hallazgo: HallazgoMejora,
        tests: list[str] | None = None,
    ) -> PropuestaMejora:

        # =====================================================
        # POLÍTICA
        # =====================================================

        evaluacion = (
            self.politica
            .evaluar_modificacion(
                hallazgo.archivo
            )
        )

        if not evaluacion.permitido:

            return PropuestaMejora(
                ok=False,
                hallazgo=hallazgo,
                mensaje=(
                    "La política bloqueó "
                    "el archivo."
                ),
                error=(
                    evaluacion.motivo
                ),
            )

        # =====================================================
        # LEER
        # =====================================================

        lectura = (
            self.inspector
            .leer_archivo(
                hallazgo.archivo
            )
        )

        if not lectura.get(
            "ok"
        ):

            return PropuestaMejora(
                ok=False,
                hallazgo=hallazgo,
                mensaje=(
                    "No fue posible leer "
                    "el archivo."
                ),
                error=(
                    lectura.get(
                        "error"
                    )
                ),
            )

        contenido_original = (
            lectura[
                "contenido"
            ]
        )

        if (
            len(contenido_original)
            > self.MAX_CARACTERES_ARCHIVO
        ):

            return PropuestaMejora(
                ok=False,
                hallazgo=hallazgo,
                mensaje=(
                    "El archivo es demasiado "
                    "grande para una propuesta "
                    "automática de un solo paso."
                ),
                error="archivo_demasiado_grande",
            )

        # =====================================================
        # QWEN
        # =====================================================

        mensajes = (
            self._crear_prompt(
                hallazgo=hallazgo,
                contenido=contenido_original,
            )
        )

        try:

            respuesta = (
                self._preguntar_llm(
                    mensajes
                )
            )

        except Exception as error:

            return PropuestaMejora(
                ok=False,
                hallazgo=hallazgo,
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

            return PropuestaMejora(
                ok=False,
                hallazgo=hallazgo,
                mensaje=(
                    "La respuesta del LLM "
                    "no pudo interpretarse."
                ),
                respuesta_llm=respuesta,
                error=(
                    f"{type(error).__name__}: "
                    f"{error}"
                ),
            )

        puede_mejorarse = bool(
            datos.get(
                "puede_mejorarse",
                False,
            )
        )

        archivo = str(
            datos.get(
                "archivo",
                "",
            )
            or ""
        ).strip()

        razon = str(
            datos.get(
                "razon",
                "",
            )
            or ""
        ).strip()

        contenido_nuevo = (
            datos.get(
                "contenido_nuevo"
            )
        )

        if not puede_mejorarse:

            return PropuestaMejora(
                ok=True,
                hallazgo=hallazgo,
                mensaje=(
                    razon
                    or "El hallazgo no puede "
                    "mejorarse de forma segura "
                    "en un solo paso."
                ),
                respuesta_llm=respuesta,
                aplicada=False,
            )

        if (
            archivo
            != hallazgo.archivo
        ):

            return PropuestaMejora(
                ok=False,
                hallazgo=hallazgo,
                mensaje=(
                    "El LLM intentó modificar "
                    "un archivo distinto al "
                    "autorizado."
                ),
                respuesta_llm=respuesta,
                error="archivo_no_autorizado",
            )

        if not isinstance(
            contenido_nuevo,
            str,
        ):

            return PropuestaMejora(
                ok=False,
                hallazgo=hallazgo,
                mensaje=(
                    "contenido_nuevo no es texto."
                ),
                respuesta_llm=respuesta,
                error="contenido_invalido",
            )

        if (
            contenido_nuevo
            == contenido_original
        ):

            return PropuestaMejora(
                ok=False,
                hallazgo=hallazgo,
                mensaje=(
                    "La propuesta no produce "
                    "ningún cambio."
                ),
                respuesta_llm=respuesta,
                error="sin_cambios",
            )

        # =====================================================
        # CAMBIO
        # =====================================================

        cambio = (
            self.gestor_parches
            .preparar_cambio(
                archivo=(
                    hallazgo.archivo
                ),
                contenido_original=(
                    contenido_original
                ),
                contenido_nuevo=(
                    contenido_nuevo
                ),
                razon=(
                    razon
                    or hallazgo.descripcion
                ),
            )
        )

        # =====================================================
        # SANDBOX
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

            return PropuestaMejora(
                ok=False,
                hallazgo=hallazgo,
                cambio=cambio,
                sandbox=resultado_sandbox,
                mensaje=(
                    "La propuesta no superó "
                    "el sandbox."
                ),
                respuesta_llm=respuesta,
                error="fallo_sandbox",
                aplicada=False,
            )

        # =====================================================
        # VERIFICADOR
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

            return PropuestaMejora(
                ok=False,
                hallazgo=hallazgo,
                cambio=cambio,
                sandbox=resultado_sandbox,
                verificacion=verificacion,
                mensaje=(
                    "La propuesta fue rechazada "
                    "por el verificador."
                ),
                respuesta_llm=respuesta,
                error="rechazada_verificador",
                aplicada=False,
            )

        return PropuestaMejora(
            ok=True,
            hallazgo=hallazgo,
            cambio=cambio,
            sandbox=resultado_sandbox,
            verificacion=verificacion,
            mensaje=(
                "Propuesta de mejora validada "
                "en sandbox. No fue aplicada "
                "al proyecto real."
            ),
            respuesta_llm=respuesta,
            aplicada=False,
        )