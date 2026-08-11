from dataclasses import dataclass

@dataclass
class CapacidadesAtenas:
    conversacion: bool = True
    historial_temporal: bool = True
    ollama: bool = True

    voz_entrada: bool = False
    voz_salida: bool = True

    vision: bool = False
    memoria_persistente: bool = False
    internet: bool = False

    control_dispositivos: bool = False
    control_robot: bool = False
    movimiento: bool = False

    spider_bot: bool = False

    def como_texto(self) -> str:
        capacidades = {
            "Conversación": self.conversacion,
            "Historial temporal": self.historial_temporal,
            "Modelo local Ollama": self.ollama,
            "Escuchar mediante micrófono": self.voz_entrada,
            "Hablar mediante voz": self.voz_salida,
            "Visión por cámara": self.vision,
            "Memoria permanente": self.memoria_persistente,
            "Acceso a Internet": self.internet,
            "Control de dispositivos": self.control_dispositivos,
            "Control robótico": self.control_robot,
            "Movimiento físico": self.movimiento,
            "Spider-Bot conectado": self.spider_bot,
        }

        activas = []
        no_disponibles = []

        for nombre, disponible in capacidades.items():
            if disponible:
                activas.append(f"- {nombre}: disponible")
            else:
                no_disponibles.append(f"- {nombre}: no disponible")

        return (
            "CAPACIDADES DISPONIBLES ACTUALMENTE:\n"
            + "\n".join(activas)
            + "\n\nCAPACIDADES TODAVÍA NO DISPONIBLES:\n"
            + "\n".join(no_disponibles)
        )