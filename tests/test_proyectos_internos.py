from __future__ import annotations

import json
import tempfile

from pathlib import Path

from src.atenas.cerebro.desarrollo.proyectos_internos import (
    EstadoObjetivoProyecto,
    EstadoProyecto,
    GestorProyectosInternos,
)

from src.atenas.cerebro.desarrollo.planificador_proyectos import (
    PlanificadorProyectosInternos,
)


class LLMFalso:

    def chat(
        self,
        mensajes,
    ):

        return json.dumps(
            {
                "objetivos": [
                    {
                        "descripcion":
                            "Analizar la arquitectura actual.",

                        "prioridad":
                            0.9,

                        "depende_de_indices":
                            [],
                    },
                    {
                        "descripcion":
                            "Diseñar la interfaz del nuevo módulo.",

                        "prioridad":
                            0.85,

                        "depende_de_indices":
                            [0],
                    },
                    {
                        "descripcion":
                            "Crear pruebas del módulo.",

                        "prioridad":
                            0.8,

                        "depende_de_indices":
                            [1],
                    },
                ]
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" PROYECTOS INTERNOS DE ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        db = (
            Path(temporal)
            / "proyectos.db"
        )

        gestor = (
            GestorProyectosInternos(
                db
            )
        )

        planificador = (
            PlanificadorProyectosInternos(
                llm=LLMFalso(),
                gestor=gestor,
            )
        )

        resultado = (
            planificador
            .crear_desde_meta(
                nombre=(
                    "Preparar sistema de visión"
                ),
                descripcion=(
                    "Preparar la arquitectura "
                    "de software necesaria para "
                    "incorporar visión más adelante."
                ),
                prioridad=0.92,
                autonomia=True,
            )
        )

        assert resultado.ok
        assert (
            resultado.proyecto
            is not None
        )

        proyecto = (
            resultado.proyecto
        )

        print()
        print(
            "Proyecto:",
            proyecto.nombre
        )

        print(
            "Estado:",
            proyecto.estado
        )

        print(
            "Objetivos:",
            len(
                proyecto.objetivos
            )
        )

        assert (
            proyecto.estado
            == EstadoProyecto.ACTIVO
        )

        assert (
            len(
                proyecto.objetivos
            )
            == 3
        )

        primero = (
            gestor.siguiente_objetivo(
                proyecto.id
            )
        )

        assert primero is not None

        print()
        print(
            "Siguiente objetivo:",
            primero.descripcion
        )

        assert (
            primero.descripcion
            == "Analizar la arquitectura actual."
        )

        gestor.iniciar_objetivo(
            primero.id
        )

        gestor.completar_objetivo(
            primero.id
        )

        segundo = (
            gestor.siguiente_objetivo(
                proyecto.id
            )
        )

        assert segundo is not None

        print(
            "Después:",
            segundo.descripcion
        )

        assert (
            segundo.descripcion
            == "Diseñar la interfaz del nuevo módulo."
        )

        # =====================================================
        # REINICIO SIMULADO
        # =====================================================

        gestor_2 = (
            GestorProyectosInternos(
                db
            )
        )

        recuperado = (
            gestor_2.obtener_proyecto(
                proyecto.id
            )
        )

        assert recuperado is not None

        print()
        print(
            "Persistido tras reinicio:",
            recuperado.nombre
        )

        print()
        print(
            gestor_2
            .contexto_para_llm()
        )

        prioritario = (
            gestor_2
            .proyecto_prioritario()
        )

        assert prioritario is not None
        assert (
            prioritario.id
            == proyecto.id
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()