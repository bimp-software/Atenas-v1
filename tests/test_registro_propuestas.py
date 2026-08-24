from __future__ import annotations

import tempfile

from dataclasses import dataclass, field
from pathlib import Path

from src.atenas.cerebro.desarrollo.registro_propuestas import (
    EstadoPropuesta,
    RegistroPropuestasMejora,
)


class Tipo:
    value = "funcion_grande"


class Riesgo:
    value = "bajo"


@dataclass
class Hallazgo:
    archivo: str = "src/atenas/ejemplo.py"
    tipo: object = field(
        default_factory=Tipo
    )
    descripcion: str = "Función demasiado grande."
    severidad: float = 0.85
    confianza: float = 0.95


@dataclass
class Cambio:
    archivo: str = "src/atenas/ejemplo.py"
    razon: str = "Separar responsabilidades."
    diff: str = "--- a\n+++ b\n-old\n+new\n"
    contenido_nuevo: str = (
        "def ejemplo():\n"
        "    return 1\n"
    )


@dataclass
class Verificacion:
    riesgo: object = field(
        default_factory=Riesgo
    )
    requiere_confirmacion: bool = False


@dataclass
class Propuesta:
    ok: bool = True

    hallazgo: object = field(
        default_factory=Hallazgo
    )

    cambio: object = field(
        default_factory=Cambio
    )

    verificacion: object = field(
        default_factory=Verificacion
    )

    mensaje: str = "Propuesta validada."


def main():

    print()
    print("=" * 80)
    print(" REGISTRO PERSISTENTE DE PROPUESTAS - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        db = (
            Path(temporal)
            / "propuestas.db"
        )

        registro = (
            RegistroPropuestasMejora(
                db_path=db
            )
        )

        # =====================================================
        # GUARDAR PROPUESTA
        # =====================================================

        guardada = (
            registro.guardar(
                Propuesta(),
                metadata={
                    "origen":
                        "automejora"
                },
            )
        )

        print()
        print(
            "ID:",
            guardada.id
        )

        print(
            "Estado:",
            guardada.estado
        )

        assert (
            guardada.estado
            == EstadoPropuesta.VALIDADA
        )

        # =====================================================
        # REINICIO SIMULADO
        # =====================================================

        registro_2 = (
            RegistroPropuestasMejora(
                db_path=db
            )
        )

        recuperada = (
            registro_2.obtener(
                guardada.id
            )
        )

        assert recuperada is not None

        print()
        print(
            "Recuperada tras reinicio:",
            recuperada.archivo
        )

        assert (
            recuperada.archivo
            == "src/atenas/ejemplo.py"
        )

        assert (
            recuperada.estado
            == EstadoPropuesta.VALIDADA
        )

        assert (
            recuperada.metadata
            is not None
        )

        assert (
            recuperada.metadata.get(
                "origen"
            )
            == "automejora"
        )

        # =====================================================
        # PENDIENTES
        # =====================================================

        pendientes = (
            registro_2.pendientes()
        )

        print()
        print(
            "Pendientes:",
            len(pendientes)
        )

        assert (
            len(pendientes)
            == 1
        )

        print()
        print("=" * 80)
        print(" CONTEXTO PARA QWEN")
        print("=" * 80)

        print()
        print(
            registro_2
            .contexto_para_llm()
        )

        # =====================================================
        # MARCAR COMO APLICADA
        # =====================================================

        aplicada = (
            registro_2
            .marcar_aplicada(
                guardada.id,
                cambio_id="cambio-123",
            )
        )

        print()
        print(
            "Estado final:",
            aplicada.estado
        )

        print(
            "Cambio ID:",
            aplicada.cambio_id
        )

        assert (
            aplicada.estado
            == EstadoPropuesta.APLICADA
        )

        assert (
            aplicada.cambio_id
            == "cambio-123"
        )

        # =====================================================
        # YA NO DEBE APARECER COMO PENDIENTE
        # =====================================================

        pendientes_finales = (
            registro_2.pendientes()
        )

        print(
            "Pendientes finales:",
            len(
                pendientes_finales
            )
        )

        assert (
            len(
                pendientes_finales
            )
            == 0
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()