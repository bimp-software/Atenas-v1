from __future__ import annotations

from src.atenas.cerebro.nucleo_conversacional import (
    NucleoConversacional,
)

from src.atenas.cerebro.desarrollo.director_desarrollo import (
    IniciativaDesarrollo,
    ResultadoDirectorDesarrollo,
    TipoIniciativaDesarrollo,
)

from src.atenas.cerebro.desarrollo.ciclo_desarrollo import (
    ResultadoCicloDesarrollo,
)


def main():

    print()
    print("=" * 80)
    print(" NÚCLEO + DESARROLLO AUTÓNOMO - ATENAS")
    print("=" * 80)

    atenas = NucleoConversacional()

    try:

        llamadas = {
            "turnos": 0,
            "ciclos": 0,
        }

        def registrar_turno():
            llamadas["turnos"] += 1

        iniciativa = IniciativaDesarrollo(
            tipo=(
                TipoIniciativaDesarrollo
                .CREAR_TEST
            ),
            descripcion=(
                "Crear un test faltante."
            ),
            prioridad=0.88,
            confianza=0.94,
            origen="automejora",
            puede_ejecutarse_sola=True,
        )

        resultado_director = (
            ResultadoDirectorDesarrollo(
                ok=True,
                iniciativa=iniciativa,
                ejecutada=True,
                mensaje="Test preparado.",
            )
        )

        def procesar(
            tests=None,
            forzar=False,
            permitir_aplicacion=None,
        ):
            llamadas["ciclos"] += 1

            assert (
                permitir_aplicacion
                is False
            )

            return ResultadoCicloDesarrollo(
                ok=True,
                revisado=True,
                ejecutado=True,
                motivo=(
                    "ATENAS decidió preparar "
                    "un test faltante."
                ),
                resultado_director=(
                    resultado_director
                ),
            )

        atenas.desarrollo.registrar_turno_desarrollo = (
            registrar_turno
        )

        atenas.desarrollo.procesar_ciclo_desarrollo = (
            procesar
        )

        resultado = (
            atenas
            ._procesar_ciclo_desarrollo()
        )

        assert resultado is not None
        assert resultado.ok
        assert resultado.revisado
        assert resultado.ejecutado

        assert llamadas["turnos"] == 1
        assert llamadas["ciclos"] == 1

        print()
        print(
            "Turnos registrados:",
            llamadas["turnos"]
        )

        print(
            "Ciclos ejecutados:",
            llamadas["ciclos"]
        )

        print(
            "Iniciativa:",
            resultado_director
            .iniciativa
            .tipo
        )

        print(
            "Aplicación automática: False"
        )

    finally:

        atenas.cerrar()

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()