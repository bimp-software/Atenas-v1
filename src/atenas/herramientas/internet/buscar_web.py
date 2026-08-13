from __future__ import annotations

from ddgs import DDGS


def buscar_web(
    consulta: str,
    limite: int = 5,
) -> dict:

    consulta = consulta.strip()

    if not consulta:
        return {
            "ok": False,
            "error": "consulta_vacia",
            "resultados": [],
        }

    limite = max(
        1,
        min(limite, 10),
    )

    try:

        resultados_raw = DDGS().text(
            consulta,
            max_results=limite,
        )

        resultados = []

        for item in resultados_raw:

            resultados.append({
                "titulo": (
                    item.get("title")
                    or ""
                ),
                "url": (
                    item.get("href")
                    or item.get("url")
                    or ""
                ),
                "fragmento": (
                    item.get("body")
                    or ""
                ),
            })

        return {
            "ok": True,
            "consulta": consulta,
            "cantidad": len(resultados),
            "resultados": resultados,
        }

    except Exception as error:

        return {
            "ok": False,
            "consulta": consulta,
            "error": type(error).__name__,
            "mensaje": str(error),
            "resultados": [],
        }