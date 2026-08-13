from __future__ import annotations
from dataclasses import dataclass

from .filtro_memoria import FiltroMemoria


@dataclass
class Experiencia:
    contenido: str

    tipo: str | None = None
    dominio: str | None = None
    subcategoria: str | None = None

    fuente: str = "usuario"

    importancia: float = 0.5
    confianza: float = 0.7
    novedad: float = 0.5

    contexto: str | None = None


class HipocampoDigital:

    def __init__(
        self,
        clasificador,
        consolidador,
        recuperador,
    ):
        self.filtro = FiltroMemoria()
        self.clasificador = clasificador
        self.consolidador = consolidador
        self.recuperador = recuperador

    # =========================================================
    # PROCESAR EXPERIENCIA
    # =========================================================

    def procesar(
        self,
        experiencia: Experiencia,
    ) -> dict:

        contenido = experiencia.contenido.strip()

        if not contenido:
            return {
                "guardada": False,
                "motivo": "contenido_vacio",
            }

        # =====================================================
        # 1. FILTRAR
        # =====================================================

        evaluacion = self.filtro.evaluar(
            texto=contenido,
            fuente=experiencia.fuente,
        )

        if not evaluacion.guardar:

            return {
                "guardada": False,
                "motivo": evaluacion.motivo,
                "tipo": evaluacion.tipo,
                "score_filtro": evaluacion.score,
            }

        # =====================================================
        # 2. CLASIFICAR
        # =====================================================

        clasificacion = (
            self.clasificador.clasificar(
                contenido
            )
        )

        experiencia.tipo = (
            clasificacion.tipo
        )

        experiencia.dominio = (
            clasificacion.dominio
        )

        # Compatibilidad por si tu clasificador usa
        # "categoria" en vez de "subcategoria".
        experiencia.subcategoria = (
            getattr(
                clasificacion,
                "subcategoria",
                None,
            )
            or getattr(
                clasificacion,
                "categoria",
                None,
            )
        )

        # =====================================================
        # 3. AJUSTAR IMPORTANCIA SEGÚN FILTRO
        # =====================================================

        experiencia.importancia = max(
            experiencia.importancia,
            evaluacion.score,
        )

        # =====================================================
        # 4. CONSOLIDAR
        # =====================================================

        resultado = (
            self.consolidador.consolidar(
                experiencia
            )
        )

        # =====================================================
        # 5. AÑADIR INFORMACIÓN DEL FILTRO
        # =====================================================

        if isinstance(
            resultado,
            dict,
        ):

            resultado[
                "filtro_tipo"
            ] = evaluacion.tipo

            resultado[
                "filtro_score"
            ] = evaluacion.score

            resultado[
                "filtro_motivo"
            ] = evaluacion.motivo

        return resultado

    # =========================================================
    # RECORDAR
    # =========================================================

    def recordar(
        self,
        consulta: str,
    ):

        consulta = consulta.strip()

        if not consulta:
            return []

        return self.recuperador.buscar(
            consulta
        )