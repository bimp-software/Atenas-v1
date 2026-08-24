from __future__ import annotations
import tempfile
from pathlib import Path
from src.atenas.cerebro.tareas import EjecutorTareas, GestorTareas, EstadoTarea, TipoDisparo

class ExecutorFalso:
    def __init__(self): self.llamadas = []
    def ejecutar(self, herramienta, argumentos):
        self.llamadas.append((herramienta, argumentos))
        return {"ok": True, "mensaje": "Herramienta simulada ejecutada."}

def main():
    print()
    print("="*80)
    print(" SISTEMA DE TAREAS - ATENAS")
    print("="*80)
    with tempfile.TemporaryDirectory() as temporal:
        db_path = Path(temporal)/"tareas.db"
        gestor = GestorTareas(db_path=db_path)
        tarea = gestor.crear(
            nombre="Crear nota de estado",
            descripcion="Registrar el estado actual del proyecto.",
            herramienta="crear_nota",
            argumentos={"contenido":"Estado automático de ATENAS."},
            tipo_disparo=TipoDisparo.MANUAL,
            origen="web",
        )
        print("\nTarea creada:", tarea.id)
        assert tarea.estado == EstadoTarea.ACTIVA

        gestor2 = GestorTareas(db_path=db_path)
        assert gestor2.obtener(tarea.id) is not None

        falso = ExecutorFalso()
        ejecutor = EjecutorTareas(gestor=gestor2, executor=falso)
        resultado = ejecutor.ejecutar(tarea.id)
        print("Ejecutada:", resultado.ejecutada)
        print("OK:", resultado.ok)
        assert resultado.ok and resultado.ejecutada
        assert gestor2.obtener(tarea.id).veces_ejecutada == 1

        assert gestor2.pausar(tarea.id).estado == EstadoTarea.PAUSADA
        assert ejecutor.ejecutar(tarea.id).ejecutada is False
        print("Pausa respetada: SÍ")

        gestor2.reanudar(tarea.id)
        sensible = gestor2.crear(
            nombre="Tarea sensible",descripcion="Requiere aprobación.",
            herramienta="crear_nota",argumentos={"contenido":"prueba"},
            requiere_confirmacion=True)
        sin = ejecutor.ejecutar(sensible.id)
        assert sin.requiere_confirmacion and not sin.ejecutada
        con = ejecutor.ejecutar(sensible.id, confirmada=True)
        assert con.ok and con.ejecutada
        print("Confirmación respetada: SÍ")
        print("Tareas visibles:", len(gestor2.listar()))
        assert len(gestor2.listar()) == 2
    print("\n"+"="*80)
    print(" TEST CORRECTO")
    print("="*80)

if __name__ == "__main__":
    main()
