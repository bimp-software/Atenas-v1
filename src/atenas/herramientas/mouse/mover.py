import pyautogui

def mover_mouse(x: int, y: int, duracion: float = 0.3) -> bool:
    ancho, alto = pyautogui.size()

    if not (0 <= x < ancho):
        raise ValueError(f"Coordenada X fuera de pantalla: {x}")

    if not (0 <= y < alto):
        raise ValueError(f"Coordenada Y fuera de pantalla: {y}")

    pyautogui.moveTo(x, y,duration=max(0.0, duracion))

    return True