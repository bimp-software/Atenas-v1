from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class ClasificacionConsulta:
    requiere_conocimiento: bool
    permite_internet: bool
    tipo: str
    motivo: str


class ClasificadorConsulta:

    CONVERSACION = (
        "hola",
        "holi",
        "buenas",
        "que cuentas",
        "qué cuentas",
        "como estas",
        "cómo estás",
        "gracias",
        "no",
        "si",
        "sí",
        "adios",
        "adiós",
        "chao",
        "hasta luego",
    )

    IDENTIDAD_ATENAS = (
        "como te llamas",
        "cómo te llamas",
        "quien eres",
        "quién eres",
        "cual es tu nombre",
        "cuál es tu nombre",
    )

    CAPACIDADES = (
        "sabes ingles",
        "sabes inglés",
        "puedes hablar",
        "puedes escuchar",
        "puedes ver",
        "tienes memoria",
        "tienes internet",
    )

    INDICADORES_INFORMACION = (
        "necesito informacion",
        "necesito información",
        "busca",
        "investiga",
        "averigua",
        "cual es",
        "cuál es",
        "que es",
        "qué es",
        "explicame",
        "explícame",
        "informacion sobre",
        "información sobre",
    )

    INDICADORES_ACTUALIDAD = (
        "actual",
        "actualmente",
        "hoy",
        "ahora",
        "ultima",
        "última",
        "ultimo",
        "último",
        "noticias",
        "precio",
        "version actual",
        "versión actual",
    )

    def _normalizar(
        self,
        texto: str,
    ) -> str:

        texto = texto.lower().strip()

        texto = re.sub(
            r"[¿?¡!.,;:_]+",
            "",
            texto,
        )

        texto = re.sub(
            r"\s+",
            " ",
            texto,
        )

        return texto.strip()

    def clasificar(
        self,
        consulta: str,
    ) -> ClasificacionConsulta:

        texto = self._normalizar(
            consulta
        )

        # =====================================================
        # CONVERSACIÓN
        # =====================================================

        if texto in self.CONVERSACION:

            return ClasificacionConsulta(
                requiere_conocimiento=False,
                permite_internet=False,
                tipo="conversacion",
                motivo="Conversación casual.",
            )

        # =====================================================
        # IDENTIDAD DE ATENAS
        # =====================================================

        if any(
            frase in texto
            for frase in self.IDENTIDAD_ATENAS
        ):

            return ClasificacionConsulta(
                requiere_conocimiento=True,
                permite_internet=False,
                tipo="identidad",
                motivo=(
                    "La identidad debe resolverse "
                    "desde el estado interno."
                ),
            )

        # =====================================================
        # CAPACIDADES
        # =====================================================

        if any(
            frase in texto
            for frase in self.CAPACIDADES
        ):

            return ClasificacionConsulta(
                requiere_conocimiento=True,
                permite_internet=False,
                tipo="capacidad",
                motivo=(
                    "Las capacidades pertenecen "
                    "al estado interno de ATENAS."
                ),
            )

        # =====================================================
        # ACTUALIDAD
        # =====================================================

        if any(
            palabra in texto
            for palabra in self.INDICADORES_ACTUALIDAD
        ):

            return ClasificacionConsulta(
                requiere_conocimiento=True,
                permite_internet=True,
                tipo="actualidad",
                motivo=(
                    "La consulta puede depender "
                    "de información actual."
                ),
            )

        # =====================================================
        # SOLICITUD DE INFORMACIÓN
        # =====================================================

        if any(
            frase in texto
            for frase in self.INDICADORES_INFORMACION
        ):

            return ClasificacionConsulta(
                requiere_conocimiento=True,
                permite_internet=True,
                tipo="conocimiento",
                motivo=(
                    "La consulta solicita "
                    "información externa."
                ),
            )

        # =====================================================
        # PREGUNTA GENERAL
        # =====================================================

        if consulta.strip().endswith("?"):

            return ClasificacionConsulta(
                requiere_conocimiento=True,
                permite_internet=True,
                tipo="pregunta",
                motivo="Pregunta general.",
            )

        # =====================================================
        # DEFAULT
        # =====================================================

        return ClasificacionConsulta(
            requiere_conocimiento=False,
            permite_internet=False,
            tipo="conversacion",
            motivo=(
                "No se detectó necesidad clara "
                "de conocimiento externo."
            ),
        )