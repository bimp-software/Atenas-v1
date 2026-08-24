from __future__ import annotations

import ctypes
import json
import os

from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path


class TipoProyectoExterno(str, Enum):
    PERSONAL = "personal"
    CLIENTE = "cliente"
    EXPERIMENTO = "experimento"
    DOCUMENTACION = "documentacion"
    OTRO = "otro"


@dataclass
class PerfilEspaciosTrabajo:
    proyectos_personales: str
    proyectos_clientes: str
    experimentos: str
    documentacion: str


@dataclass
class DestinoProyecto:
    tipo: TipoProyectoExterno
    raiz: str
    carpeta_proyecto: str
    cliente: str | None = None


class GestorEspaciosTrabajo:
    """
    Gestiona las ubicaciones reales donde ATENAS puede crear
    proyectos externos.

    En Windows intenta detectar las carpetas reales de:
    - Escritorio
    - Documentos

    Esto evita asumir que siempre están en:
        C:\\Users\\usuario\\Desktop
        C:\\Users\\usuario\\Documents

    ya que pueden estar redirigidas por OneDrive o por Windows.

    La configuración queda persistida en JSON.
    """

    # Known Folder IDs de Windows.
    # https://learn.microsoft.com/windows/win32/shell/knownfolderid

    FOLDERID_DESKTOP = (
        "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"
    )

    FOLDERID_DOCUMENTS = (
        "{FDD39AD0-238F-46AF-ADB4-6C85480369C7}"
    )

    def __init__(
        self,
        config_path: str | Path,
    ):
        self.config_path = Path(
            config_path
        ).resolve()

        self.config_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.perfil = (
            self._cargar_o_crear()
        )

    # =========================================================
    # WINDOWS KNOWN FOLDERS
    # =========================================================

    @staticmethod
    def _guid_desde_texto(
        guid_texto: str,
    ):
        """
        Convierte un GUID textual a estructura GUID de ctypes.
        """

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        texto = (
            guid_texto
            .strip()
            .strip("{}")
        )

        partes = (
            texto.split("-")
        )

        if len(partes) != 5:

            raise ValueError(
                f"GUID inválido: {guid_texto}"
            )

        data1 = int(
            partes[0],
            16,
        )

        data2 = int(
            partes[1],
            16,
        )

        data3 = int(
            partes[2],
            16,
        )

        data4_hex = (
            partes[3]
            + partes[4]
        )

        data4 = (
            ctypes.c_ubyte * 8
        )(
            *[
                int(
                    data4_hex[
                        i:
                        i + 2
                    ],
                    16,
                )
                for i
                in range(
                    0,
                    16,
                    2,
                )
            ]
        )

        return GUID(
            data1,
            data2,
            data3,
            data4,
        )

    @classmethod
    def _known_folder_windows(
        cls,
        folder_id: str,
    ) -> Path | None:
        """
        Devuelve una carpeta conocida real de Windows.

        Ejemplos:
        - Desktop real
        - Documents real

        Si falla, retorna None.
        """

        if os.name != "nt":
            return None

        try:

            shell32 = (
                ctypes.windll.shell32
            )

            ole32 = (
                ctypes.windll.ole32
            )

            guid = (
                cls._guid_desde_texto(
                    folder_id
                )
            )

            ruta_ptr = (
                ctypes.c_wchar_p()
            )

            resultado = (
                shell32
                .SHGetKnownFolderPath(
                    ctypes.byref(
                        guid
                    ),
                    0,
                    None,
                    ctypes.byref(
                        ruta_ptr
                    ),
                )
            )

            if resultado != 0:

                return None

            if not ruta_ptr.value:

                return None

            ruta = Path(
                ruta_ptr.value
            ).resolve()

            try:

                ole32.CoTaskMemFree(
                    ctypes.cast(
                        ruta_ptr,
                        ctypes.c_void_p,
                    )
                )

            except Exception:
                pass

            return ruta

        except Exception:

            return None

    # =========================================================
    # DETECCIÓN DE ESCRITORIO
    # =========================================================

    @classmethod
    def detectar_escritorio(
        cls,
    ) -> Path:

        # 1. API oficial de Windows.
        ruta = (
            cls._known_folder_windows(
                cls.FOLDERID_DESKTOP
            )
        )

        if ruta is not None:
            return ruta

        home = Path.home()

        # 2. OneDrive común.
        candidatos = [
            home
            / "OneDrive"
            / "Desktop",

            home
            / "OneDrive"
            / "Escritorio",

            home
            / "Desktop",

            home
            / "Escritorio",
        ]

        for candidato in candidatos:

            if candidato.exists():
                return candidato.resolve()

        # 3. Fallback.
        return (
            home
            / "Desktop"
        ).resolve()

    # =========================================================
    # DETECCIÓN DE DOCUMENTOS
    # =========================================================

    @classmethod
    def detectar_documentos(
        cls,
    ) -> Path:

        # 1. API oficial de Windows.
        ruta = (
            cls._known_folder_windows(
                cls.FOLDERID_DOCUMENTS
            )
        )

        if ruta is not None:
            return ruta

        home = Path.home()

        candidatos = [
            home
            / "OneDrive"
            / "Documents",

            home
            / "OneDrive"
            / "Documentos",

            home
            / "Documents",

            home
            / "Documentos",
        ]

        for candidato in candidatos:

            if candidato.exists():
                return candidato.resolve()

        return (
            home
            / "Documents"
        ).resolve()

    # =========================================================
    # PERFIL POR DEFECTO
    # =========================================================

    def _perfil_por_defecto(
        self,
    ) -> PerfilEspaciosTrabajo:

        escritorio = (
            self.detectar_escritorio()
        )

        documentos = (
            self.detectar_documentos()
        )

        return PerfilEspaciosTrabajo(

            proyectos_personales=str(
                (
                    documentos
                    / "Proyectos"
                ).resolve()
            ),

            proyectos_clientes=str(
                (
                    escritorio
                    / "Clientes"
                ).resolve()
            ),

            experimentos=str(
                (
                    documentos
                    / "Proyectos"
                    / "Experimentos"
                ).resolve()
            ),

            documentacion=str(
                (
                    documentos
                    / "Documentacion"
                ).resolve()
            ),
        )

    # =========================================================
    # CARGAR / GUARDAR
    # =========================================================

    def _cargar_o_crear(
        self,
    ) -> PerfilEspaciosTrabajo:

        if self.config_path.exists():

            try:

                datos = json.loads(
                    self.config_path
                    .read_text(
                        encoding="utf-8"
                    )
                )

                perfil = (
                    PerfilEspaciosTrabajo(
                        proyectos_personales=str(
                            datos[
                                "proyectos_personales"
                            ]
                        ),
                        proyectos_clientes=str(
                            datos[
                                "proyectos_clientes"
                            ]
                        ),
                        experimentos=str(
                            datos[
                                "experimentos"
                            ]
                        ),
                        documentacion=str(
                            datos[
                                "documentacion"
                            ]
                        ),
                    )
                )

                self._asegurar_raices(
                    perfil
                )

                return perfil

            except Exception:

                pass

        perfil = (
            self._perfil_por_defecto()
        )

        self.guardar_perfil(
            perfil
        )

        return perfil

    def _asegurar_raices(
        self,
        perfil: PerfilEspaciosTrabajo,
    ) -> None:
        """
        Crea las carpetas base si todavía no existen.
        """

        for ruta in [
            perfil.proyectos_personales,
            perfil.proyectos_clientes,
            perfil.experimentos,
            perfil.documentacion,
        ]:

            Path(
                ruta
            ).mkdir(
                parents=True,
                exist_ok=True,
            )

    def guardar_perfil(
        self,
        perfil: PerfilEspaciosTrabajo,
    ) -> None:

        self._asegurar_raices(
            perfil
        )

        self.config_path.write_text(
            json.dumps(
                asdict(
                    perfil
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        self.perfil = perfil

    # =========================================================
    # NOMBRES SEGUROS
    # =========================================================

    @staticmethod
    def _nombre_seguro(
        texto: str,
    ) -> str:

        texto = (
            texto
            or ""
        ).strip()

        invalidos = '<>:"/\\|?*'

        for caracter in invalidos:

            texto = (
                texto.replace(
                    caracter,
                    "_",
                )
            )

        texto = " ".join(
            texto.split()
        )

        texto = texto.strip(
            " ."
        )

        return (
            texto
            or "Proyecto"
        )[:100]

    # =========================================================
    # RESOLVER DESTINO
    # =========================================================

    def resolver(
        self,
        tipo: TipoProyectoExterno,
        nombre_proyecto: str,
        cliente: str | None = None,
    ) -> DestinoProyecto:

        nombre = (
            self._nombre_seguro(
                nombre_proyecto
            )
        )

        if tipo == TipoProyectoExterno.CLIENTE:

            raiz = Path(
                self.perfil
                .proyectos_clientes
            )

            if cliente:

                raiz = (
                    raiz
                    / self._nombre_seguro(
                        cliente
                    )
                )

        elif tipo == TipoProyectoExterno.PERSONAL:

            raiz = Path(
                self.perfil
                .proyectos_personales
            )

        elif tipo == TipoProyectoExterno.EXPERIMENTO:

            raiz = Path(
                self.perfil
                .experimentos
            )

        elif tipo == TipoProyectoExterno.DOCUMENTACION:

            raiz = Path(
                self.perfil
                .documentacion
            )

        else:

            raiz = Path(
                self.perfil
                .proyectos_personales
            )

        raiz.mkdir(
            parents=True,
            exist_ok=True,
        )

        carpeta = (
            raiz
            / nombre
        ).resolve()

        return DestinoProyecto(
            tipo=tipo,
            raiz=str(
                raiz.resolve()
            ),
            carpeta_proyecto=str(
                carpeta
            ),
            cliente=cliente,
        )

    # =========================================================
    # DIAGNÓSTICO
    # =========================================================

    def diagnostico(
        self,
    ) -> dict:

        escritorio = (
            self.detectar_escritorio()
        )

        documentos = (
            self.detectar_documentos()
        )

        return {
            "escritorio_detectado":
                str(
                    escritorio
                ),

            "documentos_detectados":
                str(
                    documentos
                ),

            "perfil":
                asdict(
                    self.perfil
                ),

            "config_path":
                str(
                    self.config_path
                ),
        }