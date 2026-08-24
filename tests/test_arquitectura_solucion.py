from __future__ import annotations

import json

from src.atenas.cerebro.desarrollo.analista_requisitos import (
    AnalistaRequisitos,
    TipoSolucion,
)

from src.atenas.cerebro.desarrollo.arquitecto_software import (
    ArquitectoSoftware,
)

from src.atenas.cerebro.desarrollo.disenador_base_datos import (
    DisenadorBaseDatos,
)


class LLMFalso:

    def __init__(self):
        self.llamadas = 0

    def chat(self, mensajes):

        self.llamadas += 1

        if self.llamadas == 1:

            return json.dumps({
                "nombre_proyecto": "Sistema Comercial",
                "tipo_solucion": "web",
                "resumen": "Plataforma web para ventas e inventario.",
                "actores": ["Administrador", "Vendedor"],
                "requisitos_funcionales": [
                    {
                        "id": "RF-001",
                        "descripcion": "Gestionar productos.",
                        "prioridad": "alta",
                        "obligatorio": True
                    },
                    {
                        "id": "RF-002",
                        "descripcion": "Registrar ventas.",
                        "prioridad": "alta",
                        "obligatorio": True
                    }
                ],
                "requisitos_no_funcionales": [
                    {
                        "id": "RNF-001",
                        "descripcion": "Control de acceso por roles.",
                        "prioridad": "alta",
                        "obligatorio": True
                    }
                ],
                "entidades_negocio": [
                    "Usuario",
                    "Producto",
                    "Venta",
                    "DetalleVenta"
                ],
                "integraciones": [],
                "restricciones": [],
                "necesita_base_datos": True,
                "necesita_autenticacion": True,
                "necesita_roles": True,
                "necesita_api": True,
                "necesita_archivos": False,
                "necesita_tiempo_real": False,
                "necesita_offline": False,
                "complejidad": "alta",
                "riesgos_iniciales": [
                    "Consistencia de stock."
                ],
                "preguntas_abiertas": []
            })

        if self.llamadas == 2:

            return json.dumps({
                "estilo": "monolito_modular",
                "tipo_solucion": "web",
                "frontend": {
                    "tecnologia": "React",
                    "lenguaje": "TypeScript"
                },
                "backend": {
                    "tecnologia": "FastAPI",
                    "lenguaje": "Python"
                },
                "desktop": None,
                "movil": None,
                "embebido": None,
                "api": {
                    "estilo": "REST"
                },
                "base_datos": {
                    "motor": "PostgreSQL"
                },
                "cache": None,
                "colas": None,
                "autenticacion": {
                    "metodo": "JWT"
                },
                "componentes": [
                    {
                        "nombre": "ventas",
                        "responsabilidad": "Gestionar ventas",
                        "tecnologia": "FastAPI",
                        "lenguaje": "Python",
                        "depende_de": ["inventario"]
                    }
                ],
                "despliegue": {
                    "tipo": "docker"
                },
                "pruebas": {
                    "backend": "pytest",
                    "frontend": "vitest"
                },
                "seguridad": [
                    "RBAC",
                    "validación de entrada"
                ],
                "decisiones": [
                    "Monolito modular para reducir complejidad."
                ]
            })

        return json.dumps({
            "motor": "postgresql",
            "nombre": "sistema_comercial",
            "tablas": [
                {
                    "nombre": "usuarios",
                    "descripcion": "Usuarios del sistema.",
                    "campos": [
                        {
                            "nombre": "id",
                            "tipo": "uuid",
                            "nullable": False,
                            "unique": True,
                            "default": None,
                            "descripcion": "PK"
                        },
                        {
                            "nombre": "email",
                            "tipo": "varchar(255)",
                            "nullable": False,
                            "unique": True,
                            "default": None,
                            "descripcion": "Correo"
                        }
                    ],
                    "clave_primaria": ["id"],
                    "indices": [["email"]]
                },
                {
                    "nombre": "productos",
                    "descripcion": "Catálogo.",
                    "campos": [
                        {
                            "nombre": "id",
                            "tipo": "uuid",
                            "nullable": False,
                            "unique": True,
                            "default": None,
                            "descripcion": "PK"
                        },
                        {
                            "nombre": "stock",
                            "tipo": "integer",
                            "nullable": False,
                            "unique": False,
                            "default": "0",
                            "descripcion": "Stock actual"
                        }
                    ],
                    "clave_primaria": ["id"],
                    "indices": []
                }
            ],
            "relaciones": [],
            "decisiones": [
                "Modelo relacional por consistencia transaccional."
            ],
            "estrategia_migraciones": "Migraciones versionadas.",
            "estrategia_backup": "Backup diario.",
            "estrategia_integridad": [
                "Claves foráneas",
                "restricciones NOT NULL"
            ]
        })


def main():

    print()
    print("=" * 80)
    print(" ANÁLISIS + ARQUITECTURA + BASE DE DATOS - ATENAS")
    print("=" * 80)

    llm = LLMFalso()

    analista = AnalistaRequisitos(
        llm
    )

    analisis = analista.analizar(
        "Necesito un sistema web de ventas e inventario."
    )

    print()
    print(
        "Tipo de solución:",
        analisis.tipo_solucion
    )

    assert (
        analisis.tipo_solucion
        == TipoSolucion.WEB
    )

    arquitecto = ArquitectoSoftware(
        llm
    )

    arquitectura = arquitecto.diseñar(
        analisis
    )

    print(
        "Arquitectura:",
        arquitectura.estilo
    )

    print(
        "Backend:",
        arquitectura.backend
    )

    print(
        "Base de datos:",
        arquitectura.base_datos
    )

    diseñador = DisenadorBaseDatos(
        llm
    )

    modelo = diseñador.diseñar(
        analisis,
        arquitectura,
    )

    assert modelo is not None

    print()
    print(
        "Motor BD:",
        modelo.motor
    )

    print(
        "Tablas:",
        [
            tabla.nombre
            for tabla
            in modelo.tablas
        ]
    )

    assert (
        modelo.motor
        == "postgresql"
    )

    assert (
        len(
            modelo.tablas
        )
        == 2
    )

    print()
    print("=" * 80)
    print(" TEST CORRECTO")
    print("=" * 80)


if __name__ == "__main__":
    main()