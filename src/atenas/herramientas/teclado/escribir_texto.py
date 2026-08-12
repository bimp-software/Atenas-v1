from __future__ import annotations

import time

import pyautogui
import pyperclip


def escribir_texto(
    texto: str,
    espera_antes: float = 0.5,
) -> dict:

    texto = texto.strip()

    if not texto:
        return {
            "ok": False,
            "error": "texto_vacio",
            "mensaje": "No hay texto para escribir.",
        }

    try:
        time.sleep(
            max(
                0.0,
                espera_antes,
            )
        )

        pyperclip.copy(
            texto
        )

        pyautogui.hotkey(
            "ctrl",
            "v",
        )

        return {
            "ok": True,
            "mensaje": "Texto escrito correctamente.",
            "caracteres": len(texto),
        }

    except Exception as error:

        return {
            "ok": False,
            "error": type(error).__name__,
            "mensaje": str(error),
        }