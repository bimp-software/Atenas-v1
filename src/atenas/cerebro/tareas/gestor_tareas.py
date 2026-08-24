from __future__ import annotations
import json, sqlite3, uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .modelos import EstadoTarea, TareaProgramada, TipoDisparo

class GestorTareas:
    def __init__(self, db_path: str | Path = "data/tareas.db"):
        self.db_path = Path(db_path).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._crear_tabla()

    @staticmethod
    def _ahora() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _conexion(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _crear_tabla(self) -> None:
        with closing(self._conexion()) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tareas (
                    id TEXT PRIMARY KEY,
                    nombre TEXT NOT NULL,
                    descripcion TEXT NOT NULL,
                    herramienta TEXT NOT NULL,
                    argumentos_json TEXT NOT NULL,
                    tipo_disparo TEXT NOT NULL,
                    configuracion_disparo_json TEXT NOT NULL,
                    estado TEXT NOT NULL,
                    requiere_confirmacion INTEGER NOT NULL,
                    origen TEXT NOT NULL,
                    creada_en TEXT NOT NULL,
                    actualizada_en TEXT NOT NULL,
                    ultima_ejecucion TEXT,
                    proxima_ejecucion TEXT,
                    ultimo_resultado_json TEXT,
                    veces_ejecutada INTEGER NOT NULL DEFAULT 0
                )
            """)
            conn.commit()

    @staticmethod
    def _fila_a_tarea(fila: sqlite3.Row) -> TareaProgramada:
        ultimo_resultado = None
        if fila["ultimo_resultado_json"]:
            try:
                ultimo_resultado = json.loads(fila["ultimo_resultado_json"])
            except Exception:
                ultimo_resultado = {"raw": fila["ultimo_resultado_json"]}
        return TareaProgramada(
            id=fila["id"],
            nombre=fila["nombre"],
            descripcion=fila["descripcion"],
            herramienta=fila["herramienta"],
            argumentos=json.loads(fila["argumentos_json"] or "{}"),
            tipo_disparo=TipoDisparo(fila["tipo_disparo"]),
            configuracion_disparo=json.loads(fila["configuracion_disparo_json"] or "{}"),
            estado=EstadoTarea(fila["estado"]),
            requiere_confirmacion=bool(fila["requiere_confirmacion"]),
            origen=fila["origen"],
            creada_en=fila["creada_en"],
            actualizada_en=fila["actualizada_en"],
            ultima_ejecucion=fila["ultima_ejecucion"],
            proxima_ejecucion=fila["proxima_ejecucion"],
            ultimo_resultado=ultimo_resultado,
            veces_ejecutada=int(fila["veces_ejecutada"] or 0),
        )

    def crear(self, nombre: str, descripcion: str, herramienta: str,
              argumentos: dict[str, Any] | None = None,
              tipo_disparo: TipoDisparo = TipoDisparo.MANUAL,
              configuracion_disparo: dict[str, Any] | None = None,
              requiere_confirmacion: bool = False,
              origen: str = "usuario") -> TareaProgramada:
        nombre, descripcion, herramienta = nombre.strip(), descripcion.strip(), herramienta.strip()
        if not nombre: raise ValueError("La tarea necesita un nombre.")
        if not herramienta: raise ValueError("La tarea necesita una herramienta.")
        ahora = self._ahora()
        tarea = TareaProgramada(
            id=str(uuid.uuid4()), nombre=nombre, descripcion=descripcion,
            herramienta=herramienta, argumentos=argumentos or {},
            tipo_disparo=tipo_disparo, configuracion_disparo=configuracion_disparo or {},
            estado=EstadoTarea.ACTIVA, requiere_confirmacion=bool(requiere_confirmacion),
            origen=origen, creada_en=ahora, actualizada_en=ahora,
        )
        with closing(self._conexion()) as conn:
            conn.execute("""INSERT INTO tareas (
                id,nombre,descripcion,herramienta,argumentos_json,tipo_disparo,
                configuracion_disparo_json,estado,requiere_confirmacion,origen,
                creada_en,actualizada_en,ultima_ejecucion,proxima_ejecucion,
                ultimo_resultado_json,veces_ejecutada
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
                tarea.id,tarea.nombre,tarea.descripcion,tarea.herramienta,
                json.dumps(tarea.argumentos, ensure_ascii=False),
                tarea.tipo_disparo.value,
                json.dumps(tarea.configuracion_disparo, ensure_ascii=False),
                tarea.estado.value,int(tarea.requiere_confirmacion),tarea.origen,
                tarea.creada_en,tarea.actualizada_en,None,None,None,0))
            conn.commit()
        return tarea

    def obtener(self, tarea_id: str) -> TareaProgramada | None:
        with closing(self._conexion()) as conn:
            fila = conn.execute("SELECT * FROM tareas WHERE id=? LIMIT 1",(tarea_id,)).fetchone()
        return None if fila is None else self._fila_a_tarea(fila)

    def listar(self, incluir_eliminadas: bool = False) -> list[TareaProgramada]:
        sql = "SELECT * FROM tareas"
        params = ()
        if not incluir_eliminadas:
            sql += " WHERE estado != ?"
            params = (EstadoTarea.ELIMINADA.value,)
        sql += " ORDER BY creada_en DESC"
        with closing(self._conexion()) as conn:
            filas = conn.execute(sql, params).fetchall()
        return [self._fila_a_tarea(f) for f in filas]

    def actualizar(self, tarea_id: str, **cambios) -> TareaProgramada:
        tarea = self.obtener(tarea_id)
        if tarea is None: raise KeyError(f"Tarea no encontrada: {tarea_id}")
        permitidos = {"nombre","descripcion","herramienta","argumentos","tipo_disparo",
                      "configuracion_disparo","estado","requiere_confirmacion","origen",
                      "proxima_ejecucion"}
        for clave, valor in cambios.items():
            if clave not in permitidos: continue
            if clave == "tipo_disparo" and isinstance(valor, str): valor = TipoDisparo(valor)
            if clave == "estado" and isinstance(valor, str): valor = EstadoTarea(valor)
            setattr(tarea, clave, valor)
        tarea.actualizada_en = self._ahora()
        with closing(self._conexion()) as conn:
            conn.execute("""UPDATE tareas SET nombre=?,descripcion=?,herramienta=?,argumentos_json=?,
                tipo_disparo=?,configuracion_disparo_json=?,estado=?,requiere_confirmacion=?,
                origen=?,actualizada_en=?,proxima_ejecucion=? WHERE id=?""", (
                tarea.nombre,tarea.descripcion,tarea.herramienta,
                json.dumps(tarea.argumentos,ensure_ascii=False),tarea.tipo_disparo.value,
                json.dumps(tarea.configuracion_disparo,ensure_ascii=False),tarea.estado.value,
                int(tarea.requiere_confirmacion),tarea.origen,tarea.actualizada_en,
                tarea.proxima_ejecucion,tarea.id))
            conn.commit()
        return tarea

    def pausar(self, tarea_id: str) -> TareaProgramada:
        return self.actualizar(tarea_id, estado=EstadoTarea.PAUSADA)

    def reanudar(self, tarea_id: str) -> TareaProgramada:
        return self.actualizar(tarea_id, estado=EstadoTarea.ACTIVA)

    def eliminar(self, tarea_id: str) -> TareaProgramada:
        return self.actualizar(tarea_id, estado=EstadoTarea.ELIMINADA)

    def registrar_ejecucion(self, tarea_id: str, resultado: dict[str, Any]) -> TareaProgramada:
        if self.obtener(tarea_id) is None: raise KeyError(f"Tarea no encontrada: {tarea_id}")
        ahora = self._ahora()
        with closing(self._conexion()) as conn:
            conn.execute("""UPDATE tareas SET ultima_ejecucion=?,ultimo_resultado_json=?,
                veces_ejecutada=veces_ejecutada+1,actualizada_en=? WHERE id=?""", (
                ahora,json.dumps(resultado,ensure_ascii=False,default=str),ahora,tarea_id))
            conn.commit()
        tarea = self.obtener(tarea_id)
        assert tarea is not None
        return tarea
