from __future__ import annotations

from .catalogo_herramientas import (
    CATALOGO_HERRAMIENTAS,
)

from .planificador import (
    Plan,
    PasoPlan,
)


class ValidadorPlan:

    MAX_PASOS = 8

    def validar(
        self,
        datos: dict,
    ) -> Plan:

        if not isinstance(
            datos,
            dict,
        ):
            raise ValueError(
                "El plan debe ser un objeto."
            )

        descripcion = str(
            datos.get(
                "descripcion",
                "Plan generado por ATENAS",
            )
        ).strip()

        pasos_raw = datos.get(
            "pasos",
            []
        )

        if not isinstance(
            pasos_raw,
            list,
        ):
            raise ValueError(
                "'pasos' debe ser una lista."
            )

        if len(pasos_raw) > self.MAX_PASOS:
            raise ValueError(
                "El plan contiene demasiados pasos."
            )

        pasos = []

        for numero, paso in enumerate(
            pasos_raw,
            start=1,
        ):

            if not isinstance(
                paso,
                dict,
            ):
                raise ValueError(
                    f"Paso {numero} inválido."
                )

            herramienta = str(
                paso.get(
                    "herramienta",
                    "",
                )
            ).strip()

            if (
                herramienta
                not in CATALOGO_HERRAMIENTAS
            ):
                raise ValueError(
                    "Herramienta no permitida: "
                    f"{herramienta}"
                )

            argumentos = paso.get(
                "argumentos",
                {}
            )

            if not isinstance(
                argumentos,
                dict,
            ):
                raise ValueError(
                    "Los argumentos del paso "
                    f"{numero} no son válidos."
                )

            riesgo = (
                CATALOGO_HERRAMIENTAS[
                    herramienta
                ]["riesgo"]
            )

            requiere_confirmacion = (
                riesgo != "bajo"
            )

            pasos.append(
                PasoPlan(
                    herramienta=herramienta,
                    argumentos=argumentos,
                    requiere_confirmacion=(
                        requiere_confirmacion
                    ),
                )
            )

        return Plan(
            descripcion=descripcion,
            pasos=pasos,
        )