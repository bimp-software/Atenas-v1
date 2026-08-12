from __future__ import annotations

import subprocess


PROGRAMAS_PERMITIDOS = {
    "notepad": ["notepad.exe"],
    "bloc_de_notas": ["notepad.exe"],

    "calculadora": ["calc.exe"],
    "calculator": ["calc.exe"],

    "explorador": ["explorer.exe"],
    "explorer": ["explorer.exe"],

    "cmd": ["cmd.exe"],
}


def abrir_programa(
    programa: str,
) -> dict:

    programa = programa.strip().lower()

    comando = PROGRAMAS_PERMITIDOS.get(
        programa
    )

    if comando is None:

        return {
            "ok": False,
            "error": "programa_no_permitido",
            "mensaje": (
                f"El programa '{programa}' "
                "no está registrado."
            ),
        }

    try:

        proceso = subprocess.Popen(
            comando
        )

        return {
            "ok": True,
            "programa": programa,
            "pid": proceso.pid,
            "mensaje": (
                f"Programa '{programa}' abierto."
            ),
        }

    except Exception as error:

        return {
            "ok": False,
            "error": type(error).__name__,
            "mensaje": str(error),
        }