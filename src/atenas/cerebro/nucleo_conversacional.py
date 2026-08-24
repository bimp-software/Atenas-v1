from __future__ import annotations

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

from src.atenas.cerebro.desarrollo import (
    SistemaDesarrolloAtenas,
    SupervisorErrores,
    MotorAutorreparacion,
    GestorCicloVidaAtenas,
)

from src.atenas.cerebro.identidad import (
    autoconcepto_atenas,
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

        autoconcepto_atenas.registrar_componente(
            "llm",
            True,
        )

        # =====================================================
        # STORAGE ÚNICO
        # =====================================================

        self.storage = (
            StorageManager()
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
                storage=(
                    self.storage
                ),
            )
        )

        estado_atenas.capacidades.memoria_persistente = (
            True
        )

        autoconcepto_atenas.registrar_componente(
            "memoria",
            True,
        )

        autoconcepto_atenas.registrar_componente(
            "vector_store",
            True,
        )

        autoconcepto_atenas.registrar_componente(
            "knowledge_graph",
            True,
        )

        # =====================================================
        # VOZ
        # =====================================================

        self.hablante = Hablante()

        estado_atenas.capacidades.voz_salida = (
            self.hablante.disponible
        )

        autoconcepto_atenas.registrar_componente(
            "voz_salida",
            self.hablante.disponible,
        )

        try:

            self.escucha = EscuchaVoz()

            estado_atenas.capacidades.voz_entrada = (
                True
            )

            autoconcepto_atenas.registrar_componente(
                "voz_entrada",
                True,
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

            autoconcepto_atenas.registrar_componente(
                "voz_entrada",
                False,
            )

        # =====================================================
        # AGENTE
        # =====================================================

        self.agente = (
            AgenteAtenas(
                storage=self.storage,
                llm=self.llm,
            )
        )

        self.ultima_accion_agente = None

        autoconcepto_atenas.registrar_componente(
            "agente",
            True,
        )

        autoconcepto_atenas.registrar_componente(
            "herramientas",
            True,
        )

        # =====================================================
        # INVESTIGACIÓN
        # =====================================================

        self.investigador = (
            Investigador(
                storage=self.storage
            )
        )

        self.sintetizador_investigacion = (
            SintetizadorInvestigacion(
                llm=self.llm
            )
        )

        self.consolidador_investigacion = (
            ConsolidadorInvestigacion(
                storage=self.storage,
                hipocampo=self.hipocampo,
            )
        )

        self.ultima_investigacion = None

        self.clasificador_consulta = (
            ClasificadorConsulta()
        )

        autoconcepto_atenas.registrar_componente(
            "investigacion",
            True,
        )

        autoconcepto_atenas.registrar_componente(
            "internet",
            True,
        )

        # =====================================================
        # DESARROLLO INTERNO
        # =====================================================

        try:

            self.desarrollo = (
                SistemaDesarrolloAtenas(
                    llm=self.llm,
                    raiz_proyecto=".",
                )
            )

            

            autoconcepto_atenas.registrar_componente(
                "autoprogramacion",
                True,
            )

            autoconcepto_atenas.registrar_componente(
                "autorreparacion",
                True,
            )

        except Exception as error:

            self.desarrollo = None

            autoconcepto_atenas.registrar_componente(
                "autoprogramacion",
                False,
            )

            autoconcepto_atenas.registrar_componente(
                "autorreparacion",
                False,
            )

            print(
                "[ATENAS][DESARROLLO] "
                f"No disponible: {error}"
            )

        # =====================================================
        # MOTOR DE AUTORREPARACIÓN
        # =====================================================

        self.motor_autorreparacion = (
            MotorAutorreparacion(
                desarrollo=self.desarrollo,
                max_intentos_por_error=2,
                cooldown_segundos=60.0,
                autoaplicar_bajo_riesgo=True,
            )
        )

        # =====================================================
        # SUPERVISOR DE ERRORES
        # =====================================================

        self.supervisor_errores = (
            SupervisorErrores(
                desarrollo=self.desarrollo,
                motor=self.motor_autorreparacion,
                reparar_automaticamente=True,
            )
        )

        if self.desarrollo is not None:

            try:

                (
                    self.desarrollo
                    .conectar_supervisor_desarrollo(
                        self.supervisor_errores
                    )
                )

            except Exception as error:

                print(
                    "[ATENAS][DESARROLLO] "
                    "No fue posible conectar "
                    f"SupervisorErrores: {error}"
                )

        autoconcepto_atenas.registrar_componente(
            "automejora",
            self.desarrollo is not None,
        )

        # =====================================================
        # CICLO DE VIDA
        # =====================================================

        self.ciclo_vida = (
            GestorCicloVidaAtenas(
                desarrollo=self.desarrollo,
                revisar_cada_turnos=20,
            )
        )

        self.ultima_revision_automejora = None

        # =====================================================
        # CAPACIDADES FUTURAS
        # =====================================================

        autoconcepto_atenas.registrar_componente(
            "vision",
            False,
        )

        autoconcepto_atenas.registrar_componente(
            "robot",
            False,
        )

        autoconcepto_atenas.registrar_componente(
            "servidor_local",
            False,
        )

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
    # DETECTAR CONSULTA SOBRE AUTOMEJORA
    # =========================================================

    @staticmethod
    def _consulta_sobre_automejora(
        mensaje: str,
    ) -> bool:
        """
        Decide si la consulta necesita un análisis real del
        código de ATENAS antes de responder.

        El análisis no se ejecuta en todos los turnos porque
        recorrer el proyecto completo sería innecesario.
        """

        texto = " ".join(
            (
                mensaje
                or ""
            )
            .lower()
            .strip()
            .split()
        )

        if not texto:
            return False

        indicadores = (
            "qué partes de tu código",
            "que partes de tu codigo",
            "qué mejorarías de tu código",
            "que mejorarias de tu codigo",
            "qué deberías mejorar",
            "que deberias mejorar",
            "analiza tu código",
            "analiza tu codigo",
            "revisa tu código",
            "revisa tu codigo",
            "automejora",
            "auto mejora",
            "mejoras de tu código",
            "mejoras de tu codigo",
            "problemas de tu código",
            "problemas de tu codigo",
            "calidad de tu código",
            "calidad de tu codigo",
            "refactorizar tu código",
            "refactorizar tu codigo",
        )

        return any(
            indicador in texto
            for indicador in indicadores
        )

    # =========================================================
    # CREAR CONTEXTO
    # =========================================================

    def _crear_mensajes(
        self,
        mensaje_usuario: str,
        contexto_internet: str | None = None,
    ) -> list[dict[str, str]]:

        mensaje_usuario = (
            mensaje_usuario
            or ""
        ).strip()

        # =====================================================
        # CLASIFICAR CONSULTA
        # =====================================================

        clasificacion_consulta = (
            self.clasificador_consulta
            .clasificar(
                mensaje_usuario
            )
        )

        # =====================================================
        # MEMORIA
        # =====================================================

        memoria_contexto = ""

        # Conversación, identidad y capacidades se resuelven
        # desde el prompt, estado y conversación reciente.
        # No necesitamos inyectar recuerdos semánticos.

        if (
            clasificacion_consulta.tipo
            not in {
                "conversacion",
                "identidad",
                "capacidad",
            }
        ):

            try:

                memoria_contexto = (
                    self.recuperador_memoria
                    .contexto_para_llm(
                        mensaje_usuario
                    )
                )

            except Exception as error:

                self._registrar_error_interno(
                    error=error,
                    componente="memoria",
                    funcion=(
                        "recuperador_memoria."
                        "contexto_para_llm"
                    ),
                )

                memoria_contexto = ""

        # =====================================================
        # SYSTEM PROMPT
        # =====================================================

        system_prompt = (
            construir_system_prompt()
        )

        # =====================================================
        # SISTEMA DE DESARROLLO
        # =====================================================

        if self.desarrollo is not None:

            try:

                contexto_desarrollo = (
                    self.desarrollo
                    .contexto_para_llm()
                )

                if contexto_desarrollo:

                    system_prompt += (
                        "\n\n"
                        + contexto_desarrollo
                    )

            except Exception as error:

                self._registrar_error_interno(
                    error=error,
                    componente="desarrollo",
                    funcion="desarrollo.contexto_para_llm",
                )

        # =====================================================
        # AUTOMEJORA REAL DEL PROYECTO
        # =====================================================

        if (
            self.desarrollo is not None
            and self._consulta_sobre_automejora(
                mensaje_usuario
            )
        ):

            try:

                informe_mejoras = (
                    self.desarrollo
                    .analizar_mejoras()
                )

                contexto_mejoras = (
                    self.desarrollo
                    .contexto_mejoras_para_llm(
                        limite=15,
                        ejecutar_si_falta=False,
                    )
                )

                if contexto_mejoras:

                    system_prompt += (
                        "\n\n"
                        + contexto_mejoras
                    )

                print(
                    "[ATENAS][AUTOMEJORA] "
                    f"Analizados "
                    f"{informe_mejoras.total_archivos} "
                    "archivos; "
                    f"{len(informe_mejoras.hallazgos)} "
                    "hallazgos."
                )

            except Exception as error:

                self._registrar_error_interno(
                    error=error,
                    componente="automejora",
                    funcion="desarrollo.analizar_mejoras",
                )

        if (self.supervisor_errores is not None):
            try:

                contexto_errores = (
                    self.supervisor_errores
                    .contexto_para_llm()
                )

                if contexto_errores:

                    system_prompt += (
                        "\n\n"
                        + contexto_errores
                    )

            except Exception as error:

                print(
                    "[ATENAS][SUPERVISOR][CONTEXTO] "
                    f"{error}"
                )

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

        mensajes.append(
            {
                "role": "user",
                "content": mensaje_usuario,
            }
        )

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
            mensaje_usuario
            or ""
        ).strip()

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

            self._registrar_error_interno(
                error=error,
                componente="agente",
                funcion="agente.observar",
            )

        # =====================================================
        # 2. INVESTIGACIÓN
        # =====================================================

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
        # 3. RESPUESTA CONVERSACIONAL
        # =====================================================

        mensajes = (
            self._crear_mensajes(
                mensaje_usuario,
                contexto_internet=(
                    contexto_internet
                ),
            )
        )

        respuesta_completa = ""

        try:

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

        except Exception as error:

            self._registrar_error_interno(
                error=error,
                componente="llm",
                funcion="llm.chat_stream",
            )

            return

        respuesta_completa = (
            respuesta_completa.strip()
        )

        # =====================================================
        # 4. HISTORIAL
        # =====================================================

        try:

            self.historial.agregar_usuario(
                mensaje_usuario
            )

            self.historial.agregar_asistente(
                respuesta_completa
            )

        except Exception as error:

            self._registrar_error_interno(
                error=error,
                componente="historial",
                funcion="historial.agregar",
            )

        # =====================================================
        # 5. MEMORIA
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

            self._registrar_error_interno(
                error=error,
                componente="memoria",
                funcion="hipocampo.procesar",
            )

        # =====================================================
        # 6. AUTONOMÍA
        # =====================================================

        self.ultima_accion_agente = None

        # ATENAS solamente ejecuta automáticamente
        # necesidades detectadas en ESTE turno.

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

                        plan = (
                            resultado_agente.get(
                                "plan"
                            )
                        )

                        resultados = (
                            resultado_agente.get(
                                "resultados",
                                [],
                            )
                        )

                        if plan is not None:

                            print(
                                "[ATENAS][AGENTE] "
                                f"Objetivo: "
                                f"{plan.descripcion}"
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
                                        "Argumentos: "
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

                elif resultado_agente.get(
                    "requiere_confirmacion"
                ):

                    print(
                        "\n[ATENAS][AGENTE] "
                        "Hay una acción pendiente "
                        "de confirmación."
                    )

            except Exception as error:

                self._registrar_error_interno(
                    error=error,
                    componente="agente",
                    funcion="agente.actuar",
                )

        self.ultima_accion_agente = (
            resultados_agente
        )

        # =====================================================
        # 7. CICLO DE VIDA / INICIATIVA DE AUTOMEJORA
        # =====================================================

        self._procesar_ciclo_desarrollo()

    # =========================================================
    # CICLO AUTÓNOMO GENERAL DE DESARROLLO
    # =========================================================

    def _procesar_ciclo_desarrollo(
        self,
    ):
        """
        Registra el turno y permite que ATENAS decida si existe
        trabajo interno de ingeniería que convenga realizar.

        Puede reparar, revalidar, preparar tests, organizar
        código, preparar soluciones sencillas o no hacer nada.

        Por defecto NO aplica cambios reales automáticamente.
        """

        if self.desarrollo is None:
            return None

        try:

            (
                self.desarrollo
                .registrar_turno_desarrollo()
            )

            resultado = (
                self.desarrollo
                .procesar_ciclo_desarrollo(
                    permitir_aplicacion=False
                )
            )

            if not resultado.revisado:
                return resultado

            print(
                "\n[ATENAS][DESARROLLO_AUTONOMO] "
                f"{resultado.motivo}"
            )

            director = (
                resultado.resultado_director
            )

            if director is not None:

                iniciativa = (
                    director.iniciativa
                )

                print(
                    "[ATENAS][DESARROLLO_AUTONOMO] "
                    f"Iniciativa: "
                    f"{iniciativa.tipo.value}"
                )

                print(
                    "[ATENAS][DESARROLLO_AUTONOMO] "
                    f"Prioridad: "
                    f"{iniciativa.prioridad:.2f}"
                )

                print(
                    "[ATENAS][DESARROLLO_AUTONOMO] "
                    f"Confianza: "
                    f"{iniciativa.confianza:.2f}"
                )

            return resultado

        except Exception as error:

            self._registrar_error_interno(
                error=error,
                componente="desarrollo_autonomo",
                funcion=(
                    "desarrollo."
                    "procesar_ciclo_desarrollo"
                ),
            )

            return None

    # =========================================================
    # CICLO DE VIDA ANTERIOR
    # =========================================================

    def _procesar_ciclo_vida(
        self,
    ):
        """
        Registra un turno conversacional completo y, cuando
        corresponde, permite que ATENAS consulte su iniciativa
        de automejora.

        La revisión automática NO permite aplicar cambios al
        proyecto real. Solo puede analizar y preparar propuestas.
        """

        ciclo_vida = getattr(
            self,
            "ciclo_vida",
            None,
        )

        if ciclo_vida is None:
            return None

        try:

            ciclo_vida.registrar_turno()

            if not ciclo_vida.debe_revisar():
                return None

            print(
                "\n[ATENAS][CICLO_VIDA] "
                "Corresponde revisar oportunidades "
                "de automejora."
            )

            resultado = (
                ciclo_vida
                .revisar_si_corresponde()
            )

            self.ultima_revision_automejora = (
                resultado
            )

            if resultado is None:
                return None

            decision = getattr(
                resultado,
                "decision",
                None,
            )

            if decision is not None:

                print(
                    "[ATENAS][AUTOMEJORA] "
                    f"Ejecutar: "
                    f"{decision.ejecutar}"
                )

                print(
                    "[ATENAS][AUTOMEJORA] "
                    f"Motivo: "
                    f"{decision.motivo}"
                )

            ciclo = getattr(
                resultado,
                "ciclo",
                None,
            )

            if ciclo is not None:

                print(
                    "[ATENAS][AUTOMEJORA] "
                    f"Estado: {ciclo.estado}"
                )

                # El ciclo de vida siempre llama con
                # permitir_aplicacion=False.
                if getattr(
                    ciclo,
                    "aplicada",
                    False,
                ):

                    print(
                        "[ATENAS][AUTOMEJORA][ADVERTENCIA] "
                        "Una revisión de ciclo de vida informó "
                        "una aplicación inesperada."
                    )

            return resultado

        except Exception as error:

            # El ciclo de vida no debe interrumpir una
            # conversación normal.
            self._registrar_error_interno(
                error=error,
                componente="ciclo_vida",
                funcion="ciclo_vida.revisar_si_corresponde",
            )

            return None

    # =========================================================
    # ESTADO DEL CICLO DE VIDA
    # =========================================================

    def estado_ciclo_vida(
        self,
    ) -> dict:

        ciclo_vida = getattr(
            self,
            "ciclo_vida",
            None,
        )

        if ciclo_vida is None:

            return {
                "disponible": False,
            }

        estado = ciclo_vida.estado

        return {
            "disponible": True,
            "revisar_cada_turnos": (
                ciclo_vida.revisar_cada_turnos
            ),
            "turnos_desde_revision": (
                estado.turnos_desde_revision
            ),
            "total_revisiones": (
                estado.total_revisiones
            ),
            "ultima_revision": (
                estado.ultima_revision
            ),
        }

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

        texto = (
            texto
            or ""
        ).strip()

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

            try:

                self.hablante.esperar()
                self.hablante.cerrar()

            except Exception as error:

                self._registrar_error_interno(
                    error=error,
                    componente="voz",
                    funcion="hablante.cerrar",
                )

    # =========================================================
    # REGISTRAR ERROR INTERNO
    # =========================================================

    def _registrar_error_interno(
        self,
        error: BaseException,
        componente: str,
        funcion: str,
        tests: list[str] | None = None,
    ):
        """
        Registra un error interno, lo diagnostica y permite
        al MotorAutorreparacion decidir si debe intentar
        una corrección.

        Este método es el último nivel de captura. Si el
        supervisor o el motor fallan, solo se informa por
        consola para evitar recursión infinita.
        """

        supervisor = getattr(
            self,
            "supervisor_errores",
            None,
        )

        if supervisor is None:

            print(
                f"[ATENAS][{componente.upper()}] "
                f"{type(error).__name__}: {error}"
            )

            return None

        # =====================================================
        # EVENTO + DIAGNÓSTICO
        # =====================================================

        try:

            evento = (
                supervisor
                .crear_evento(
                    error=error,
                    modulo=(
                        "src.atenas.cerebro."
                        "nucleo_conversacional"
                    ),
                    funcion=funcion,
                    componente=componente,
                    diagnosticar=True,
                )
            )

            supervisor.mostrar_evento(
                evento
            )

        except Exception as error_supervisor:

            print(
                "[ATENAS][SUPERVISOR] "
                "No fue posible registrar un error interno: "
                f"{type(error_supervisor).__name__}: "
                f"{error_supervisor}"
            )

            print(
                f"[ATENAS][{componente.upper()}] "
                f"{type(error).__name__}: {error}"
            )

            return None

        # =====================================================
        # MOTOR DE AUTORREPARACIÓN
        # =====================================================

        motor = getattr(
            self,
            "motor_autorreparacion",
            None,
        )

        if motor is None:
            return evento

        try:

            decision = (
                motor.evaluar(
                    evento
                )
            )

            print(
                "[ATENAS][AUTORREPARACION] "
                f"Intentar: {decision.intentar}"
            )

            print(
                "[ATENAS][AUTORREPARACION] "
                f"Motivo: {decision.motivo}"
            )

            if not decision.intentar:
                return evento

            print(
                "[ATENAS][AUTORREPARACION] "
                "Iniciando análisis automático..."
            )

            resultado_motor = (
                motor.procesar(
                    evento=evento,
                    tests=tests,
                )
            )

            if resultado_motor.error:

                print(
                    "[ATENAS][AUTORREPARACION] "
                    "Error del motor: "
                    f"{resultado_motor.error}"
                )

                return evento

            reparacion = (
                resultado_motor
                .resultado_reparacion
            )

            if reparacion is None:
                return evento

            if isinstance(
                reparacion,
                dict,
            ):

                estado = (
                    reparacion.get(
                        "estado"
                    )
                )

                aplicado = bool(
                    reparacion.get(
                        "aplicado",
                        False,
                    )
                )

                requiere_confirmacion = bool(
                    reparacion.get(
                        "requiere_confirmacion",
                        False,
                    )
                )

            else:

                estado = getattr(
                    reparacion,
                    "estado",
                    None,
                )

                aplicado = bool(
                    getattr(
                        reparacion,
                        "aplicado",
                        False,
                    )
                )

                requiere_confirmacion = bool(
                    getattr(
                        reparacion,
                        "requiere_confirmacion",
                        False,
                    )
                )

            print(
                "[ATENAS][AUTORREPARACION] "
                f"Estado: {estado}"
            )

            if aplicado:

                print(
                    "[ATENAS][AUTORREPARACION] "
                    "La corrección fue aplicada "
                    "y validada."
                )

            elif requiere_confirmacion:

                print(
                    "[ATENAS][AUTORREPARACION] "
                    "Existe una corrección válida, "
                    "pero requiere aprobación."
                )

            else:

                print(
                    "[ATENAS][AUTORREPARACION] "
                    "La reparación no fue aplicada."
                )

        except Exception as error_motor:

            # No reenviar este fallo al supervisor:
            # podría causar una recursión infinita.
            print(
                "[ATENAS][AUTORREPARACION][INTERNO] "
                f"{type(error_motor).__name__}: "
                f"{error_motor}"
            )

        return evento

    # =========================================================
    # INVESTIGAR SI ES NECESARIO
    # =========================================================

    def _investigar_si_es_necesario(
        self,
        consulta: str,
    ) -> dict | None:
        """
        Evalúa si ATENAS tiene suficiente conocimiento local.

        Si no lo tiene, realiza una búsqueda web,
        sintetiza la información y puede incorporarla
        posteriormente a la memoria.
        """

        consulta = (
            consulta
            or ""
        ).strip()

        if not consulta:
            return None

        # =====================================================
        # EVALUAR
        # =====================================================

        try:

            evaluacion = (
                self.investigador
                .evaluar_consulta(
                    consulta
                )
            )

        except Exception as error:

            self._registrar_error_interno(
                error=error,
                componente="investigacion",
                funcion="investigador.evaluar_consulta",
            )

            return None

        # =====================================================
        # INTERNET BLOQUEADO PARA ESTE TIPO DE CONSULTA
        # =====================================================

        if (
            evaluacion.get(
                "internet_permitido"
            )
            is False
        ):

            return None

        # =====================================================
        # YA SABE SUFICIENTE
        # =====================================================

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

        # =====================================================
        # BUSCAR
        # =====================================================

        try:

            resultado = (
                self.investigador.investigar(
                    consulta=consulta,
                    limite=5,
                )
            )

        except Exception as error:

            self._registrar_error_interno(
                error=error,
                componente="investigacion",
                funcion="investigador.investigar",
            )

            return None

        if not resultado.get(
            "investigo",
            False,
        ):

            return None

        resultados_web = (
            resultado.get(
                "resultados",
                [],
            )
        )

        if not resultados_web:

            print(
                "[ATENAS][INVESTIGACION] "
                "No se encontraron resultados útiles."
            )

            return None

        # =====================================================
        # SINTETIZAR
        # =====================================================

        try:

            sintesis = (
                self.sintetizador_investigacion
                .sintetizar(
                    consulta=consulta,
                    resultados=resultados_web,
                )
            )

        except Exception as error:

            self._registrar_error_interno(
                error=error,
                componente="investigacion",
                funcion=(
                    "sintetizador_investigacion."
                    "sintetizar"
                ),
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

            if (
                resultado_aprendizaje
                and resultado_aprendizaje.get(
                    "guardada"
                )
            ):

                print(
                    "[ATENAS][APRENDIZAJE] "
                    "La investigación fue incorporada "
                    "a la memoria."
                )

        except Exception as error:

            self._registrar_error_interno(
                error=error,
                componente="aprendizaje",
                funcion=(
                    "consolidador_investigacion."
                    "consolidar"
                ),
            )

        # =====================================================
        # RESULTADO
        # =====================================================

        resultado_final = {
            "consulta": consulta,
            "evaluacion": evaluacion,
            "fuentes": resultados_web,
            "sintesis": sintesis,
            "aprendizaje": (
                resultado_aprendizaje
            ),
        }

        self.ultima_investigacion = (
            resultado_final
        )

        print(
            "[ATENAS][INVESTIGACION] "
            "Investigación completada "
            f"({len(resultados_web)} fuentes)."
        )

        return resultado_final

    # =========================================================
    # DESARROLLO
    # =========================================================

    def estado_desarrollo(
        self,
    ) -> dict:

        if self.desarrollo is None:

            return {
                "disponible": False,
            }

        try:

            estado = (
                self.desarrollo.estado()
            )

            return {
                "disponible":
                    estado.disponible,

                "inspector":
                    estado.inspector,

                "mapa_proyecto":
                    estado.mapa_proyecto,

                "diagnostico":
                    estado.diagnostico,

                "programador":
                    estado.programador,

                "sandbox":
                    estado.sandbox,

                "pruebas":
                    estado.pruebas,

                "verificador":
                    estado.verificador,

                "historial":
                    estado.historial,

                "rollback":
                    estado.rollback,

                "autorreparacion":
                    estado.autorreparacion,

                "automejora":
                    estado.automejora,

                "cambios_registrados":
                    estado.cambios_registrados,

                "hallazgos_automejora":
                    estado.hallazgos_automejora,
            }

        except Exception as error:

            return {
                "disponible": False,
                "error": str(error),
            }

    # =========================================================
    # DIAGNOSTICAR ERROR
    # =========================================================

    def diagnosticar_error(
        self,
        traceback_texto: str,
    ):

        if self.desarrollo is None:
            return None

        return (
            self.desarrollo
            .diagnosticar(
                traceback_texto
            )
        )

    # =========================================================
    # REPARAR ERROR
    # =========================================================

    def reparar_error(
        self,
        traceback_texto: str,
        tests: list[str] | None = None,
        aplicar_bajo_riesgo: bool = False,
    ):

        if self.desarrollo is None:

            return {
                "ok": False,
                "error": (
                    "sistema_desarrollo_no_disponible"
                ),
            }

        return (
            self.desarrollo
            .reparar_error(
                traceback_texto=(
                    traceback_texto
                ),
                tests=tests,
                aplicar_bajo_riesgo=(
                    aplicar_bajo_riesgo
                ),
            )
        )

    # =========================================================
    # AUTOMEJORA
    # =========================================================

    def analizar_mejoras(
        self,
        limite_archivos: int | None = None,
    ):
        """
        Analiza estáticamente el proyecto real de ATENAS.

        No modifica archivos.
        """

        if self.desarrollo is None:
            return None

        return (
            self.desarrollo
            .analizar_mejoras(
                limite_archivos=(
                    limite_archivos
                )
            )
        )

    def mejoras_prioritarias(
        self,
        limite: int = 10,
        severidad_minima: float = 0.50,
    ):

        if self.desarrollo is None:
            return []

        return (
            self.desarrollo
            .mejoras_prioritarias(
                limite=limite,
                severidad_minima=(
                    severidad_minima
                ),
            )
        )

    def contexto_mejoras(
        self,
        limite: int = 20,
    ) -> str:

        if self.desarrollo is None:

            return (
                "ANÁLISIS DE AUTOMEJORA DE ATENAS:\n"
                "- Sistema de desarrollo no disponible."
            )

        return (
            self.desarrollo
            .contexto_mejoras_para_llm(
                limite=limite,
                ejecutar_si_falta=True,
            )
        )

    # =========================================================
    # ÚLTIMOS CAMBIOS
    # =========================================================

    def ultimos_cambios(
        self,
        limite: int = 10,
    ) -> list[dict]:

        if self.desarrollo is None:
            return []

        return (
            self.desarrollo
            .ultimos_cambios(
                limite=limite
            )
        )

    # =========================================================
    # REVERTIR CAMBIO
    # =========================================================

    def revertir_cambio(
        self,
        cambio_id: str,
    ):

        if self.desarrollo is None:

            return {
                "ok": False,
                "error": (
                    "sistema_desarrollo_no_disponible"
                ),
            }

        return (
            self.desarrollo
            .revertir_cambio(
                cambio_id
            )
        )

    

    # =========================================================
    # ERRORES INTERNOS
    # =========================================================

    def ultimo_error(
        self,
    ):

        if self.supervisor_errores is None:
            return None

        return (
            self.supervisor_errores
            .ultimo()
        )

    def errores_recientes(
        self,
        limite: int = 10,
    ):

        if self.supervisor_errores is None:
            return []

        return (
            self.supervisor_errores
            .recientes(
                limite=limite
            )
        )

    def errores_reparables(
        self,
    ):

        if self.supervisor_errores is None:
            return []

        return (
            self.supervisor_errores
            .pendientes_reparacion()
        )

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