import pyautogui


def escribir_texto(texto: str,intervalo: float = 0.02,) -> bool:
    if not texto: return False
    pyautogui.write(texto,interval=max(0.0,intervalo,),)
    return True