import pyautogui


BOTONES_PERMITIDOS = {
    "left",
    "right",
    "middle",
}


def hacer_click(boton: str = "left",clicks: int = 1,) -> bool:
    boton = boton.lower()
    if boton not in BOTONES_PERMITIDOS:
        raise ValueError(f"Botón no permitido: {boton}")

    clicks = max(1,min(clicks, 3),)
    pyautogui.click(button=boton,clicks=clicks,interval=0.1,)
    return True