from collections.abc import Generator

from src.config.settings import settings

from src.atenas.cerebro.estado import (
    estado_atenas,
)

from src.atenas.cerebro.historial import (
    HistorialConversacion,
)

from src.atenas.cerebro.llm.ollama_client import (
    OllamaClient,
)

from src.atenas.cerebro.prompts import (
    construir_system_prompt,
)

from src.atenas.cerebro.voz import (
    Hablante,
    hablar_stream,
    EscuchaVoz,
)

from src.atenas.memoria.store_manager import (
    StorageManager,
)

from src.atenas.cerebro.memoria.hipocampo import (
    HipocampoDigital,
    Experiencia,
)

from src.atenas.cerebro.memoria.clasificador import (
    ClasificadorMemoria,
)

from src.atenas.cerebro.memoria.consolidador import (
    ConsolidadorMemoria,
)

from src.atenas.cerebro.memoria.recuperador import (
    RecuperadorMemoria,
)

from src.atenas.cerebro.agente import (
    AgenteAtenas,
)

from src.atenas.cerebro.investigacion import (
    Investigador,
    SintetizadorInvestigacion,
    ConsolidadorInvestigacion,
)

from src.atenas.cerebro.investigacion.clasificador_consulta import (
    ClasificadorConsulta,
)

class NucleoConversacional:

    def __init__(
        self,
    ):

        # =====================================================
        # CONVERSACIÓN
        # =====================================================

        self.historial = (
            HistorialConversacion(
                max_turnos=(
                    settings.llm
                    .max_turnos_historial
                )
            )
        )

        # =====================================================
        # LLM ÚNICO
        # =====================================================

        self.llm = OllamaClient(
            config=settings.llm
        )

        # =====================================================
        # STORAGE ÚNICO
        # =====================================================

        self.storage = (
            StorageManager()
        )

        # =====================================================
        # VOZ
        # =====================================================

        self.hablante = Hablante()

        estado_atenas.capacidades.voz_salida = (
            self.hablante.disponible
        )

        try:

            self.escucha = EscuchaVoz()

            estado_atenas.capacidades.voz_entrada = (
                True
            )

        except Exception as error:

            print(
                "[ATENAS] No fue posible iniciar "
                "el reconocimiento de voz: "
                f"{error}"
            )

            self.escucha = None

            estado_atenas.capacidades.voz_entrada = (
                False
            )

        # =====================================================
        # MEMORIA
        # =====================================================

        self.clasificador_memoria = (
            ClasificadorMemoria()
        )

        self.consolidador_memoria = (
            ConsolidadorMemoria(
                storage=self.storage
            )
        )

        self.recuperador_memoria = (
            RecuperadorMemoria(
                storage=self.storage
            )
        )

        self.hipocampo = (
            HipocampoDigital(
                clasificador=(
                    self.clasificador_memoria
                ),
                consolidador=(
                    self.consolidador_memoria
                ),
                recuperador=(
                    self.recuperador_memoria
                ),
            )
        )

        estado_atenas.capacidades.memoria_persistente = (
            True
        )

        # =====================================================
        # AGENTE
        # =====================================================
        self.agente = (AgenteAtenas(storage=self.storage,llm=self.llm,))
        self.ultima_accion_agente = None
        self.investigador = Investigador(storage=self.storage)
        self.sintetizador_investigacion = (SintetizadorInvestigacion(llm=self.llm))
        self.consolidador_investigacion = (ConsolidadorInvestigacion(storage=self.storage,hipocampo=self.hipocampo,))

        self.ultima_investigacion = None
        self.clasificador_consulta = (ClasificadorConsulta())


    # =========================================================
    # ESCUCHAR
    # =========================================================

    def escuchar(
        self,
        duracion: float = 5.0,
    ) -> str:

        if self.escucha is None:
            return ""

        self.hablante.esperar()

        return self.escucha.escuchar(
            duracion=duracion
        )

    # =========================================================
    # CREAR CONTEXTO
    # =========================================================
    def _crear_mensajes(self,mensaje_usuario: str,contexto_internet: str | None = None,) -> list[dict[str, str]]:
        # =====================================================
        # CLASIFICAR EL TIPO DE CONSULTA
        # =====================================================
        clasificacion_consulta = (self.clasificador_consulta.clasificar(mensaje_usuario))

        # =====================================================
        # MEMORIA
        # =====================================================
        memoria_contexto = ""

        # Para conversación casual, identidad y capacidades
        # NO inyectamos recuerdos semánticos.
        #
        # Estas cosas se resuelven con:
        # - system prompt
        # - estado actual
        # - conversación reciente

        if clasificacion_consulta.tipo not in {"conversacion","identidad","capacidad",}:
            memoria_contexto = (self.recuperador_memoria.contexto_para_llm(mensaje_usuario))

        # =====================================================
        # SYSTEM PROMPT
        # =====================================================

        system_prompt = (construir_system_prompt())

        # =====================================================
        # MEMORIA RELEVANTE
        # =====================================================
        if memoria_contexto:

            system_prompt += (
                "\n\n"
                + memoria_contexto
            )

        # =====================================================
        # INTERNET
        # =====================================================

        if contexto_internet:

            system_prompt += (
                "\n\n"
                "INFORMACIÓN RECIÉN INVESTIGADA "
                "EN INTERNET:\n\n"
                + contexto_internet
                + "\n\n"
                "Utiliza esta información únicamente "
                "para responder la consulta actual. "
                "No inventes información adicional."
            )

        # =====================================================
        # MENSAJES
        # =====================================================

        mensajes = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        mensajes.extend(
            self.historial.obtener()
        )

        mensajes.append({
            "role": "user",
            "content": mensaje_usuario.strip(),
        })

        return mensajes

    # =========================================================
    # RESPONDER STREAM
    # =========================================================

    def responder_stream(
        self,
        mensaje_usuario: str,
        usar_voz: bool = True,
    ) -> Generator[str, None, None]:

        mensaje_usuario = (
            mensaje_usuario.strip()
        )

        if not mensaje_usuario:
            return

        # =====================================================
        # 1. ATENAS OBSERVA EL MENSAJE
        # =====================================================

        pendientes_del_turno = []

        try:

            pendientes_del_turno = (
                self.agente.observar(
                    mensaje_usuario
                )
            )

        except Exception as error:

            print(
                "[ATENAS][AGENTE][OBSERVAR] "
                f"{error}"
            )

        contexto_internet = None

        investigacion = (
            self._investigar_si_es_necesario(
                mensaje_usuario
            )
        )

        if investigacion:

            contexto_internet = (
                investigacion.get(
                    "sintesis"
                )
            )

        # =====================================================
        # 2. RESPUESTA CONVERSACIONAL
        # =====================================================

        mensajes = self._crear_mensajes(
            mensaje_usuario,
            contexto_internet=contexto_internet,
        )

        respuesta_completa = ""

        stream_llm = (
            self.llm.chat_stream(
                mensajes
            )
        )

        if (
            usar_voz
            and self.hablante.disponible
        ):

            stream_salida = (
                hablar_stream(
                    stream_llm,
                    self.hablante,
                )
            )

        else:

            stream_salida = (
                stream_llm
            )

        for fragmento in stream_salida:

            respuesta_completa += (
                fragmento
            )

            yield fragmento

        respuesta_completa = (
            respuesta_completa.strip()
        )

        # =====================================================
        # 3. HISTORIAL
        # =====================================================

        self.historial.agregar_usuario(
            mensaje_usuario
        )

        self.historial.agregar_asistente(
            respuesta_completa
        )

        # =====================================================
        # 4. MEMORIA
        # =====================================================

        try:

            experiencia = Experiencia(
                contenido=mensaje_usuario,
                fuente="usuario",
                importancia=0.5,
                confianza=0.85,
                contexto="conversacion",
            )

            self.hipocampo.procesar(
                experiencia
            )

        except Exception as error:

            print(
                "[ATENAS][MEMORIA] "
                "No fue posible procesar "
                f"la memoria: {error}"
            )

        # =====================================================
        # 5. AUTONOMÍA
        # =====================================================

        self.ultima_accion_agente = None

        # ATENAS solamente ejecuta automáticamente
        # necesidades detectadas en ESTE turno.
        if not pendientes_del_turno:
            return

        resultados_agente = []

        for pendiente in pendientes_del_turno:

            try:

                resultado_agente = (
                    self.agente.actuar(
                        pendiente_id=(
                            pendiente.id
                        )
                    )
                )

                resultados_agente.append(
                    resultado_agente
                )

                if resultado_agente.get(
                    "actuo"
                ):

                    if resultado_agente.get(
                        "exito"
                    ):

                        print(
                            "\n[ATENAS][AGENTE] "
                            "Acción autónoma completada."
                        )

                        plan = resultado_agente.get(
                            "plan"
                        )

                        resultados = resultado_agente.get(
                            "resultados",
                            []
                        )

                        if plan is not None:

                            print(
                                "[ATENAS][AGENTE] "
                                f"Objetivo: {plan.descripcion}"
                            )

                            for numero, paso in enumerate(
                                plan.pasos,
                                start=1,
                            ):

                                print(
                                    "[ATENAS][AGENTE] "
                                    f"Paso {numero}: "
                                    f"{paso.herramienta}"
                                )

                                if paso.argumentos:

                                    print(
                                        "[ATENAS][AGENTE] "
                                        f"Argumentos: "
                                        f"{paso.argumentos}"
                                    )

                        for numero, resultado in enumerate(
                            resultados,
                            start=1,
                        ):

                            print(
                                "[ATENAS][AGENTE] "
                                f"Resultado {numero}: "
                                f"{resultado}"
                            )

                    else:

                        print(
                            "\n[ATENAS][AGENTE] "
                            "La acción autónoma falló."
                        )
                elif (
                    resultado_agente.get(
                        "requiere_confirmacion"
                    )
                ):

                    print(
                        "\n[ATENAS][AGENTE] "
                        "Hay una acción pendiente "
                        "de confirmación."
                    )

            except Exception as error:

                print(
                    "\n[ATENAS][AGENTE] "
                    f"Error: {error}"
                )

        self.ultima_accion_agente = (
            resultados_agente
        )
    # =========================================================
    # RESPUESTA NORMAL
    # =========================================================

    def responder(
        self,
        mensaje_usuario: str,
        usar_voz: bool = True,
    ) -> str:

        return "".join(
            self.responder_stream(
                mensaje_usuario,
                usar_voz=usar_voz,
            )
        )

    # =========================================================
    # LIMPIAR
    # =========================================================

    def limpiar_conversacion(
        self,
    ) -> None:

        self.historial.limpiar()

    # =========================================================
    # VOZ DIRECTA
    # =========================================================

    def decir(
        self,
        texto: str,
    ) -> bool:

        if not texto:
            return False

        if not self.hablante.disponible:
            return False

        return self.hablante.decir(
            texto
        )

    # =========================================================
    # CERRAR
    # =========================================================

    def cerrar(
        self,
    ) -> None:

        if self.hablante is not None:

            self.hablante.esperar()
            self.hablante.cerrar()

    # =========================================================
    # INVESTIGAR SI ES NECESARIO
    # =========================================================
    def _investigar_si_es_necesario(
        self,
        consulta: str,
    ) -> dict | None:
        """
        Evalúa si ATENAS tiene suficiente conocimiento local.

        Si no lo tiene, realiza una búsqueda web y sintetiza
        la información encontrada.
        """

        consulta = consulta.strip()

        if not consulta:
            return None

        try:

            evaluacion = (
                self.investigador
                .evaluar_consulta(
                    consulta
                )
            )

        except Exception as error:

            print(
                "[ATENAS][INVESTIGACION] "
                "No fue posible evaluar "
                f"la consulta: {error}"
            )

            return None

        if not evaluacion.get(
            "necesita_investigar",
            False,
        ):
            return None

        print(
            "\n[ATENAS][INVESTIGACION] "
            "Información local insuficiente."
        )

        print(
            "[ATENAS][INVESTIGACION] "
            "Buscando información..."
        )

        try:

            resultado = (
                self.investigador.investigar(
                    consulta=consulta,
                    limite=5,
                )
            )

        except Exception as error:

            print(
                "[ATENAS][INVESTIGACION] "
                f"Error buscando información: {error}"
            )

            return None

        resultados_web = resultado.get(
            "resultados",
            [],
        )

        if not resultados_web:

            print(
                "[ATENAS][INVESTIGACION] "
                "No se encontraron resultados útiles."
            )

            return None

        try:

            sintesis = (
                self.sintetizador_investigacion
                .sintetizar(
                    consulta=consulta,
                    resultados=resultados_web,
                )
            )

        except Exception as error:

            print(
                "[ATENAS][INVESTIGACION] "
                f"No fue posible sintetizar: {error}"
            )

            return None

        if not sintesis:
            return None

        # =====================================================
        # APRENDER LO INVESTIGADO
        # =====================================================

        resultado_aprendizaje = None

        try:

            resultado_aprendizaje = (
                self.consolidador_investigacion
                .consolidar(
                    consulta=consulta,
                    sintesis=sintesis,
                    fuentes=resultados_web,
                    confianza=0.80,
                )
            )

            if resultado_aprendizaje.get(
                "guardada"
            ):

                print(
                    "[ATENAS][APRENDIZAJE] "
                    "La investigación fue incorporada "
                    "a la memoria."
                )

        except Exception as error:

            print(
                "[ATENAS][APRENDIZAJE] "
                "No fue posible consolidar "
                f"la investigación: {error}"
            )

        resultado_final = {
            "consulta": consulta,
            "evaluacion": evaluacion,
            "fuentes": resultados_web,
            "sintesis": sintesis,
            "aprendizaje": resultado_aprendizaje,
        }

        self.ultima_investigacion = (
            resultado_final
        )

        print(
            "[ATENAS][INVESTIGACION] "
            f"Investigación completada "
            f"({len(resultados_web)} fuentes)."
        )

        return resultado_final

    # =========================================================
    # PROPIEDADES
    # =========================================================

    @property
    def modelo(
        self,
    ) -> str:

        return settings.llm.modelo

    @property
    def voz_disponible(
        self,
    ) -> bool:

        return self.hablante.disponible

    @property
    def motor_voz(
        self,
    ) -> str:

        return self.hablante.backend