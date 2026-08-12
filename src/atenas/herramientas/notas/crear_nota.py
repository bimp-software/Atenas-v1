from __future__ import annotations

from datetime import datetime
from pathlib import Path


def crear_nota(
    contenido: str,
    carpeta: str = "data/notas",
) -> dict:

    contenido = contenido.strip()

    if not contenido:
        raise ValueError(
            "No se puede crear una nota vacía."
        )

    ruta_carpeta = Path(
        carpeta
    )

    ruta_carpeta.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    ruta = (
        ruta_carpeta
        / f"nota_{timestamp}.txt"
    )

    ruta.write_text(
        contenido,
        encoding="utf-8",
    )

    return {
        "ok": True,
        "archivo": str(ruta),
        "mensaje": (
            "Nota creada correctamente."
        ),
    }