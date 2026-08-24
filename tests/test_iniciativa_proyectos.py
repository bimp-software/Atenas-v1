from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.atenas.cerebro.desarrollo import (
    SistemaDesarrolloAtenas,
    TipoIniciativaDesarrollo,
)


class LLMFalso:
    def chat(self, mensajes):
        ultimo = mensajes[-1]["content"]

        if "Divide este proyecto" in ultimo:
            return json.dumps(
                {
                    "objetivos": [
                        {
                            "descripcion":
                                "Analizar la arquitectura actual.",
                            "prioridad": 0.95,
                            "depende_de_indices": [],
                        },
                        {
                            "descripcion":
                                "Diseñar una interfaz técnica.",
                            "prioridad": 0.90,
                            "depende_de_indices": [0],
                        },
                    ]
                },
                ensure_ascii=False,
            )

        return json.dumps(
            {
                "completado": True,
                "resumen": (
                    "Analicé la arquitectura disponible "
                    "y definí los componentes relevantes."
                ),
                "entregable": (
                    "La futura capacidad debe separar captura, "
                    "percepción, estado del mundo y planificación."
                ),
                "siguiente_recomendacion": (
                    "Diseñar la interfaz entre percepción "
                    "y estado del mundo."
                ),
            },
            ensure_ascii=False,
        )


def main():
    print()
    print("=" * 80)
    print(" INICIATIVA PROPIA SOBRE PROYECTOS - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:
        raiz = Path(temporal)
        proyecto_raiz = raiz / "proyecto"
        (proyecto_raiz / "src" / "atenas").mkdir(parents=True)
        (proyecto_raiz / "src" / "__init__.py").write_text("", encoding="utf-8")
        (proyecto_raiz / "src" / "atenas" / "__init__.py").write_text("", encoding="utf-8")

        sistema = SistemaDesarrolloAtenas(
            llm=LLMFalso(),
            raiz_proyecto=proyecto_raiz,
            db_historial=raiz / "historial.db",
        )

        creado = sistema.crear_proyecto_interno(
            nombre="Preparar percepción visual",
            descripcion=(
                "Diseñar progresivamente la arquitectura previa "
                "a incorporar visión al cuerpo de ATENAS."
            ),
            prioridad=0.96,
            autonomia=True,
        )

        assert creado.ok
        assert creado.proyecto is not None

        print()
        print("Proyecto creado:", creado.proyecto.nombre)

        informe_vacio = type("Informe", (), {"hallazgos": []})()
        sistema.analizar_mejoras = lambda: informe_vacio

        decision = sistema.decidir_siguiente_trabajo_desarrollo()

        print()
        print("ATENAS decidió:", decision.tipo)
        print("Objetivo:", decision.datos.get("objetivo"))

        assert (
            decision.tipo
            == TipoIniciativaDesarrollo.CONTINUAR_PROYECTO
        )

        resultado = sistema.ejecutar_siguiente_trabajo_desarrollo(
            permitir_aplicacion=False
        )

        assert resultado.ok
        assert resultado.ejecutada

        trabajo = resultado.resultado

        print()
        print("Trabajo realizado:", trabajo.resumen)
        print("Completado:", trabajo.completado)
        print("Resultado guardado:", trabajo.archivo_resultado)

        assert trabajo.completado
        assert trabajo.archivo_resultado is not None
        assert Path(trabajo.archivo_resultado).exists()

        siguiente = sistema.siguiente_objetivo_proyecto(
            creado.proyecto.id
        )

        assert siguiente is not None

        print()
        print("Siguiente objetivo elegido:", siguiente.descripcion)

        assert (
            siguiente.descripcion
            == "Diseñar una interfaz técnica."
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()