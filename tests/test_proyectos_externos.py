from __future__ import annotations

import json
import tempfile

from pathlib import Path

from src.atenas.cerebro.proyectos_externos.espacios_trabajo import (
    GestorEspaciosTrabajo,
    PerfilEspaciosTrabajo,
)

from src.atenas.cerebro.proyectos_externos.creador_proyecto_externo import (
    CreadorProyectosExternos,
)


class LLMFalso:

    def chat(
        self,
        mensajes,
    ):

        return json.dumps(
            {
                "tipo": "cliente",
                "nombre": "Portal Inventario",
                "cliente": "Cliente Demo",
                "lenguaje_sugerido": "python",
                "necesita_pdf": True,
                "confianza": 0.98,
                "motivo": (
                    "La solicitud corresponde "
                    "a un proyecto para un cliente."
                ),
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" PROYECTOS EXTERNOS AUTÓNOMOS - ATENAS")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as temporal:

        raiz = Path(
            temporal
        )

        config = (
            raiz
            / "espacios.json"
        )

        espacios = (
            GestorEspaciosTrabajo(
                config_path=config
            )
        )

        # En el test redirigimos todos los destinos a TEMP.
        espacios.guardar_perfil(
            PerfilEspaciosTrabajo(
                proyectos_personales=str(
                    raiz
                    / "Personales"
                ),
                proyectos_clientes=str(
                    raiz
                    / "Escritorio"
                    / "Clientes"
                ),
                experimentos=str(
                    raiz
                    / "Experimentos"
                ),
                documentacion=str(
                    raiz
                    / "Documentacion"
                ),
            )
        )

        creador = (
            CreadorProyectosExternos(
                llm=LLMFalso(),
                espacios=espacios,
            )
        )

        resultado = (
            creador.crear(
                descripcion=(
                    "Crear un portal de inventario "
                    "para Cliente Demo, con usuarios, "
                    "productos y reportes."
                ),
                objetivos=[
                    "Gestionar usuarios.",
                    "Gestionar productos.",
                    "Generar reportes.",
                ],
                requisitos=[
                    "Persistencia de datos.",
                    "Validación de acceso.",
                ],
                arquitectura=[
                    "Backend separado de interfaz.",
                    "Módulos por responsabilidad.",
                ],
                entregables=[
                    "Código fuente.",
                    "Documentación.",
                    "PDF de especificaciones.",
                ],
                pruebas=[
                    "Pruebas unitarias.",
                    "Pruebas de integración.",
                ],
            )
        )

        assert resultado.ok
        assert resultado.carpeta

        carpeta = Path(
            resultado.carpeta
        )

        print()
        print(
            "Carpeta elegida por ATENAS:",
            carpeta
        )

        print(
            "PDF generado:",
            resultado.pdf_generado
        )

        assert (
            "Cliente Demo"
            in str(
                carpeta
            )
        )

        assert (
            carpeta
            / "src"
        ).exists()

        assert (
            carpeta
            / "tests"
        ).exists()

        assert (
            carpeta
            / "docs"
        ).exists()

        assert (
            carpeta
            / "README.md"
        ).exists()

        assert (
            carpeta
            / "ESPECIFICACIONES.md"
        ).exists()

        assert (
            carpeta
            / "proyecto.json"
        ).exists()

        print()
        print("-" * 80)
        print(" ARCHIVOS")
        print("-" * 80)

        for archivo in resultado.archivos_creados:

            print(
                archivo
            )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()