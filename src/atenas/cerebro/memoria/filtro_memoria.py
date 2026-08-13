from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ResultadoFiltroMemoria:
    guardar: bool
    motivo: str
    tipo: str
    score: float


class FiltroMemoria:
    """
    Decide si un mensaje del usuario merece convertirse
    en memoria persistente.

    No todo lo dicho durante una conversación debe formar
    parte del conocimiento de ATENAS.
    """

    INICIOS_PREGUNTA = (
        "qué ",
        "que ",
        "cómo ",
        "como ",
        "cuándo ",
        "cuando ",
        "dónde ",
        "donde ",
        "por qué ",
        "por que ",
        "quién ",
        "quien ",
        "cuál ",
        "cual ",
        "puedes ",
        "podrías ",
        "podrias ",
        "sabes ",
        "recuerdas ",
    )

    FRASES_CONVERSACIONALES = (
        "hola",
        "buenas",
        "gracias",
        "muchas gracias",
        "adiós",
        "adios",
        "chao",
        "cómo estás",
        "como estas",
        "qué tal",
        "que tal",
    )

    INDICADORES_CONOCIMIENTO = (
        "voy a",
        "quiero usar",
        "utilizaré",
        "utilizare",
        "estoy utilizando",
        "estoy usando",
        "decidí",
        "decidi",
        "tendrá",
        "tendra",
        "tendrán",
        "tendran",
        "será",
        "sera",
        "funciona con",
        "está hecho",
        "esta hecho",
        "usaré",
        "usare",
    )

    def evaluar(
        self,
        texto: str,
        fuente: str = "usuario",
    ) -> ResultadoFiltroMemoria:

        texto = texto.strip()

        if not texto:
            return ResultadoFiltroMemoria(
                guardar=False,
                motivo="texto_vacio",
                tipo="descartable",
                score=0.0,
            )

        normalizado = re.sub(
            r"\s+",
            " ",
            texto.lower(),
        ).strip()

        # =====================================================
        # INFORMACIÓN INVESTIGADA
        # =====================================================

        if fuente == "internet":

            return ResultadoFiltroMemoria(
                guardar=True,
                motivo="conocimiento_investigado",
                tipo="conocimiento",
                score=0.90,
            )

        # =====================================================
        # CONVERSACIÓN SIMPLE
        # =====================================================

        if normalizado in self.FRASES_CONVERSACIONALES:

            return ResultadoFiltroMemoria(
                guardar=False,
                motivo="mensaje_conversacional",
                tipo="conversacion",
                score=0.05,
            )

        # =====================================================
        # PREGUNTA
        # =====================================================

        es_pregunta = (
            texto.startswith("¿")
            or texto.endswith("?")
            or normalizado.startswith(
                self.INICIOS_PREGUNTA
            )
        )

        if es_pregunta:

            # Una orden explícita para recordar puede
            # contener una pregunta, pero merece conservarse.
            if any(
                expresion in normalizado
                for expresion in (
                    "recuerda que",
                    "acuérdate que",
                    "acuerdate que",
                    "guarda que",
                )
            ):

                return ResultadoFiltroMemoria(
                    guardar=True,
                    motivo="peticion_explicita_de_memoria",
                    tipo="instruccion_memoria",
                    score=0.90,
                )

            return ResultadoFiltroMemoria(
                guardar=False,
                motivo="pregunta_no_es_conocimiento",
                tipo="pregunta",
                score=0.10,
            )

        # =====================================================
        # DECISIÓN / CONOCIMIENTO DEL PROYECTO
        # =====================================================

        if any(
            indicador in normalizado
            for indicador in self.INDICADORES_CONOCIMIENTO
        ):

            return ResultadoFiltroMemoria(
                guardar=True,
                motivo="decision_o_conocimiento",
                tipo="conocimiento",
                score=0.80,
            )

        # =====================================================
        # TEXTO DEMASIADO CORTO
        # =====================================================

        palabras = normalizado.split()

        if len(palabras) <= 2:

            return ResultadoFiltroMemoria(
                guardar=False,
                motivo="contenido_insuficiente",
                tipo="descartable",
                score=0.15,
            )

        # =====================================================
        # CASO GENERAL
        # =====================================================

        return ResultadoFiltroMemoria(
            guardar=True,
            motivo="contenido_potencialmente_util",
            tipo="general",
            score=0.50,
        )