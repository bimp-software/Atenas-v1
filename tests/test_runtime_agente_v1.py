from __future__ import annotations

import tempfile
from pathlib import Path

from atenas.cerebro.agente.runtime_agente import (
    RuntimeAtenas,
)


def titulo(texto: str) -> None:
    print()
    print("=" * 80)
    print(f" {texto}")
    print("=" * 80)
    print()


def main() -> None:
    titulo("RUNTIME AGENTE V1 - INTEGRACIÓN FINAL")

    with tempfile.TemporaryDirectory() as temporal:
        raiz = Path(temporal) / "agente"

        runtime = RuntimeAtenas.crear(
            raiz_datos=raiz
        )

        # Las instancias deben ser exactamente las mismas.
        assert (
            runtime.agente.contexto_operativo
            is runtime.capacidad_sistema.contexto_operativo
        )

        assert (
            runtime.agente.gestor_sesiones
            is runtime.capacidad_sistema.gestor_sesiones
        )

        assert (
            runtime.agente.gestor_confirmaciones
            is runtime.capacidad_sistema.gestor_confirmaciones
        )

        assert (
            runtime.agente.registro_actividad
            is runtime.capacidad_sistema.registro_actividad
        )

        estado_inicial = runtime.estado()

        print("Estado inicial:", estado_inicial["estado"])
        print(
            "Confirmaciones:",
            estado_inicial["confirmaciones_pendientes"],
        )

        # Crear sesión real usando la capacidad compartida.
        sesion = (
            runtime.capacidad_sistema
            .crear_sesion_trabajo(
                nombre="Sesión Runtime Demo",
                objetivo_superior=(
                    "Mantener una sesión persistente de prueba."
                ),
                proyecto_id="runtime-demo",
                resultado_esperado="Sesión creada correctamente.",
            )
        )

        estado_sesion = runtime.estado()

        print("Sesión:", estado_sesion["sesion_nombre"])
        print("Proyecto:", estado_sesion["proyecto_id"])

        assert estado_sesion["sesion_id"] == sesion.id

        # -----------------------------------------------------
        # REINICIO SIMULADO DEL RUNTIME COMPLETO
        # -----------------------------------------------------

        print()
        print("-" * 80)
        print(" REINICIO RUNTIME")
        print("-" * 80)

        runtime_2 = RuntimeAtenas.crear(
            raiz_datos=raiz
        )

        estado_reinicio = runtime_2.estado()

        print("Estado tras reinicio:", estado_reinicio["estado"])
        print("Sesión restaurada:", estado_reinicio["sesion_nombre"])

        assert estado_reinicio["sesion_id"] == sesion.id
        assert (
            runtime_2.agente.contexto_operativo
            is runtime_2.capacidad_sistema.contexto_operativo
        )

        titulo("RUNTIME AGENTE V1 CORRECTO")


if __name__ == "__main__":
    main()