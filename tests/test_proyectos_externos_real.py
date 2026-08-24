from __future__ import annotations

import json

from pathlib import Path

from src.atenas.cerebro.proyectos_externos.espacios_trabajo import (
    GestorEspaciosTrabajo,
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
                "nombre": (
                    "Portal Inventario ATENAS"
                ),
                "cliente": (
                    "Cliente Demo"
                ),
                "lenguaje_sugerido":
                    "python",
                "necesita_pdf":
                    True,
                "confianza":
                    0.99,
                "motivo": (
                    "Es un proyecto para "
                    "un cliente."
                ),
            },
            ensure_ascii=False,
        )


def main():

    print()
    print("=" * 80)
    print(" PROYECTO EXTERNO REAL - ATENAS")
    print("=" * 80)

    raiz_atenas = (
        Path.cwd()
        .resolve()
    )

    if not (
        raiz_atenas
        / "src"
        / "atenas"
    ).exists():

        raise RuntimeError(
            "Ejecuta este test desde "
            "la raíz de Atenas-v1."
        )

    config = (
        raiz_atenas
        / "data"
        / "espacios_trabajo.json"
    )

    espacios = (
        GestorEspaciosTrabajo(
            config_path=config
        )
    )

    print()
    print("-" * 80)
    print(" RUTAS DETECTADAS")
    print("-" * 80)

    diagnostico = (
        espacios.diagnostico()
    )

    print(
        "Escritorio:",
        diagnostico[
            "escritorio_detectado"
        ]
    )

    print(
        "Documentos:",
        diagnostico[
            "documentos_detectados"
        ]
    )

    print(
        "Clientes:",
        espacios.perfil
        .proyectos_clientes
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
                "para Cliente Demo con usuarios, "
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
            riesgos=[
                "Validar permisos.",
                "Proteger datos del cliente.",
            ],
        )
    )

    print()
    print("-" * 80)
    print(" RESULTADO")
    print("-" * 80)

    print(
        "OK:",
        resultado.ok
    )

    print(
        "Carpeta:",
        resultado.carpeta
    )

    print(
        "PDF:",
        resultado.pdf_generado
    )

    if not resultado.ok:

        raise AssertionError(
            resultado.error
        )

    carpeta = Path(
        resultado.carpeta
    )

    assert carpeta.exists()

    esperados = [
        carpeta / "src",
        carpeta / "tests",
        carpeta / "docs",
        carpeta / "assets",
        carpeta / ".gitignore",
        carpeta / "README.md",
        carpeta / "ESPECIFICACIONES.md",
        carpeta / "proyecto.json",
    ]

    if resultado.pdf_generado:

        esperados.append(
            carpeta
            / "ESPECIFICACIONES.pdf"
        )

    print()
    print("-" * 80)
    print(" VERIFICACIÓN REAL")
    print("-" * 80)

    for ruta in esperados:

        existe = ruta.exists()

        print(
            (
                "SÍ"
                if existe
                else "NO"
            ),
            "->",
            ruta,
        )

        assert existe

    print()
    print("-" * 80)
    print(" ABRIR EN WINDOWS")
    print("-" * 80)

    print()
    print(
        f'explorer "{carpeta}"'
    )

    print()
    print("=" * 80)
    print(" TEST REAL CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()