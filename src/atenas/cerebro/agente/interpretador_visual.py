from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .percepcion_visual import EstadoVisual


@dataclass
class ElementoVisual:
    tipo: str
    descripcion: str
    confianza: float = 0.0
    x_relativo: float | None = None
    y_relativo: float | None = None
    ancho_relativo: float | None = None
    alto_relativo: float | None = None
    texto: str | None = None
    accion_sugerida: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InterpretacionVisual:
    resumen: str
    contexto_aplicacion: str | None = None
    elementos: list[ElementoVisual] = field(default_factory=list)
    observaciones: list[str] = field(default_factory=list)
    riesgos: list[str] = field(default_factory=list)
    confianza_global: float = 0.0


@dataclass
class ResultadoInterpretacionVisual:
    ok: bool
    interpretacion: InterpretacionVisual | None = None
    mensaje: str = ""
    error: str | None = None


class InterpretadorVisual:
    """
    Capa semántica sobre EstadoVisual + captura.

    Si no existe un modelo multimodal, entrega una interpretación
    estructurada basada en ventanas, mouse y contexto de aplicación.
    Si se entrega un adaptador de visión, puede enriquecer la escena.
    """

    def __init__(self, vision: Any | None = None):
        self.vision = vision

    @staticmethod
    def _clamp(valor: Any) -> float:
        try:
            valor = float(valor)
        except Exception:
            valor = 0.0
        return max(0.0, min(1.0, valor))

    @staticmethod
    def _base(estado: EstadoVisual) -> InterpretacionVisual:
        observaciones: list[str] = []
        riesgos: list[str] = []
        elementos: list[ElementoVisual] = []

        titulo = None
        if estado.ventana_activa:
            titulo = str(estado.ventana_activa.get("titulo") or "")
            observaciones.append(f"La ventana activa es '{titulo}'.")
            elementos.append(
                ElementoVisual(
                    tipo="ventana",
                    descripcion=f"Ventana activa: {titulo}",
                    confianza=1.0,
                    metadata={
                        "hwnd": estado.ventana_activa.get("hwnd"),
                        "pid": estado.ventana_activa.get("pid"),
                    },
                )
            )

        if estado.mouse:
            observaciones.append(
                f"El cursor está en x={estado.mouse['x']}, y={estado.mouse['y']}."
            )

        contexto = estado.contexto_aplicacion
        if contexto == "editor_codigo":
            observaciones.append("El contexto parece ser un editor de código.")
        elif contexto == "terminal":
            observaciones.append("El contexto parece ser una terminal.")
            riesgos.append(
                "Las acciones de teclado en una terminal pueden ejecutar comandos reales."
            )
        elif contexto == "navegador":
            observaciones.append("El contexto parece ser un navegador.")
            riesgos.append(
                "Las acciones GUI en navegador pueden producir efectos externos."
            )
        elif contexto == "explorador_archivos":
            observaciones.append("El contexto parece ser el explorador de archivos.")
        elif contexto == "editor_texto":
            observaciones.append("El contexto parece ser un editor de texto.")

        return InterpretacionVisual(
            resumen=(
                "Escena visual estructurada disponible."
                + (f" Contexto: {contexto}." if contexto else "")
            ),
            contexto_aplicacion=contexto,
            elementos=elementos,
            observaciones=observaciones,
            riesgos=riesgos,
            confianza_global=0.55,
        )

    @staticmethod
    def _prompt(estado: EstadoVisual) -> str:
        return f"""
Analiza esta captura como sistema de percepción para ATENAS.

CONTEXTO:
- aplicación: {estado.contexto_aplicacion}
- ventana activa: {estado.ventana_activa}
- mouse: {estado.mouse}
- resolución: {estado.pantalla_ancho} x {estado.pantalla_alto}

Responde SOLO JSON válido:
{{
  "resumen": "...",
  "contexto_aplicacion": "...",
  "observaciones": ["..."],
  "riesgos": ["..."],
  "confianza_global": 0.0,
  "elementos": [
    {{
      "tipo": "boton|campo_texto|editor|panel|menu|terminal|texto|otro",
      "descripcion": "...",
      "confianza": 0.0,
      "x_relativo": 0.0,
      "y_relativo": 0.0,
      "ancho_relativo": 0.0,
      "alto_relativo": 0.0,
      "texto": null,
      "accion_sugerida": null,
      "metadata": {{}}
    }}
  ]
}}

Reglas:
- coordenadas entre 0 y 1;
- no inventes elementos;
- baja confianza si no estás seguro;
- no ejecutes acciones.
""".strip()

    def _llamar_vision(self, ruta: str, prompt: str) -> str:
        if self.vision is None:
            raise RuntimeError("modelo_vision_no_configurado")

        for nombre in ("analizar_imagen", "vision", "chat_vision"):
            metodo = getattr(self.vision, nombre, None)
            if callable(metodo):
                return metodo(ruta, prompt)

        raise RuntimeError("adaptador_vision_incompatible")

    @classmethod
    def _parsear(
        cls,
        texto: str,
        base: InterpretacionVisual,
    ) -> InterpretacionVisual:
        texto = (texto or "").strip()
        if texto.startswith("```"):
            texto = texto.strip("`")
            if texto.lower().startswith("json"):
                texto = texto[4:].strip()

        datos = json.loads(texto)
        elementos: list[ElementoVisual] = []

        for item in datos.get("elementos", []) or []:
            if not isinstance(item, dict):
                continue
            elementos.append(
                ElementoVisual(
                    tipo=str(item.get("tipo", "otro")),
                    descripcion=str(item.get("descripcion", "")),
                    confianza=cls._clamp(item.get("confianza", 0.0)),
                    x_relativo=(
                        cls._clamp(item["x_relativo"])
                        if item.get("x_relativo") is not None
                        else None
                    ),
                    y_relativo=(
                        cls._clamp(item["y_relativo"])
                        if item.get("y_relativo") is not None
                        else None
                    ),
                    ancho_relativo=(
                        cls._clamp(item["ancho_relativo"])
                        if item.get("ancho_relativo") is not None
                        else None
                    ),
                    alto_relativo=(
                        cls._clamp(item["alto_relativo"])
                        if item.get("alto_relativo") is not None
                        else None
                    ),
                    texto=(
                        str(item["texto"])
                        if item.get("texto") is not None
                        else None
                    ),
                    accion_sugerida=(
                        str(item["accion_sugerida"])
                        if item.get("accion_sugerida") is not None
                        else None
                    ),
                    metadata=item.get("metadata", {}) or {},
                )
            )

        return InterpretacionVisual(
            resumen=str(datos.get("resumen", base.resumen)),
            contexto_aplicacion=(
                datos.get("contexto_aplicacion") or base.contexto_aplicacion
            ),
            elementos=base.elementos + elementos,
            observaciones=(
                base.observaciones
                + [str(x) for x in (datos.get("observaciones", []) or [])]
            ),
            riesgos=(
                base.riesgos
                + [str(x) for x in (datos.get("riesgos", []) or [])]
            ),
            confianza_global=cls._clamp(
                datos.get("confianza_global", base.confianza_global)
            ),
        )

    def interpretar(
        self,
        estado: EstadoVisual,
        usar_modelo_vision: bool = True,
    ) -> ResultadoInterpretacionVisual:
        base = self._base(estado)

        if (
            not usar_modelo_vision
            or self.vision is None
            or not estado.captura_ruta
        ):
            return ResultadoInterpretacionVisual(
                ok=True,
                interpretacion=base,
                mensaje="Interpretación estructurada generada.",
            )

        ruta = Path(estado.captura_ruta)
        if not ruta.exists():
            return ResultadoInterpretacionVisual(
                ok=False,
                interpretacion=base,
                mensaje="La escena estructurada existe, pero falta la captura.",
                error="captura_no_existe",
            )

        try:
            respuesta = self._llamar_vision(str(ruta), self._prompt(estado))
            enriquecida = self._parsear(respuesta, base)
            return ResultadoInterpretacionVisual(
                ok=True,
                interpretacion=enriquecida,
                mensaje="Interpretación visual semántica generada.",
            )
        except Exception as error:
            return ResultadoInterpretacionVisual(
                ok=True,
                interpretacion=base,
                mensaje=(
                    "Se utilizó percepción estructurada porque el modelo "
                    "visual no pudo responder."
                ),
                error=f"{type(error).__name__}: {error}",
            )