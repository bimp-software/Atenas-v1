from __future__ import annotations
import json, re, uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
from .analista_requisitos import AnalisisRequisitos
from .arquitecto_software import ArquitecturaSoftware
from .disenador_base_datos import ModeloBaseDatos

class EstadoTarea(str, Enum):
    PENDIENTE="pendiente"; BLOQUEADA="bloqueada"; EN_PROGRESO="en_progreso"
    COMPLETADA="completada"; FALLIDA="fallida"; CANCELADA="cancelada"

@dataclass
class TareaSoftware:
    id:str; titulo:str; descripcion:str; tipo:str; prioridad:float
    depende_de:list[str]=field(default_factory=list)
    criterios_aceptacion:list[str]=field(default_factory=list)
    archivos_estimados:list[str]=field(default_factory=list)
    lenguaje:str|None=None; tecnologia:str|None=None
    requiere_pruebas:bool=True; requiere_documentacion:bool=False
    estado:EstadoTarea=EstadoTarea.PENDIENTE

@dataclass
class EpicaSoftware:
    id:str; nombre:str; descripcion:str; prioridad:float
    tareas:list[TareaSoftware]=field(default_factory=list)

@dataclass
class FaseSoftware:
    id:str; nombre:str; objetivo:str; orden:int
    epicas:list[EpicaSoftware]=field(default_factory=list)

@dataclass
class PlanSistemaSoftware:
    id:str; nombre_proyecto:str; tipo_solucion:str; arquitectura:str; complejidad:str
    fases:list[FaseSoftware]=field(default_factory=list)
    ruta_persistencia:str|None=None

class PlanificadorSistemaSoftware:
    def __init__(self,llm:Any,raiz_planes:str|Path):
        self.llm=llm
        self.raiz_planes=Path(raiz_planes).resolve()
        self.raiz_planes.mkdir(parents=True,exist_ok=True)

    def _preguntar(self,mensajes):
        if hasattr(self.llm,"chat"):
            r=self.llm.chat(mensajes)
            if isinstance(r,str): return r
            if isinstance(r,dict):
                m=r.get("message") or {}
                if isinstance(m,dict) and m.get("content"): return str(m["content"])
                if r.get("content"): return str(r["content"])
        raise RuntimeError("LLM incompatible.")

    @staticmethod
    def _extraer_json(texto):
        texto=(texto or "").strip()
        m=re.search(r"```(?:json)?\s*(\{.*\})\s*```",texto,re.DOTALL)
        if m: texto=m.group(1)
        else:
            i,f=texto.find("{"),texto.rfind("}")
            if i<0 or f<=i: raise ValueError("No se encontró JSON.")
            texto=texto[i:f+1]
        d=json.loads(texto)
        if not isinstance(d,dict): raise ValueError("JSON inválido.")
        return d

    @staticmethod
    def _entrada(a,ar,bd):
        return {"analisis":asdict(a),"arquitectura":asdict(ar),"base_datos":asdict(bd) if bd else None}

    def planificar(self,analisis:AnalisisRequisitos,arquitectura:ArquitecturaSoftware,modelo_bd:ModeloBaseDatos|None):
        system="""Eres el planificador principal de desarrollo de ATENAS.
Divide un sistema completo en fases, épicas y tareas pequeñas, verificables y dependientes.
No construyas todo de una vez. Respeta la arquitectura elegida.
Incluye cuando corresponda: preparación, persistencia/migraciones, backend/core,
autenticación/autorización, módulos de negocio, interfaz, integraciones,
pruebas, seguridad, despliegue y documentación.
Devuelve SOLO JSON:
{"fases":[{"id":"F1","nombre":"...","objetivo":"...","orden":1,"epicas":[{"id":"E1","nombre":"...","descripcion":"...","prioridad":0.9,"tareas":[{"id":"T1","titulo":"...","descripcion":"...","tipo":"backend","prioridad":0.9,"depende_de":[],"criterios_aceptacion":[],"archivos_estimados":[],"lenguaje":"python","tecnologia":"FastAPI","requiere_pruebas":true,"requiere_documentacion":false}]}]}]}
Máximo 12 fases, 12 épicas/fase y 20 tareas/épica. No uses tareas gigantes."""
        datos=self._extraer_json(self._preguntar([
            {"role":"system","content":system},
            {"role":"user","content":json.dumps(self._entrada(analisis,arquitectura,modelo_bd),ensure_ascii=False,indent=2,default=str)}
        ]))
        mapa={}; tareas_totales=[]; fases=[]
        for nf,fd in enumerate(datos.get("fases",[])[:12],1):
            epicas=[]
            for ed in fd.get("epicas",[])[:12]:
                tareas=[]
                for td in ed.get("tareas",[])[:20]:
                    ext=str(td.get("id") or uuid.uuid4()); interno=str(uuid.uuid4()); mapa[ext]=interno
                    t=TareaSoftware(
                        id=interno,titulo=str(td.get("titulo","Tarea")),descripcion=str(td.get("descripcion","")),
                        tipo=str(td.get("tipo","implementacion")),prioridad=max(0,min(float(td.get("prioridad",.5) or .5),1)),
                        depende_de=[str(x) for x in td.get("depende_de",[])],
                        criterios_aceptacion=[str(x) for x in td.get("criterios_aceptacion",[])],
                        archivos_estimados=[str(x) for x in td.get("archivos_estimados",[])],
                        lenguaje=str(td["lenguaje"]) if td.get("lenguaje") else None,
                        tecnologia=str(td["tecnologia"]) if td.get("tecnologia") else None,
                        requiere_pruebas=bool(td.get("requiere_pruebas",True)),
                        requiere_documentacion=bool(td.get("requiere_documentacion",False)))
                    tareas.append(t); tareas_totales.append(t)
                epicas.append(EpicaSoftware(str(uuid.uuid4()),str(ed.get("nombre","Épica")),str(ed.get("descripcion","")),
                                            max(0,min(float(ed.get("prioridad",.5) or .5),1)),tareas))
            fases.append(FaseSoftware(str(uuid.uuid4()),str(fd.get("nombre","Fase")),str(fd.get("objetivo","")),
                                      int(fd.get("orden",nf) or nf),epicas))
        for t in tareas_totales: t.depende_de=[mapa.get(d,d) for d in t.depende_de]
        plan=PlanSistemaSoftware(str(uuid.uuid4()),analisis.nombre_proyecto,analisis.tipo_solucion.value,
                                 arquitectura.estilo,analisis.complejidad,fases)
        ruta=self.raiz_planes/f"{plan.id}.json"
        ruta.write_text(json.dumps(asdict(plan),ensure_ascii=False,indent=2,default=str),encoding="utf-8")
        plan.ruta_persistencia=str(ruta)
        return plan

    @staticmethod
    def todas_las_tareas(plan):
        return [t for f in plan.fases for e in f.epicas for t in e.tareas]

    @classmethod
    def siguiente_tarea(cls,plan):
        tareas=cls.todas_las_tareas(plan)
        completadas={t.id for t in tareas if t.estado==EstadoTarea.COMPLETADA}
        candidatas=[]
        for t in tareas:
            if t.estado not in {EstadoTarea.PENDIENTE,EstadoTarea.BLOQUEADA}: continue
            if all(d in completadas for d in t.depende_de):
                t.estado=EstadoTarea.PENDIENTE; candidatas.append(t)
            else: t.estado=EstadoTarea.BLOQUEADA
        return max(candidatas,key=lambda x:x.prioridad) if candidatas else None