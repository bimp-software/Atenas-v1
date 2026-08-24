from __future__ import annotations

import shutil
from pathlib import Path

from src.atenas.cerebro.desarrollo.coordinador_dependencias_tarea import (
    CoordinadorDependenciasTarea,
    EstadoDependenciasTarea,
    estado_para_ejecutor,
)


def main():

    print()
    print("=" * 80)
    print(" EJECUTOR + ENTORNO + DEPENDENCIAS - ATENAS")
    print("=" * 80)

    raiz = Path.cwd().resolve()
    proyecto = (
        raiz
        / "data"
        / "pruebas_desarrollo"
        / "coordinador_dependencias"
        / "proyecto"
    )

    if proyecto.exists():
        shutil.rmtree(proyecto)

    (proyecto / "src").mkdir(parents=True, exist_ok=True)

    (proyecto / "src" / "app.py").write_text(
        "def ejecutar():\n"
        "    return True\n",
        encoding="utf-8",
    )

    # Usamos una dependencia deliberadamente inexistente para probar
    # el BLOQUEO sin descargar nada de Internet.
    (proyecto / "requirements.txt").write_text(
        "atenas-paquete-prueba-inexistente-xyz==0.0.1\n",
        encoding="utf-8",
    )

    coordinador = CoordinadorDependenciasTarea()

    resultado = coordinador.preparar(proyecto)

    print()
    print("Estado:", resultado.estado.value)
    print("OK:", resultado.ok)
    print("Pendientes:", len(resultado.pendientes))

    for pendiente in resultado.pendientes:
        print()
        print("Dependencia:", pendiente.dependencia.nombre)
        print("Motivo:", pendiente.motivo)
        if pendiente.evaluacion:
            print(
                "Requiere confirmación:",
                pendiente.evaluacion.requiere_confirmacion,
            )

    assert not resultado.ok
    assert (
        resultado.estado
        == EstadoDependenciasTarea.REQUIERE_CONFIRMACION
    )
    assert len(resultado.pendientes) == 1
    assert (
        estado_para_ejecutor(resultado)
        == "requiere_confirmacion_dependencias"
    )

    print()
    print("La tarea NO se ejecutó.")
    print("La dependencia NO se instaló.")
    print("ATENAS conservó el proyecto para reanudarlo después.")
    print()
    print("Proyecto persistente:", proyecto)
    print(f'explorer "{proyecto}"')

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()