from __future__ import annotations

import time
import uuid

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .accion_gui import AccionGUIPlanificada, TipoAccionGUI
from .ciclo_accion_gui import CicloAccionGUI
from .ejecutor_sistema import AccionSistema, EjecutorSistema, TipoAccionSistema
from .registro_tareas_escritorio import RegistroTareasEscritorio
from .gestor_contexto_operativo import GestorContextoOperativo
from .replanificador_tareas_escritorio import (
    ReplanificadorTareasEscritorio,
    ResultadoReplanificacion,
)
from .tareas_escritorio import (
    EstadoPasoEscritorio,
    EstadoTareaEscritorio,
    PasoTareaEscritorio,
    TareaEscritorio,
    TipoPasoEscritorio,
)
from .verificador_visual import CriterioVerificacionVisual


@dataclass
class ResultadoPasoTarea:
    ok: bool
    tarea_id: str
    paso_id: str | None = None
    estado_tarea: str = ""
    estado_paso: str | None = None
    progreso: float = 0.0
    requiere_confirmacion: bool = False
    mensaje: str = ""
    error: str | None = None
    datos: dict[str, Any] = field(default_factory=dict)


class OrquestadorTareasEscritorio:
    def __init__(
        self,
        ejecutor_sistema: EjecutorSistema,
        ciclo_gui: CicloAccionGUI,
        registro: RegistroTareasEscritorio | None = None,
        replanificador: ReplanificadorTareasEscritorio | None = None,
        contexto_operativo: GestorContextoOperativo | None = None,
    ):
        self.ejecutor_sistema = ejecutor_sistema
        self.ciclo_gui = ciclo_gui
        self.registro = registro or RegistroTareasEscritorio()
        self.replanificador = (
            replanificador or ReplanificadorTareasEscritorio()
        )
        self.contexto_operativo = (
            contexto_operativo or GestorContextoOperativo()
        )

    def crear_tarea(
        self,
        nombre: str,
        descripcion: str,
        pasos: list[PasoTareaEscritorio],
        prioridad: float = 0.70,
        creada_por: str = "agente",
        proyecto_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TareaEscritorio:
        tarea = TareaEscritorio(
            id=str(uuid.uuid4()),
            nombre=(nombre or "Tarea de escritorio").strip(),
            descripcion=(descripcion or "").strip(),
            pasos=pasos,
            prioridad=max(0.0, min(1.0, float(prioridad))),
            creada_por=creada_por,
            proyecto_id=proyecto_id,
            metadata=metadata or {},
        )
        self.registro.guardar(tarea)
        self.contexto_operativo.actualizar(
            ultima_tarea_id=tarea.id,
            metadata={
                "ultima_tarea_nombre": tarea.nombre,
            },
        )
        return tarea

    @staticmethod
    def _siguiente_paso(
        tarea: TareaEscritorio,
    ) -> tuple[int, PasoTareaEscritorio] | None:
        for indice, paso in enumerate(tarea.pasos):
            if paso.estado in {
                EstadoPasoEscritorio.PENDIENTE,
                EstadoPasoEscritorio.REQUIERE_CONFIRMACION,
            }:
                return indice, paso
        return None

    @staticmethod
    def _verificar_archivo(ruta: str) -> tuple[bool, dict[str, Any]]:
        archivo = Path(ruta).expanduser().resolve()
        return (
            archivo.exists() and archivo.is_file(),
            {
                "ruta": str(archivo),
                "existe": archivo.exists(),
                "es_archivo": archivo.is_file(),
            },
        )

    @staticmethod
    def _verificar_carpeta(ruta: str) -> tuple[bool, dict[str, Any]]:
        carpeta = Path(ruta).expanduser().resolve()
        return (
            carpeta.exists() and carpeta.is_dir(),
            {
                "ruta": str(carpeta),
                "existe": carpeta.exists(),
                "es_carpeta": carpeta.is_dir(),
            },
        )

    def ejecutar_siguiente(
        self,
        tarea_id: str,
        confirmada: bool = False,
        es_autonoma: bool = True,
    ) -> ResultadoPasoTarea:
        tarea = self.registro.obtener(tarea_id)

        if tarea is None:
            return ResultadoPasoTarea(
                ok=False,
                tarea_id=tarea_id,
                error="tarea_no_encontrada",
            )

        if tarea.completada:
            return ResultadoPasoTarea(
                ok=True,
                tarea_id=tarea.id,
                estado_tarea=tarea.estado.value,
                progreso=100.0,
                mensaje="La tarea ya está completada.",
            )

        siguiente = self._siguiente_paso(tarea)

        if siguiente is None:
            tarea.estado = EstadoTareaEscritorio.COMPLETADA
            self.registro.guardar(tarea)
            return ResultadoPasoTarea(
                ok=True,
                tarea_id=tarea.id,
                estado_tarea=tarea.estado.value,
                progreso=100.0,
                mensaje="Tarea completada.",
            )

        indice, paso = siguiente
        tarea.paso_actual = indice
        tarea.estado = EstadoTareaEscritorio.EN_PROGRESO
        paso.estado = EstadoPasoEscritorio.EN_PROGRESO
        paso.intentos += 1
        self.registro.guardar(tarea)

        try:
            resultado = self._ejecutar_paso(
                paso=paso,
                confirmada=confirmada,
                es_autonoma=es_autonoma,
            )
        except Exception as error:
            resultado = {
                "ok": False,
                "requiere_confirmacion": False,
                "mensaje": "El paso produjo una excepción.",
                "error": f"{type(error).__name__}: {error}",
                "datos": {},
            }

        if resultado.get("requiere_confirmacion", False):
            paso.estado = EstadoPasoEscritorio.REQUIERE_CONFIRMACION
            paso.requiere_confirmacion = True
            tarea.estado = EstadoTareaEscritorio.REQUIERE_CONFIRMACION
            paso.resultado = resultado.get("datos", {}) or {}
            paso.error = resultado.get("error")
            self.registro.guardar(tarea)

            return ResultadoPasoTarea(
                ok=False,
                tarea_id=tarea.id,
                paso_id=paso.id,
                estado_tarea=tarea.estado.value,
                estado_paso=paso.estado.value,
                progreso=tarea.progreso,
                requiere_confirmacion=True,
                mensaje=resultado.get("mensaje", ""),
                error=resultado.get("error"),
                datos=resultado.get("datos", {}) or {},
            )

        if resultado.get("ok", False):
            paso.estado = EstadoPasoEscritorio.COMPLETADO
            paso.requiere_confirmacion = False
            paso.error = None
            paso.resultado = resultado.get("datos", {}) or {}
            tarea.ultimo_error = None

            if self._siguiente_paso(tarea) is None:
                tarea.estado = EstadoTareaEscritorio.COMPLETADA
            else:
                tarea.estado = EstadoTareaEscritorio.EN_PROGRESO
        else:
            paso.error = resultado.get("error") or "paso_fallido"
            paso.resultado = resultado.get("datos", {}) or {}
            tarea.ultimo_error = paso.error

            if paso.intentos < paso.max_intentos:
                paso.estado = EstadoPasoEscritorio.PENDIENTE
                tarea.estado = EstadoTareaEscritorio.PAUSADA
            else:
                paso.estado = EstadoPasoEscritorio.FALLIDO
                tarea.estado = EstadoTareaEscritorio.FALLIDA
                tarea.metadata["replanificacion_sugerida"] = True

        self.registro.guardar(tarea)

        self.contexto_operativo.actualizar(
            ultima_tarea_id=tarea.id,
            ultimo_error=(
                resultado.get("error")
                if not resultado.get("ok", False)
                else None
            ),
            metadata={
                "estado_ultima_tarea":
                    tarea.estado.value,

                "progreso_ultima_tarea":
                    tarea.progreso,

                "ultimo_paso_tarea":
                    paso.descripcion,
            },
        )

        datos_contexto = (
            resultado.get(
                "datos",
                {}
            )
            or {}
        )

        ruta_contexto = (
            datos_contexto.get("ruta")
            or datos_contexto.get("archivo")
            or datos_contexto.get("carpeta")
        )

        if ruta_contexto:

            self.contexto_operativo.registrar_archivo(
                str(
                    ruta_contexto
                )
            )

        titulo_contexto = (
            datos_contexto.get("titulo")
        )

        if titulo_contexto:

            self.contexto_operativo.actualizar(
                ventana_activa=str(
                    titulo_contexto
                )
            )

        return ResultadoPasoTarea(
            ok=bool(resultado.get("ok", False)),
            tarea_id=tarea.id,
            paso_id=paso.id,
            estado_tarea=tarea.estado.value,
            estado_paso=paso.estado.value,
            progreso=tarea.progreso,
            mensaje=resultado.get("mensaje", ""),
            error=resultado.get("error"),
            datos=resultado.get("datos", {}) or {},
        )

    def _ejecutar_paso(
        self,
        paso: PasoTareaEscritorio,
        confirmada: bool,
        es_autonoma: bool,
    ) -> dict[str, Any]:
        args = paso.argumentos or {}
        tipo = paso.tipo

        if tipo == TipoPasoEscritorio.CREAR_CARPETA:
            r = self.ejecutor_sistema.ejecutar(
                AccionSistema(
                    TipoAccionSistema.CREAR_CARPETA,
                    {"ruta": args["ruta"]},
                )
            )
            return {"ok": r.ok, "mensaje": r.mensaje, "error": r.error, "datos": r.datos}

        if tipo == TipoPasoEscritorio.ESCRIBIR_ARCHIVO:
            r = self.ejecutor_sistema.ejecutar(
                AccionSistema(
                    TipoAccionSistema.ESCRIBIR_TEXTO,
                    {
                        "ruta": args["ruta"],
                        "contenido": args.get("contenido", ""),
                        "sobrescribir": bool(args.get("sobrescribir", False)),
                    },
                )
            )
            return {"ok": r.ok, "mensaje": r.mensaje, "error": r.error, "datos": r.datos}

        if tipo == TipoPasoEscritorio.ABRIR_RUTA:
            r = self.ejecutor_sistema.ejecutar(
                AccionSistema(
                    TipoAccionSistema.ABRIR_RUTA,
                    {"ruta": args["ruta"]},
                )
            )
            return {"ok": r.ok, "mensaje": r.mensaje, "error": r.error, "datos": r.datos}

        if tipo == TipoPasoEscritorio.ABRIR_APLICACION:
            r = self.ejecutor_sistema.ejecutar(
                AccionSistema(
                    TipoAccionSistema.ABRIR_APLICACION,
                    {
                        "alias": args["alias"],
                        "argumentos": args.get("argumentos", []),
                    },
                )
            )
            return {"ok": r.ok, "mensaje": r.mensaje, "error": r.error, "datos": r.datos}

        if tipo == TipoPasoEscritorio.ESPERAR_VENTANA:
            titulo = str(args["titulo"])
            timeout = max(0.5, min(30.0, float(args.get("timeout", 8.0))))
            inicio = time.monotonic()

            while time.monotonic() - inicio < timeout:
                encontrada = self.ejecutor_sistema.gestor_ventanas.buscar(titulo)
                if encontrada.ok and encontrada.ventana:
                    return {
                        "ok": True,
                        "mensaje": f"Ventana '{encontrada.ventana.titulo}' detectada.",
                        "datos": {
                            "hwnd": encontrada.ventana.hwnd,
                            "titulo": encontrada.ventana.titulo,
                        },
                    }
                time.sleep(0.20)

            return {
                "ok": False,
                "mensaje": f"No apareció una ventana que contenga '{titulo}'.",
                "error": "timeout_esperando_ventana",
                "datos": {},
            }

        if tipo == TipoPasoEscritorio.ACTIVAR_VENTANA:
            r = self.ejecutor_sistema.gestor_ventanas.activar(
                titulo=str(args["titulo"])
            )
            return {
                "ok": r.ok,
                "mensaje": r.mensaje,
                "error": r.error,
                "datos": {
                    "titulo": r.ventana.titulo if r.ventana else None,
                },
            }

        if tipo == TipoPasoEscritorio.OBSERVAR:
            r = self.ejecutor_sistema.construir_estado_visual(capturar=True)
            return {"ok": r.ok, "mensaje": r.mensaje, "error": r.error, "datos": r.datos}

        if tipo == TipoPasoEscritorio.INTERPRETAR_ESCENA:
            r = self.ejecutor_sistema.interpretar_escena(
                usar_modelo_vision=bool(args.get("usar_modelo_vision", True))
            )
            return {"ok": r.ok, "mensaje": r.mensaje, "error": r.error, "datos": r.datos}

        if tipo == TipoPasoEscritorio.ACCION_GUI:
            accion_datos = args.get("accion", {}) or {}
            criterio_datos = args.get("criterio", {}) or {}

            accion = AccionGUIPlanificada(
                tipo=TipoAccionGUI(accion_datos["tipo"]),
                ventana=accion_datos.get("ventana"),
                x_relativo=accion_datos.get("x_relativo"),
                y_relativo=accion_datos.get("y_relativo"),
                texto=accion_datos.get("texto"),
                teclas=list(accion_datos.get("teclas", []) or []),
                requiere_confirmacion=bool(
                    accion_datos.get("requiere_confirmacion", True)
                ),
                motivo=str(accion_datos.get("motivo", "")),
                metadata=accion_datos.get("metadata", {}) or {},
            )

            criterio = CriterioVerificacionVisual(
                descripcion=str(
                    criterio_datos.get("descripcion", "Verificar resultado visual.")
                ),
                texto_debe_aparecer=criterio_datos.get("texto_debe_aparecer"),
                texto_debe_desaparecer=criterio_datos.get("texto_debe_desaparecer"),
                tipo_elemento_debe_aparecer=criterio_datos.get(
                    "tipo_elemento_debe_aparecer"
                ),
                tipo_elemento_debe_desaparecer=criterio_datos.get(
                    "tipo_elemento_debe_desaparecer"
                ),
                contexto_esperado=criterio_datos.get("contexto_esperado"),
                confianza_minima=float(
                    criterio_datos.get("confianza_minima", 0.65)
                ),
            )

            r = self.ciclo_gui.ejecutar_y_verificar(
                accion=accion,
                criterio=criterio,
                es_autonoma=es_autonoma,
                confirmada=confirmada,
                usar_modelo_vision=bool(args.get("usar_modelo_vision", True)),
            )

            return {
                "ok": r.ok,
                "requiere_confirmacion": r.requiere_confirmacion,
                "mensaje": r.mensaje,
                "error": r.error,
                "datos": r.datos,
            }

        if tipo == TipoPasoEscritorio.VERIFICAR_ARCHIVO:
            ok, datos = self._verificar_archivo(str(args["ruta"]))
            return {
                "ok": ok,
                "mensaje": "Archivo verificado." if ok else "El archivo esperado no existe.",
                "error": None if ok else "archivo_no_verificado",
                "datos": datos,
            }

        if tipo == TipoPasoEscritorio.VERIFICAR_CARPETA:
            ok, datos = self._verificar_carpeta(str(args["ruta"]))
            return {
                "ok": ok,
                "mensaje": "Carpeta verificada." if ok else "La carpeta esperada no existe.",
                "error": None if ok else "carpeta_no_verificada",
                "datos": datos,
            }

        if tipo == TipoPasoEscritorio.VERIFICAR_VENTANA:
            r = self.ejecutor_sistema.gestor_ventanas.buscar(str(args["titulo"]))
            return {
                "ok": r.ok,
                "mensaje": r.mensaje,
                "error": r.error,
                "datos": {
                    "titulo": r.ventana.titulo if r.ventana else None,
                },
            }

        return {
            "ok": False,
            "mensaje": "Tipo de paso no soportado.",
            "error": "tipo_paso_no_soportado",
            "datos": {},
        }

    def replanificar_tarea(
        self,
        tarea_id: str,
        motivo: str,
        contexto_nuevo: dict[str, Any] | None = None,
        objetivo_actualizado: str | None = None,
    ) -> ResultadoReplanificacion:
        tarea = self.registro.obtener(tarea_id)

        if tarea is None:
            return ResultadoReplanificacion(
                ok=False,
                error="tarea_no_encontrada",
                motivo=motivo,
            )

        resultado = self.replanificador.replanificar(
            tarea=tarea,
            motivo=motivo,
            contexto_nuevo=contexto_nuevo,
            objetivo_actualizado=objetivo_actualizado,
        )

        if resultado.ok and resultado.tarea is not None:
            self.registro.guardar(resultado.tarea)

        return resultado

    def evaluar_y_replanificar_si_conviene(
        self,
        tarea_id: str,
        contexto_nuevo: dict[str, Any] | None = None,
    ) -> ResultadoReplanificacion:
        tarea = self.registro.obtener(tarea_id)

        if tarea is None:
            return ResultadoReplanificacion(
                ok=False,
                error="tarea_no_encontrada",
                motivo="No se pudo evaluar la tarea.",
            )

        conviene, motivo = self.replanificador.conviene_replanificar(tarea)

        if not conviene:
            return ResultadoReplanificacion(
                ok=False,
                tarea=tarea,
                motivo=motivo,
                error="replanificacion_no_necesaria",
            )

        contexto_combinado = (
            self.contexto_operativo
            .para_planificacion()
        )

        contexto_combinado.update(
            contexto_nuevo
            or {}
        )

        return self.replanificar_tarea(
            tarea_id=tarea_id,
            motivo=motivo,
            contexto_nuevo=contexto_combinado,
        )

    def ejecutar_hasta_pausa(
        self,
        tarea_id: str,
        max_pasos: int = 5,
        es_autonoma: bool = True,
    ) -> list[ResultadoPasoTarea]:
        resultados = []

        for _ in range(max(1, int(max_pasos))):
            r = self.ejecutar_siguiente(
                tarea_id=tarea_id,
                confirmada=False,
                es_autonoma=es_autonoma,
            )
            resultados.append(r)

            if (
                r.requiere_confirmacion
                or not r.ok
                or r.estado_tarea in {
                    EstadoTareaEscritorio.COMPLETADA.value,
                    EstadoTareaEscritorio.FALLIDA.value,
                }
            ):
                break

        return resultados