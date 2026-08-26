from __future__ import annotations

import json
import tempfile

from pathlib import Path

from atenas.cerebro.agente.estado_agente import (
    EstadoOperativoAgente,
    GestorEstadoAgente,
)
from atenas.cerebro.agente.gestor_confirmaciones import (
    GestorConfirmaciones,
)
from atenas.cerebro.agente.gestor_contexto_operativo import (
    GestorContextoOperativo,
)
from atenas.cerebro.agente.gestor_sesion_trabajo import (
    GestorSesionTrabajo,
)
from atenas.cerebro.agente.registro_actividad_agente import (
    RegistroActividadAgente,
)
from atenas.cerebro.agente.registro_tareas_escritorio import (
    RegistroTareasEscritorio,
)
from atenas.cerebro.agente.tareas_escritorio import (
    EstadoPasoEscritorio,
    EstadoTareaEscritorio,
    PasoTareaEscritorio,
    TareaEscritorio,
    TipoPasoEscritorio,
)


def titulo(texto: str) -> None:
    print()
    print("=" * 80)
    print(f" {texto}")
    print("=" * 80)
    print()


def main() -> None:
    titulo("AGENTE V1 E2E - ESTADO + PERSISTENCIA + REINICIO")

    with tempfile.TemporaryDirectory() as temporal:
        raiz = Path(temporal)

        contexto = GestorContextoOperativo(
            raiz / "contexto.json"
        )

        sesiones = GestorSesionTrabajo(
            raiz / "sesiones.json"
        )

        tareas = RegistroTareasEscritorio(
            raiz / "tareas.json"
        )

        confirmaciones = GestorConfirmaciones(
            raiz / "confirmaciones.json"
        )

        actividad = RegistroActividadAgente(
            raiz / "actividad.jsonl"
        )

        # -----------------------------------------------------
        # 1. Contexto operativo
        # -----------------------------------------------------

        contexto.actualizar(
            proyecto_actual_id="proyecto-demo",
            ruta_proyecto_actual=str(
                raiz / "Proyecto Demo"
            ),
            nombre_proyecto_actual="Proyecto Demo",
            lenguaje="Python",
            framework="FastAPI",
            base_datos="PostgreSQL",
        )

        # -----------------------------------------------------
        # 2. Sesión
        # -----------------------------------------------------

        sesion = sesiones.crear(
            nombre="Preparar Proyecto Demo",
            objetivo_superior=(
                "Dejar el proyecto listo para revisión."
            ),
            proyecto_id="proyecto-demo",
            resultado_esperado=(
                "Proyecto funcional y validado."
            ),
        )

        # -----------------------------------------------------
        # 3. Tarea con un paso ya completado
        # -----------------------------------------------------

        tarea = TareaEscritorio(
            id="tarea-demo",
            nombre="Validar proyecto",
            descripcion=(
                "Validar el proyecto antes de la entrega."
            ),
            pasos=[
                PasoTareaEscritorio(
                    id="paso-1",
                    tipo=TipoPasoEscritorio.VERIFICAR_CARPETA,
                    descripcion="Verificar carpeta",
                    argumentos={
                        "ruta":
                            str(
                                raiz / "Proyecto Demo"
                            )
                    },
                    estado=EstadoPasoEscritorio.COMPLETADO,
                ),
                PasoTareaEscritorio(
                    id="paso-2",
                    tipo=TipoPasoEscritorio.OBSERVAR,
                    descripcion="Observar estado",
                    estado=EstadoPasoEscritorio.PENDIENTE,
                ),
            ],
            estado=EstadoTareaEscritorio.EN_PROGRESO,
            prioridad=0.90,
        )

        tareas.guardar(tarea)

        sesiones.asociar_tarea(
            sesion.id,
            tarea.id,
            hacer_actual=True,
        )

        contexto.actualizar(
            ultima_tarea_id=tarea.id
        )

        actividad.registrar(
            categoria="test",
            accion="estado_inicial",
            mensaje="Estado inicial creado.",
            sesion_id=sesion.id,
            tarea_id=tarea.id,
            proyecto_id="proyecto-demo",
        )

        # -----------------------------------------------------
        # 4. Estado consolidado
        # -----------------------------------------------------

        gestor = GestorEstadoAgente(
            contexto=contexto,
            sesiones=sesiones,
            tareas=tareas,
            confirmaciones=confirmaciones,
            actividad=actividad,
        )

        estado = gestor.construir()

        print("Estado:", estado.estado.value)
        print("Sesión:", estado.sesion_nombre)
        print("Proyecto:", estado.proyecto_nombre)
        print("Tarea:", estado.tarea_nombre)
        print("Tarea estado:", estado.tarea_estado)
        print("Progreso:", estado.progreso)
        print("Confirmaciones:", estado.confirmaciones_pendientes)

        assert estado.estado == EstadoOperativoAgente.TRABAJANDO
        assert estado.sesion_id == sesion.id
        assert estado.tarea_id == tarea.id
        assert estado.proyecto_id == "proyecto-demo"

        # -----------------------------------------------------
        # 5. Confirmación persistente
        # -----------------------------------------------------

        confirmacion = confirmaciones.crear(
            accion="escribir_en_ventana",
            descripcion="Confirmar escritura en aplicación.",
            riesgo=2,
            sesion_id=sesion.id,
            tarea_id=tarea.id,
            proyecto_id="proyecto-demo",
        )

        bloqueado = gestor.construir()

        print()
        print("Estado con confirmación:", bloqueado.estado.value)

        assert bloqueado.estado == EstadoOperativoAgente.BLOQUEADO
        assert bloqueado.confirmaciones_pendientes == 1

        confirmaciones.resolver(
            confirmacion.id,
            aprobar=True,
        )

        # -----------------------------------------------------
        # 6. Simular avance
        # -----------------------------------------------------

        restaurada = tareas.obtener(tarea.id)
        assert restaurada is not None

        restaurada.pasos[1].estado = EstadoPasoEscritorio.COMPLETADO
        restaurada.estado = EstadoTareaEscritorio.COMPLETADA
        tareas.guardar(restaurada)

        sesiones.marcar_tarea_completada(
            sesion.id,
            tarea.id,
        )

        sesiones.completar(
            sesion.id,
            resultado="Proyecto validado.",
        )

        contexto.registrar_error(None)

        actividad.registrar(
            categoria="test",
            accion="completar",
            mensaje="Tarea y sesión completadas.",
            ok=True,
            sesion_id=sesion.id,
            tarea_id=tarea.id,
            proyecto_id="proyecto-demo",
        )

        # -----------------------------------------------------
        # 7. REINICIO SIMULADO
        # -----------------------------------------------------

        print()
        print("-" * 80)
        print(" REINICIO SIMULADO")
        print("-" * 80)

        contexto_2 = GestorContextoOperativo(
            raiz / "contexto.json"
        )

        sesiones_2 = GestorSesionTrabajo(
            raiz / "sesiones.json"
        )

        tareas_2 = RegistroTareasEscritorio(
            raiz / "tareas.json"
        )

        confirmaciones_2 = GestorConfirmaciones(
            raiz / "confirmaciones.json"
        )

        actividad_2 = RegistroActividadAgente(
            raiz / "actividad.jsonl"
        )

        gestor_2 = GestorEstadoAgente(
            contexto=contexto_2,
            sesiones=sesiones_2,
            tareas=tareas_2,
            confirmaciones=confirmaciones_2,
            actividad=actividad_2,
        )

        tarea_2 = tareas_2.obtener(
            tarea.id
        )

        sesion_2 = sesiones_2.obtener(
            sesion.id
        )

        assert tarea_2 is not None
        assert sesion_2 is not None

        print("Tarea restaurada:", tarea_2.estado.value)
        print("Sesión restaurada:", sesion_2.estado.value)
        print(
            "Paso 1 restaurado:",
            tarea_2.pasos[0].estado.value,
        )
        print(
            "Paso 2 restaurado:",
            tarea_2.pasos[1].estado.value,
        )

        assert tarea_2.estado == EstadoTareaEscritorio.COMPLETADA
        assert sesion_2.estado.value == "completada"
        assert all(
            paso.estado == EstadoPasoEscritorio.COMPLETADO
            for paso in tarea_2.pasos
        )

        # El reinicio no recrea ni reinicia pasos completados.
        assert tareas_2.obtener(tarea.id).progreso == 100.0

        estado_final = gestor_2.construir()

        print()
        print("Estado final:", estado_final.estado.value)
        print("Actividad persistida:", len(actividad_2.recientes(50)))

        assert estado_final.confirmaciones_pendientes == 0
        assert len(actividad_2.recientes(50)) >= 2

        titulo("AGENTE V1 E2E CORRECTO")


if __name__ == "__main__":
    main()