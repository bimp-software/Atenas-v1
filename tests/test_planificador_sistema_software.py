from __future__ import annotations
import json, tempfile
from pathlib import Path
from src.atenas.cerebro.desarrollo.analista_requisitos import AnalisisRequisitos, Requisito, TipoSolucion
from src.atenas.cerebro.desarrollo.arquitecto_software import ArquitecturaSoftware
from src.atenas.cerebro.desarrollo.disenador_base_datos import ModeloBaseDatos
from src.atenas.cerebro.desarrollo.planificador_sistema_software import EstadoTarea, PlanificadorSistemaSoftware

class LLMFalso:
    def chat(self,mensajes):
        return json.dumps({"fases":[
            {"id":"F1","nombre":"Base del sistema","objetivo":"Persistencia y núcleo","orden":1,"epicas":[
                {"id":"E1","nombre":"Persistencia","descripcion":"Datos","prioridad":1.0,"tareas":[
                    {"id":"T1","titulo":"Crear modelos de datos","descripcion":"Modelos iniciales","tipo":"base_datos","prioridad":1.0,"depende_de":[],"criterios_aceptacion":["Modelos importables"],"archivos_estimados":["src/models.py"],"lenguaje":"python","tecnologia":"SQLAlchemy","requiere_pruebas":True,"requiere_documentacion":False},
                    {"id":"T2","titulo":"Crear repositorios","descripcion":"Acceso a datos","tipo":"backend","prioridad":0.9,"depende_de":["T1"],"criterios_aceptacion":["CRUD básico"],"archivos_estimados":["src/repositories.py"],"lenguaje":"python","tecnologia":"SQLAlchemy","requiere_pruebas":True,"requiere_documentacion":False}
                ]}
            ]},
            {"id":"F2","nombre":"API","objetivo":"Exponer operaciones","orden":2,"epicas":[
                {"id":"E2","nombre":"REST API","descripcion":"Endpoints","prioridad":0.85,"tareas":[
                    {"id":"T3","titulo":"Crear endpoints de productos","descripcion":"CRUD REST","tipo":"api","prioridad":0.85,"depende_de":["T2"],"criterios_aceptacion":["Endpoints correctos"],"archivos_estimados":["src/api/products.py"],"lenguaje":"python","tecnologia":"FastAPI","requiere_pruebas":True,"requiere_documentacion":True}
                ]}
            ]}
        ]},ensure_ascii=False)

def main():
    print("\n"+"="*80+"\n PLANIFICADOR DE SISTEMAS COMPLETOS - ATENAS\n"+"="*80)
    analisis=AnalisisRequisitos(nombre_proyecto="Sistema Comercial",tipo_solucion=TipoSolucion.WEB,resumen="Ventas e inventario",requisitos_funcionales=[Requisito(id="RF-001",descripcion="Gestionar productos",prioridad="alta")],necesita_base_datos=True,necesita_api=True,complejidad="alta")
    arquitectura=ArquitecturaSoftware(estilo="monolito_modular",tipo_solucion="web",backend={"tecnologia":"FastAPI","lenguaje":"Python"},base_datos={"motor":"PostgreSQL"})
    modelo=ModeloBaseDatos(motor="postgresql",nombre="sistema_comercial")
    with tempfile.TemporaryDirectory() as temporal:
        p=PlanificadorSistemaSoftware(LLMFalso(),Path(temporal)/"planes")
        plan=p.planificar(analisis,arquitectura,modelo)
        tareas=p.todas_las_tareas(plan)
        print("\nProyecto:",plan.nombre_proyecto); print("Fases:",len(plan.fases)); print("Tareas:",len(tareas))
        assert len(plan.fases)==2 and len(tareas)==3
        t1=p.siguiente_tarea(plan); assert t1 and t1.titulo=="Crear modelos de datos"
        print("\nPrimera tarea:",t1.titulo)
        t1.estado=EstadoTarea.COMPLETADA
        t2=p.siguiente_tarea(plan); assert t2 and t2.titulo=="Crear repositorios"
        print("Después:",t2.titulo)
        assert Path(plan.ruta_persistencia).exists()
        print("\nPlan persistido:",plan.ruta_persistencia)
    print("\n"+"="*80+"\n TEST CORRECTO\n"+"="*80)

if __name__=="__main__": main()