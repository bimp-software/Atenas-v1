from __future__ import annotations

import hashlib
import tempfile

from dataclasses import dataclass, field
from pathlib import Path

from src.atenas.cerebro.desarrollo.registro_propuestas import (
    EstadoPropuesta,
    RegistroPropuestasMejora,
)

from src.atenas.cerebro.desarrollo.reanudar_propuestas import (
    ReanudadorPropuestas,
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
    descripcion: str = "Función grande."
    severidad: float = 0.9
    confianza: float = 0.95


@dataclass
class CambioInicial:
    archivo: str
    contenido_original: str
    contenido_nuevo: str
    razon: str
    diff: str
    hash_original: str


@dataclass
class Verificacion:
    valido: bool = True
    riesgo: object = field(
        default_factory=Riesgo
    )
    requiere_confirmacion: bool = False


@dataclass
class Propuesta:
    ok: bool
    hallazgo: object
    cambio: object
    verificacion: object
    mensaje: str = "validada"


class InspectorFalso:

    def __init__(
        self,
        archivo: Path,
    ):
        self.archivo = archivo

    def leer_archivo(
        self,
        ruta,
    ):
        return {
            "ok": True,
            "contenido": (
                self.archivo.read_text(
                    encoding="utf-8"
                )
            ),
        }


@dataclass
class CambioReconstruido:
    archivo: str
    contenido_original: str
    contenido_nuevo: str
    razon: str
    diff: str
    hash_original: str


class GestorFalso:

    def preparar_cambio(
        self,
        archivo,
        contenido_original,
        contenido_nuevo,
        razon,
    ):
        return CambioReconstruido(
            archivo=archivo,
            contenido_original=(
                contenido_original
            ),
            contenido_nuevo=(
                contenido_nuevo
            ),
            razon=razon,
            diff=(
                "--- a\n+++ b\n-old\n+new\n"
            ),
            hash_original=(
                hashlib.sha256(
                    contenido_original.encode(
                        "utf-8"
                    )
                ).hexdigest()
            ),
        )


@dataclass
class SandboxResultado:
    ok: bool = True
    pruebas: list = field(
        default_factory=lambda: [
            type(
                "Prueba",
                (),
                {
                    "ok": True,
                },
            )()
        ]
    )


class SandboxFalso:

    def crear(
        self,
    ):
        return object()

    def probar_cambio(
        self,
        entorno,
        cambio,
        tests=None,
    ):
        return SandboxResultado()


class VerificadorFalso:

    def verificar(
        self,
        cambio,
        resultado_sandbox,
    ):
        return Verificacion()


class DecisionPolitica:
    aplicar = True
    requiere_confirmacion = False
    motivo = "Seguro."


class PoliticaFalsa:

    def evaluar(
        self,
        propuesta,
    ):
        return DecisionPolitica()


class ResultadoAplicacion:
    ok = True
    aplicada = True
    cambio_id = "cambio-reanudado"
    mensaje = "Aplicado."
    error = None


class AplicadorFalso:

    def aplicar(
        self,
        propuesta,
    ):
        return ResultadoAplicacion()


def main():

    print()
    print("=" * 80)
    print(" REANUDAR PROPUESTA PERSISTIDA - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(temporal)

        archivo = (
            raiz
            / "ejemplo.py"
        )

        original = (
            "def ejemplo():\n"
            "    return 1\n"
        )

        nuevo = (
            "def ejemplo():\n"
            "    valor = 1\n"
            "    return valor\n"
        )

        archivo.write_text(
            original,
            encoding="utf-8",
        )

        hash_original = hashlib.sha256(
            original.encode(
                "utf-8"
            )
        ).hexdigest()

        propuesta = Propuesta(
            ok=True,
            hallazgo=Hallazgo(),
            cambio=CambioInicial(
                archivo=(
                    "src/atenas/ejemplo.py"
                ),
                contenido_original=original,
                contenido_nuevo=nuevo,
                razon="Refactor pequeño.",
                diff=(
                    "--- a\n+++ b\n-old\n+new\n"
                ),
                hash_original=hash_original,
            ),
            verificacion=(
                Verificacion()
            ),
        )

        db = (
            raiz
            / "propuestas.db"
        )

        registro = (
            RegistroPropuestasMejora(
                db
            )
        )

        persistida = (
            registro.guardar(
                propuesta
            )
        )

        print()
        print(
            "Guardada:",
            persistida.id
        )

        # =====================================================
        # REINICIO SIMULADO
        # =====================================================

        registro_2 = (
            RegistroPropuestasMejora(
                db
            )
        )

        reanudador = (
            ReanudadorPropuestas(
                raiz_proyecto=raiz,
                registro=registro_2,
                inspector=(
                    InspectorFalso(
                        archivo
                    )
                ),
                gestor_parches=(
                    GestorFalso()
                ),
                sandbox=(
                    SandboxFalso()
                ),
                verificador=(
                    VerificadorFalso()
                ),
                politica_aplicacion=(
                    PoliticaFalsa()
                ),
                aplicador=(
                    AplicadorFalso()
                ),
            )
        )

        preparado = (
            reanudador.preparar(
                persistida.id,
                tests=[
                    "tests.test_ejemplo"
                ],
            )
        )

        print()
        print(
            "Preparada:",
            preparado.ok
        )

        print(
            "Estado:",
            preparado.estado
        )

        print(
            "Aplicable:",
            preparado.aplicable
        )

        assert preparado.ok
        assert (
            preparado.estado
            == "revalidada"
        )
        assert preparado.aplicable

        aplicada = (
            reanudador.aplicar(
                persistida.id,
                tests=[
                    "tests.test_ejemplo"
                ],
            )
        )

        print()
        print(
            "Aplicación estado:",
            aplicada.estado
        )

        assert aplicada.ok
        assert (
            aplicada.estado
            == "aplicada"
        )

        final = (
            registro_2.obtener(
                persistida.id
            )
        )

        assert final is not None
        assert (
            final.estado
            == EstadoPropuesta.APLICADA
        )

        assert (
            final.cambio_id
            == "cambio-reanudado"
        )

        # =====================================================
        # PROPUESTA OBSOLETA
        # =====================================================

        otra = (
            registro_2.guardar(
                propuesta
            )
        )

        archivo.write_text(
            "def ejemplo():\n    return 999\n",
            encoding="utf-8",
        )

        obsoleta = (
            reanudador.preparar(
                otra.id
            )
        )

        print()
        print(
            "Propuesta modificada:",
            obsoleta.estado
        )

        assert (
            obsoleta.estado
            == "obsoleta"
        )

        registro_obsoleta = (
            registro_2.obtener(
                otra.id
            )
        )

        assert (
            registro_obsoleta
            is not None
        )

        assert (
            registro_obsoleta.estado
            == EstadoPropuesta.OBSOLETA
        )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()
