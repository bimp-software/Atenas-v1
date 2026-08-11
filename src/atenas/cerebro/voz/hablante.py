from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

from .motor_voz import MotorVoz


logger = logging.getLogger(__name__)


class Hablante:
    _FIN = object()

    def __init__(self,motor: Optional[MotorVoz] = None,timeout_inicio: float = 5.0,):
        self.motor = motor or MotorVoz()
        self._cola: queue.Queue = queue.Queue()
        self._listo = threading.Event()
        self._cerrado = threading.Event()
        self._disponible = False
        self._hilo = threading.Thread(
            target=self._worker,
            name="ATENAS-TTS",
            daemon=True,
        )

        self._hilo.start()
        self._listo.wait(timeout=timeout_inicio)

    def _worker(self) -> None:
        try:
            self._disponible = self.motor.inicializar()

        except Exception:
            logger.exception("No fue posible inicializar la voz.")
            self._disponible = False

        finally:
            self._listo.set()

        if not self._disponible:
            return

        try:
            while not self._cerrado.is_set():
                elemento = self._cola.get()

                try:
                    if elemento is self._FIN:
                        break

                    texto = str(elemento).strip()

                    if texto:
                        self.motor.hablar(texto)

                except Exception:
                    logger.exception("Error procesando fragmento de voz.")

                finally:
                    self._cola.task_done()

        finally:
            self.motor.cerrar()

    def decir(self, texto: str) -> bool:
        if not self._disponible:
            return False

        texto = texto.strip()

        if not texto:
            return False

        self._cola.put(texto)

        return True

    def esperar(self) -> None:
        if self._disponible:
            self._cola.join()

    def cerrar(self) -> None:
        if self._cerrado.is_set():
            return

        self._cerrado.set()

        if self._hilo.is_alive():
            self._cola.put(self._FIN)
            self._hilo.join(timeout=3)


    @property
    def disponible(self) -> bool:
        return self._disponible

    @property
    def backend(self) -> str:
        return self.motor.nombre_backend