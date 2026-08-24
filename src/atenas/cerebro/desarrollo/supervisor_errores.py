from __future__ import annotations

import traceback as traceback_lib
import uuid

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from .sistema_desarrollo import (
    SistemaDesarrolloAtenas,
)

from .motor_autorreparacion import (
    MotorAutorreparacion,
    ResultadoMotorAutorreparacion,
)


@dataclass
class EventoError:
    id: str

    tipo: str
    mensaje: str
    traceback: str

    modulo: str | None = None
    funcion: str | None = None
    componente: str | None = None

    creado_en: str = ""

    diagnosticado: bool = False
    diagnostico: Any = None

    reparacion_iniciada: bool = False
    resultado_reparacion: Any = None

    resuelto: bool = False


class SupervisorErrores:
    """
    Supervisor central de errores internos de ATENAS.

    Flujo:

        excepción
            ↓
        EventoError
            ↓
        DiagnosticoCodigo
            ↓
        MotorAutorreparacion
            ↓
        decisión
            ↓
        reparación opcional

    El supervisor no modifica archivos directamente.
    """

    def __init__(
        self,
        desarrollo: SistemaDesarrolloAtenas | None = None,
        motor: MotorAutorreparacion | None = None,
        max_eventos: int = 100,
        reparar_automaticamente: bool = True,
    ):
        self.desarrollo = desarrollo

        self.motor = (
            motor
            or MotorAutorreparacion(
                desarrollo=desarrollo,
                max_intentos_por_error=2,
                cooldown_segundos=60.0,
                autoaplicar_bajo_riesgo=True,
            )
        )

        self.max_eventos = max(
            10,
            int(max_eventos),
        )

        self.reparar_automaticamente = bool(
            reparar_automaticamente
        )

        self._eventos: list[EventoError] = []

        self._procesando_error = False

    # =========================================================
    # CREAR EVENTO
    # =========================================================

    def crear_evento(
        self,
        error: BaseException,
        modulo: str | None = None,
        funcion: str | None = None,
        componente: str | None = None,
        diagnosticar: bool = True,
        intentar_reparacion: bool | None = None,
        tests: list[str] | None = None,
    ) -> EventoError:

        traceback_texto = "".join(
            traceback_lib.format_exception(
                type(error),
                error,
                error.__traceback__,
            )
        )

        evento = EventoError(
            id=str(uuid.uuid4()),
            tipo=type(error).__name__,
            mensaje=str(error),
            traceback=traceback_texto,
            modulo=modulo,
            funcion=funcion,
            componente=componente,
            creado_en=(
                datetime.now()
                .astimezone()
                .isoformat()
            ),
        )

        self._registrar(evento)

        if diagnosticar:
            self.diagnosticar(evento)

        if intentar_reparacion is None:
            intentar_reparacion = (
                self.reparar_automaticamente
            )

        if intentar_reparacion:
            self.procesar_reparacion(
                evento=evento,
                tests=tests,
            )

        return evento

    # =========================================================
    # TRACEBACK EXTERNO
    # =========================================================

    def registrar_traceback(
        self,
        traceback_texto: str,
        tipo: str = "Error",
        mensaje: str = "",
        modulo: str | None = None,
        funcion: str | None = None,
        componente: str | None = None,
        diagnosticar: bool = True,
        intentar_reparacion: bool | None = None,
        tests: list[str] | None = None,
    ) -> EventoError:

        evento = EventoError(
            id=str(uuid.uuid4()),
            tipo=tipo,
            mensaje=mensaje,
            traceback=(traceback_texto or "").strip(),
            modulo=modulo,
            funcion=funcion,
            componente=componente,
            creado_en=(
                datetime.now()
                .astimezone()
                .isoformat()
            ),
        )

        self._registrar(evento)

        if diagnosticar:
            self.diagnosticar(evento)

        if intentar_reparacion is None:
            intentar_reparacion = (
                self.reparar_automaticamente
            )

        if intentar_reparacion:
            self.procesar_reparacion(
                evento=evento,
                tests=tests,
            )

        return evento

    # =========================================================
    # REGISTRAR
    # =========================================================

    def _registrar(
        self,
        evento: EventoError,
    ) -> None:

        self._eventos.append(evento)

        if len(self._eventos) > self.max_eventos:
            self._eventos = self._eventos[
                -self.max_eventos:
            ]

    # =========================================================
    # DIAGNOSTICAR
    # =========================================================

    def diagnosticar(
        self,
        evento: EventoError,
    ):

        if evento.diagnosticado:
            return evento.diagnostico

        if self.desarrollo is None:
            return None

        if not evento.traceback:
            return None

        try:

            resultado = (
                self.desarrollo
                .diagnosticar(
                    evento.traceback
                )
            )

            evento.diagnostico = resultado
            evento.diagnosticado = (
                resultado is not None
            )

            return resultado

        except Exception as error:

            print(
                "[ATENAS][SUPERVISOR][DIAGNOSTICO] "
                f"{type(error).__name__}: {error}"
            )

            return None

    # =========================================================
    # PROCESAR REPARACIÓN
    # =========================================================

    def procesar_reparacion(
        self,
        evento: EventoError,
        tests: list[str] | None = None,
    ) -> ResultadoMotorAutorreparacion | None:

        if self.motor is None:
            return None

        if self._procesando_error:
            return None

        if evento.reparacion_iniciada:
            resultado = (
                evento.resultado_reparacion
            )

            if isinstance(
                resultado,
                ResultadoMotorAutorreparacion,
            ):
                return resultado

            return None

        if not evento.diagnosticado:
            self.diagnosticar(evento)

        self._procesando_error = True

        try:

            resultado = (
                self.motor.procesar(
                    evento=evento,
                    tests=tests,
                )
            )

            evento.reparacion_iniciada = (
                resultado.procesado
            )

            evento.resultado_reparacion = (
                resultado
            )

            reparacion = (
                resultado.resultado_reparacion
            )

            aplicado = False

            if reparacion is not None:

                if isinstance(
                    reparacion,
                    dict,
                ):
                    aplicado = bool(
                        reparacion.get(
                            "aplicado",
                            False,
                        )
                    )

                else:
                    aplicado = bool(
                        getattr(
                            reparacion,
                            "aplicado",
                            False,
                        )
                    )

            evento.resuelto = aplicado

            return resultado

        except Exception as error:

            print(
                "[ATENAS][SUPERVISOR][REPARACION] "
                f"{type(error).__name__}: {error}"
            )

            return None

        finally:

            self._procesando_error = False

    # =========================================================
    # EJECUTAR FUNCIÓN SUPERVISADA
    # =========================================================

    def ejecutar(
        self,
        funcion: Callable[..., Any],
        *args,
        modulo: str | None = None,
        nombre_funcion: str | None = None,
        componente: str | None = None,
        diagnosticar: bool = True,
        intentar_reparacion: bool | None = None,
        tests: list[str] | None = None,
        relanzar: bool = False,
        **kwargs,
    ) -> dict:

        try:

            resultado = funcion(
                *args,
                **kwargs,
            )

            return {
                "ok": True,
                "resultado": resultado,
                "evento": None,
            }

        except Exception as error:

            evento = self.crear_evento(
                error=error,
                modulo=modulo,
                funcion=(
                    nombre_funcion
                    or getattr(
                        funcion,
                        "__name__",
                        None,
                    )
                ),
                componente=componente,
                diagnosticar=diagnosticar,
                intentar_reparacion=(
                    intentar_reparacion
                ),
                tests=tests,
            )

            self.mostrar_evento(evento)

            if relanzar:
                raise

            return {
                "ok": False,
                "resultado": None,
                "evento": evento,
            }

    # =========================================================
    # MOSTRAR EVENTO
    # =========================================================

    @staticmethod
    def mostrar_evento(
        evento: EventoError,
    ) -> None:

        print()
        print("[ATENAS][ERROR]")
        print(f"Tipo: {evento.tipo}")
        print(f"Mensaje: {evento.mensaje}")

        if evento.componente:
            print(
                "Componente: "
                f"{evento.componente}"
            )

        if evento.modulo:
            print(
                f"Módulo: {evento.modulo}"
            )

        if evento.funcion:
            print(
                f"Función: {evento.funcion}"
            )

        if evento.diagnostico is not None:

            categoria = getattr(
                evento.diagnostico,
                "categoria",
                None,
            )

            archivo = getattr(
                evento.diagnostico,
                "archivo_principal",
                None,
            )

            if categoria:
                print(
                    "Diagnóstico: "
                    f"{categoria}"
                )

            if archivo:
                print(
                    "Archivo probable: "
                    f"{archivo}"
                )

        if evento.reparacion_iniciada:
            print(
                "Reparación iniciada: sí"
            )

        if evento.resuelto:
            print(
                "Resuelto: sí"
            )

    # =========================================================
    # CONSULTAS
    # =========================================================

    def ultimo(
        self,
    ) -> EventoError | None:

        if not self._eventos:
            return None

        return self._eventos[-1]

    def recientes(
        self,
        limite: int = 10,
    ) -> list[EventoError]:

        limite = max(
            1,
            min(
                int(limite),
                self.max_eventos,
            ),
        )

        return self._eventos[
            -limite:
        ]

    def pendientes_reparacion(
        self,
    ) -> list[EventoError]:

        return [
            evento
            for evento
            in self._eventos
            if (
                not evento.resuelto
                and evento.diagnosticado
            )
        ]

    def contar(
        self,
    ) -> int:

        return len(
            self._eventos
        )

    # =========================================================
    # CONTEXTO PARA LLM
    # =========================================================

    def contexto_para_llm(
        self,
        limite: int = 5,
    ) -> str:

        eventos = self.recientes(
            limite=limite
        )

        if not eventos:

            return (
                "ERRORES INTERNOS RECIENTES DE ATENAS:\n"
                "- Ningún error registrado."
            )

        lineas = [
            "ERRORES INTERNOS RECIENTES DE ATENAS:"
        ]

        for evento in eventos:

            linea = (
                f"- {evento.tipo}: "
                f"{evento.mensaje}"
            )

            if evento.componente:
                linea += (
                    " | componente="
                    f"{evento.componente}"
                )

            if evento.modulo:
                linea += (
                    " | módulo="
                    f"{evento.modulo}"
                )

            if evento.funcion:
                linea += (
                    " | función="
                    f"{evento.funcion}"
                )

            if evento.diagnosticado:

                categoria = getattr(
                    evento.diagnostico,
                    "categoria",
                    None,
                )

                if categoria:
                    linea += (
                        " | diagnóstico="
                        f"{categoria}"
                    )

            if evento.reparacion_iniciada:
                linea += (
                    " | reparación=iniciada"
                )

            if evento.resuelto:
                linea += (
                    " | resuelto=sí"
                )

            lineas.append(linea)

        return "\n".join(lineas)