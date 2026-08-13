from __future__ import annotations

import re


class DetectorDesconocimiento:
    """
    Decide si la información local de ATENAS
    parece suficiente para responder una consulta.

    No basta con encontrar recuerdos vagamente relacionados.
    Debe existir evidencia razonablemente cercana a la
    pregunta concreta.
    """

    PALABRAS_VACIAS = {
        "que",
        "qué",
        "como",
        "cómo",
        "para",
        "por",
        "con",
        "sin",
        "una",
        "uno",
        "unos",
        "unas",
        "los",
        "las",
        "del",
        "desde",
        "esto",
        "esta",
        "este",
        "ser",
        "es",
        "son",
        "podria",
        "podría",
        "puede",
        "pueden",
        "util",
        "útil",
    }

    # =========================================================
    # TÉRMINOS IMPORTANTES
    # =========================================================

    def _extraer_terminos(
        self,
        consulta: str,
    ) -> set[str]:

        palabras = re.findall(
            r"[a-záéíóúñüA-ZÁÉÍÓÚÑÜ0-9+#.-]+",
            consulta.lower(),
        )

        return {
            palabra
            for palabra in palabras
            if (
                len(palabra) >= 3
                and palabra
                not in self.PALABRAS_VACIAS
            )
        }

    # =========================================================
    # EVALUAR
    # =========================================================

    def evaluar(
        self,
        consulta: str,
        memorias: list[dict],
        relaciones: list[dict],
    ) -> dict:

        consulta = consulta.strip()

        terminos_consulta = (
            self._extraer_terminos(
                consulta
            )
        )

        incertidumbre = 0.0

        motivos = []

        # =====================================================
        # 1. NO EXISTE MEMORIA
        # =====================================================

        if not memorias:

            incertidumbre += 0.50

            motivos.append(
                "sin_memorias"
            )

        # =====================================================
        # 2. NO EXISTEN RELACIONES
        # =====================================================

        if not relaciones:

            incertidumbre += 0.15

            motivos.append(
                "sin_relaciones_grafo"
            )

        # =====================================================
        # 3. MEJOR SIMILITUD VECTORIAL
        # =====================================================

        mejor_similitud = 0.0

        if memorias:

            mejor_similitud = max(
                float(
                    memoria.get(
                        "similitud_semantica",
                        0.0,
                    )
                    or 0.0
                )
                for memoria in memorias
            )

            if mejor_similitud < 0.35:

                incertidumbre += 0.35

                motivos.append(
                    "similitud_muy_baja"
                )

            elif mejor_similitud < 0.50:

                incertidumbre += 0.20

                motivos.append(
                    "similitud_baja"
                )

        # =====================================================
        # 4. ¿LOS TÉRMINOS IMPORTANTES APARECEN REALMENTE
        #    EN LA MEMORIA?
        # =====================================================

        texto_memorias = " ".join(
            str(
                memoria.get("contenido")
                or memoria.get("descripcion")
                or ""
            ).lower()
            for memoria in memorias
        )

        texto_relaciones = " ".join(
            str(relacion).lower()
            for relacion in relaciones
        )

        conocimiento_local = (
            texto_memorias
            + " "
            + texto_relaciones
        )

        terminos_encontrados = {
            termino
            for termino in terminos_consulta
            if termino in conocimiento_local
        }

        terminos_desconocidos = (
            terminos_consulta
            - terminos_encontrados
        )

        # =====================================================
        # 5. TÉRMINOS IMPORTANTES DESCONOCIDOS
        # =====================================================

        if terminos_consulta:

            cobertura = (
                len(terminos_encontrados)
                / len(terminos_consulta)
            )

        else:

            cobertura = 1.0

        if cobertura < 0.30:

            incertidumbre += 0.35

            motivos.append(
                "muy_baja_cobertura_conceptual"
            )

        elif cobertura < 0.55:

            incertidumbre += 0.20

            motivos.append(
                "baja_cobertura_conceptual"
            )

        incertidumbre = min(
            incertidumbre,
            1.0,
        )

        necesita_investigar = (
            incertidumbre >= 0.50
        )

        return {
            "necesita_investigar":
                necesita_investigar,

            "incertidumbre":
                incertidumbre,

            "mejor_similitud":
                mejor_similitud,

            "terminos_consulta":
                sorted(
                    terminos_consulta
                ),

            "terminos_encontrados":
                sorted(
                    terminos_encontrados
                ),

            "terminos_desconocidos":
                sorted(
                    terminos_desconocidos
                ),

            "cobertura_conceptual":
                cobertura,

            "motivos":
                motivos,
        }