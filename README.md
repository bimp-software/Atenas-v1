# ATENAS

> Asistente inteligente local, modular y experimental orientado a conversación, memoria persistente, investigación, automatización, desarrollo autónomo de software y autorreparación.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Ollama](https://img.shields.io/badge/LLM-Ollama-black)
![Model](https://img.shields.io/badge/Modelo-qwen3%3A8b-purple)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-En%20desarrollo-orange)

---

## 🧠 ¿Qué es ATENAS?

**ATENAS** es un proyecto de asistente de inteligencia artificial local diseñado para evolucionar desde un chatbot tradicional hacia un sistema capaz de **recordar, investigar, razonar sobre su entorno, utilizar herramientas, desarrollar software, detectar errores y mejorar progresivamente su propio funcionamiento**.

El proyecto utiliza **Ollama** como motor local para modelos de lenguaje y actualmente está configurado para trabajar principalmente con:

```text
qwen3:8b
```

ATENAS está construido mediante una arquitectura modular. La conversación, memoria, identidad, investigación, voz, autonomía, desarrollo y autorreparación se encuentran separadas en distintos componentes, permitiendo que cada capacidad evolucione independientemente.

> [!IMPORTANT]
> ATENAS se encuentra actualmente en **desarrollo activo**. Algunas capacidades son experimentales y pueden cambiar significativamente entre versiones.

---

# 🎯 Objetivo

La meta de ATENAS no es ser únicamente una interfaz para un modelo de lenguaje.

El proyecto busca construir progresivamente un **agente inteligente persistente** capaz de:

* conversar de forma natural;
* ejecutarse principalmente de manera local;
* recordar conversaciones y experiencias;
* recuperar recuerdos por significado;
* almacenar conocimiento sobre personas y conceptos;
* investigar cuando desconoce una respuesta;
* interactuar con herramientas;
* comprender objetivos;
* planificar tareas;
* controlar aplicaciones y elementos del escritorio;
* analizar proyectos de software;
* diagnosticar errores;
* generar soluciones;
* modificar código de manera controlada;
* ejecutar pruebas;
* verificar resultados;
* revertir cambios fallidos;
* detectar oportunidades de mejora;
* evolucionar hacia visión artificial y robótica.

---

# ✨ Capacidades

## 💬 Núcleo conversacional

El centro de ATENAS es `NucleoConversacional`.

Este componente coordina los diferentes subsistemas antes de generar una respuesta.

Entre ellos:

* modelo de lenguaje;
* historial;
* memoria;
* identidad;
* contexto;
* investigación;
* voz;
* agente;
* desarrollo;
* supervisión;
* automejora;
* ciclo de vida.

Las respuestas pueden generarse mediante **streaming**, permitiendo mostrar el texto progresivamente mientras el modelo lo produce.

---

## 🤖 LLM local con Ollama

ATENAS utiliza **Ollama** como backend principal para ejecutar modelos de lenguaje localmente.

Configuración actual aproximada:

```python
modelo = "qwen3:8b"
temperatura = 0.6
contexto = 4096
max_tokens = 1024
max_turnos_historial = 10
pensar = False
```

Esto permite que una parte importante del procesamiento pueda realizarse en el computador donde se ejecuta ATENAS sin depender obligatoriamente de servicios externos.

---

# 🧠 Sistema de memoria

ATENAS posee diferentes mecanismos de persistencia y recuperación de información.

Actualmente la arquitectura contempla:

* memoria semántica;
* memoria episódica;
* memoria de personas;
* investigaciones almacenadas;
* memoria vectorial;
* grafo de conocimiento;
* consolidación de recuerdos;
* recuperación contextual.

## Memoria vectorial

La memoria vectorial permite encontrar recuerdos mediante **similitud semántica** y no solamente mediante coincidencia exacta de palabras.

El modelo de embeddings utilizado actualmente es:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

Esto permite, por ejemplo, relacionar:

```text
"Mi perro se llama Toby"
```

con una consulta futura como:

```text
"¿Cómo se llama mi mascota?"
```

aunque ambas frases sean diferentes.

La arquitectura utiliza almacenamiento local para metadatos y vectores.

---

# 🕸️ Grafo de conocimiento

ATENAS también cuenta con un sistema orientado a representar relaciones entre información.

Por ejemplo:

```text
Benjamín
   │
   ├── creó ──────► ATENAS
   │
   └── trabaja en ► BIMP Software
```

El objetivo futuro es permitir que ATENAS no solo recuerde datos individuales, sino que pueda relacionarlos y construir una representación más consistente del conocimiento adquirido.

---

# 👤 Identidad y autoconcepto

ATENAS posee módulos destinados a representar aspectos de su propia identidad.

Entre ellos:

```text
identidad/
├── identidad.py
├── personalidad.py
├── valores.py
└── autoconcepto.py
```

Este sistema permite separar conceptos como:

* identidad;
* personalidad;
* valores;
* capacidades;
* limitaciones;
* autoconcepto.

El propósito es que ATENAS pueda diferenciar entre capacidades realmente disponibles y capacidades futuras o todavía experimentales.

---

# 🔎 Investigación

ATENAS posee una arquitectura específica para investigación.

Entre los componentes existentes se encuentran:

```text
investigacion/
├── clasificador_consulta.py
├── consolidador.py
├── detector_desconocimiento.py
├── investigador.py
├── sintetizador.py
└── vigencia.py
```

El flujo esperado es aproximadamente:

```text
Consulta
   ↓
Clasificación
   ↓
¿ATENAS posee información suficiente?
   │
   ├── Sí ──► Responder
   │
   └── No
        ↓
    Investigar
        ↓
    Sintetizar
        ↓
    Consolidar
        ↓
    Generar respuesta
```

Esto busca evitar que el modelo dependa exclusivamente de su conocimiento interno.

---

# 🎙️ Voz

ATENAS incluye sistemas de entrada y salida mediante voz.

## Salida de voz

Puede utilizar:

* **SAPI5** en Windows;
* `pyttsx3` como alternativa.

La reproducción se procesa mediante una cola para reducir el bloqueo del sistema conversacional.

---

## Entrada de voz

Para reconocimiento de voz se utilizan componentes como:

* `sounddevice`;
* NumPy;
* `faster-whisper`.

El audio capturado desde el micrófono puede ser transcrito localmente mediante Whisper.

Desde la consola principal se puede utilizar:

```text
/voz
```

para comenzar una captura de audio.

---

# 🦾 Agente

ATENAS contiene una capa de agente encargada de transformar objetivos e instrucciones en acciones.

El proyecto posee componentes relacionados con:

* objetivos;
* decisiones;
* acciones;
* planificación;
* estado del mundo;
* autonomía;
* replanificación;
* ejecución;
* verificación.

La intención es evolucionar desde:

```text
Usuario → pregunta → respuesta
```

hacia:

```text
Usuario
   ↓
Objetivo
   ↓
ATENAS
   ↓
Planificación
   ↓
Acciones
   ↓
Verificación
   ↓
Resultado
```

---

# 🖥️ Automatización de escritorio

Dentro del sistema de agente existen módulos orientados al control del computador.

Entre las capacidades experimentales se encuentran:

* mouse;
* teclado;
* ventanas;
* capturas de pantalla;
* acciones GUI;
* percepción del escritorio;
* interpretación visual;
* planificación de tareas;
* verificación visual;
* recuperación del contexto;
* replanificación.

> [!WARNING]
> Las capacidades que controlan mouse, teclado, archivos o aplicaciones deben utilizarse con precaución durante el desarrollo.

---

# 💻 Sistema de desarrollo autónomo

Una de las áreas principales de ATENAS es su arquitectura orientada al **desarrollo de software asistido y autónomo**.

El sistema incluye componentes para distintas etapas.

## Análisis

* análisis de requisitos;
* inspección de proyectos;
* diagnóstico de código;
* mapa del proyecto;
* detección de errores;
* detección de oportunidades de mejora.

## Diseño

* diseño de arquitectura;
* diseño de base de datos;
* planificación de sistemas;
* planificación de proyectos.

## Implementación

* programación;
* generación de código;
* generación de artefactos;
* ejecución de planes;
* administración de tareas;
* generación de documentación.

## Validación

* ejecución de pruebas;
* verificación de cambios;
* supervisor de errores;
* validación de tareas.

## Recuperación

* historial de cambios;
* parches;
* sandbox;
* rollback;
* recuperación de entorno;
* gestión segura de dependencias.

---

# 🧬 Automejora

ATENAS contiene mecanismos experimentales destinados a analizar su propio proyecto y detectar posibles mejoras.

Un ciclo simplificado puede representarse así:

```text
┌───────────────────────┐
│ Analizar proyecto     │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Detectar oportunidad  │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Crear propuesta       │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Generar modificación  │
└───────────┬───────────┘
            ↓
┌───────────────────────┐
│ Ejecutar pruebas      │
└───────────┬───────────┘
            ↓
       ¿Funciona?
        /     \
      Sí       No
      ↓         ↓
   Aplicar   Rollback
```

La intención no es permitir modificaciones sin control, sino construir un sistema donde las mejoras puedan ser **propuestas, evaluadas, comprobadas y revertidas**.

---

# 🩺 Autorreparación

ATENAS incluye un motor específico de autorreparación de software.

Puede utilizar información como:

* excepciones;
* `tracebacks`;
* pruebas fallidas;
* archivos afectados;
* líneas involucradas;
* diagnóstico del código;
* contexto del proyecto;

para intentar determinar la causa de un problema y producir una corrección.

Ejemplo conceptual:

```text
AssertionError
      ↓
Supervisor
      ↓
Diagnóstico
      ↓
LLM / Qwen
      ↓
Propuesta de corrección
      ↓
Patch
      ↓
Pruebas
      ↓
┌───────────────┐
│ ¿Funcionó?    │
├───────┬───────┤
│ Sí    │ No    │
↓       ↓
Aplicar Rollback
```

El repositorio posee además pruebas específicas para procesos de autorreparación y reparación mediante Qwen.

---

# 🏗️ Arquitectura

Una representación simplificada de la estructura actual es:

```text
Atenas-v1/
│
├── main.py
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
│
├── assets/
├── templates/
├── tests/
│
└── src/
    ├── config/
    │   └── settings.py
    │
    └── atenas/
        │
        ├── cerebro/
        │   │
        │   ├── agente/
        │   ├── desarrollo/
        │   ├── estado/
        │   ├── identidad/
        │   ├── investigacion/
        │   ├── llm/
        │   ├── memoria/
        │   ├── voz/
        │   │
        │   ├── historial.py
        │   ├── nucleo_conversacional.py
        │   └── prompts.py
        │
        ├── herramientas/
        │   ├── internet/
        │   ├── mouse/
        │   ├── notas/
        │   ├── sistema/
        │   ├── teclado/
        │   └── executor.py
        │
        └── memoria/
            ├── database.py
            ├── episodic_store.py
            ├── investigacion_store.py
            ├── knowledge_graph.py
            ├── people_store.py
            ├── semantic_store.py
            ├── store_manager.py
            └── vector_store.py
```

---

# ⚙️ Requisitos

Se recomienda utilizar:

* Python **3.11+**;
* Git;
* Ollama;
* Windows 10/11 para aprovechar completamente SAPI5 y las funciones de escritorio;
* un modelo compatible instalado mediante Ollama.

Actualmente el modelo principal configurado es:

```text
qwen3:8b
```

Puedes instalarlo mediante:

```bash
ollama pull qwen3:8b
```

Comprueba los modelos disponibles con:

```bash
ollama list
```

---

# 📦 Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/bimp-software/Atenas-v1.git
cd Atenas-v1
```

---

## 2. Crear entorno virtual

### Windows

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Actualizar pip

```bash
python -m pip install --upgrade pip
```

---

## 4. Instalar dependencias

> [!NOTE]
> `requirements.txt` todavía se encuentra en construcción. Mientras no contenga todas las dependencias del proyecto, algunas deberán instalarse manualmente.

Entre las dependencias utilizadas actualmente se encuentran:

```bash
pip install ollama numpy sentence-transformers sounddevice faster-whisper pyttsx3 flask pytest
```

En Windows, para soporte SAPI5:

```bash
pip install pywin32
```

Algunos módulos experimentales de automatización pueden necesitar dependencias adicionales.

---

# 🚀 Ejecución

Primero asegúrate de que Ollama esté instalado y que `qwen3:8b` se encuentre disponible:

```bash
ollama pull qwen3:8b
```

Luego ejecuta:

```bash
python main.py
```

En Windows también puedes utilizar:

```powershell
py -3.11 main.py
```

---

# 💬 Uso

Al ejecutar el programa se inicia la interfaz principal de consola.

Los comandos disponibles incluyen:

```text
/voz
```

Inicia una captura desde el micrófono.

```text
/limpiar
```

Limpia el contexto conversacional.

```text
salir
```

Finaliza ATENAS.

También puedes escribir directamente:

```text
Tú: Hola ATENAS
```

y recibir la respuesta mediante streaming.

---

# 🌐 Interfaz web

El repositorio contiene además una aplicación Flask básica.

Puede iniciarse mediante:

```bash
python app.py
```

La interfaz web todavía se encuentra en evolución y su integración completa con el núcleo de ATENAS forma parte del desarrollo futuro del proyecto.

---

# 🧪 Pruebas

El proyecto contiene una batería amplia de pruebas para los diferentes subsistemas.

Puedes utilizar:

```bash
pytest
```

o:

```bash
python -m pytest
```

Para ejecutar una prueba específica:

```bash
python -m pytest tests/test_autorreparacion_qwen.py
```

Algunas pruebas pueden:

* comunicarse con Ollama;
* utilizar un modelo local;
* crear proyectos temporales;
* modificar archivos temporales;
* interactuar con componentes del sistema;
* necesitar dependencias opcionales.

Por este motivo se recomienda ejecutar inicialmente pruebas individuales durante el desarrollo.

---

# 🔒 Seguridad

ATENAS posee capacidades experimentales que pueden interactuar con:

* archivos;
* código fuente;
* dependencias;
* mouse;
* teclado;
* aplicaciones;
* proyectos de software;
* procesos del sistema.

La arquitectura incluye mecanismos destinados a reducir el riesgo:

* sandbox;
* validación;
* políticas de ejecución;
* confirmaciones;
* historial;
* verificación;
* rollback;
* recuperación;
* gestión segura de dependencias.

Sin embargo:

> [!CAUTION]
> ATENAS es software experimental. No se recomienda ejecutar módulos autónomos con permisos administrativos innecesarios ni utilizarlos sobre información crítica sin disponer de respaldos.

---

# 📊 Estado del proyecto

## Implementado / en desarrollo avanzado

* [x] Núcleo conversacional
* [x] Integración con Ollama
* [x] Qwen local
* [x] Streaming de respuestas
* [x] Historial conversacional
* [x] Memoria persistente
* [x] Memoria semántica
* [x] Memoria episódica
* [x] Memoria vectorial
* [x] Grafo de conocimiento
* [x] Registro de personas
* [x] Sistema de investigación
* [x] Identidad
* [x] Autoconcepto
* [x] Voz de salida
* [x] Reconocimiento de voz
* [x] Sistema de agente
* [x] Automatización de escritorio
* [x] Sistema de desarrollo
* [x] Diagnóstico de código
* [x] Generación y aplicación de parches
* [x] Ejecución de pruebas
* [x] Rollback
* [x] Automejora experimental
* [x] Autorreparación experimental
* [x] Ciclo de vida

---

## En evolución

* [ ] Robustecer la autonomía
* [ ] Mejorar percepción visual
* [ ] Aumentar seguridad de ejecución
* [ ] Completar gestión de dependencias
* [ ] Completar `requirements.txt`
* [ ] Consolidar interfaz web
* [ ] Mejorar observabilidad y logs
* [ ] Ampliar pruebas end-to-end
* [ ] Documentar APIs internas
* [ ] Mejorar recuperación de memoria
* [ ] Crear instalación reproducible

---

# 🔭 Visión futura

Entre las capacidades contempladas para futuras etapas se encuentran:

* [ ] Visión multimodal avanzada
* [ ] Integración con hardware
* [ ] Control robótico
* [ ] Planificación autónoma de largo plazo
* [ ] Aprendizaje continuo controlado
* [ ] Mayor comprensión del entorno
* [ ] Arquitectura distribuida de herramientas
* [ ] Interacción física mediante un robot

---

# 🕷️ ATENAS y robótica

La arquitectura de ATENAS está pensada para que el cerebro de software pueda evolucionar posteriormente hacia una implementación física.

Conceptualmente:

```text
                    ATENAS
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
     Memoria       Razonamiento     Visión
        │              │              │
        └──────────────┼──────────────┘
                       ↓
                     Agente
                       ↓
               Sistema de acciones
                       ↓
          ┌────────────┴────────────┐
          ↓                         ↓
     Computador                  Robot
```

De esta manera, el sistema de inteligencia y memoria puede mantenerse separado de la plataforma física que utilice ATENAS en el futuro.

---

# 💡 Filosofía

ATENAS está construido alrededor de una idea:

> **Un asistente útil no debería limitarse a generar texto. Debería poder recordar, comprender su entorno, utilizar herramientas, aprender de los errores y mejorar de manera verificable.**

Por esta razón el proyecto prioriza una arquitectura modular donde las capacidades puedan desarrollarse, probarse y mejorarse progresivamente.

---

# 🗺️ Roadmap

Algunos objetivos importantes para las próximas versiones:

1. completar y fijar dependencias;
2. completar `requirements.txt`;
3. agregar configuración robusta mediante `.env`;
4. separar configuraciones de desarrollo y producción;
5. crear perfiles de autonomía;
6. fortalecer permisos del agente;
7. mejorar sandbox y rollback;
8. aumentar cobertura de tests;
9. integrar completamente la interfaz web;
10. implementar métricas y trazabilidad;
11. mejorar la memoria semántica y vectorial;
12. optimizar los ciclos de automejora;
13. mejorar los mecanismos de autorreparación;
14. documentar APIs internas;
15. preparar integración con hardware y robótica.

---

# 🤝 Contribución

El proyecto se encuentra en evolución constante.

Para contribuir:

1. realiza un fork;
2. crea una rama:

```bash
git checkout -b feature/nueva-capacidad
```

3. desarrolla los cambios;
4. ejecuta las pruebas;
5. realiza un commit descriptivo;
6. abre un Pull Request.

Ejemplo:

```bash
git commit -m "feat: agregar nueva capacidad a ATENAS"
```

---

# 📜 Licencia

Este proyecto está distribuido bajo la licencia **MIT**.

Consulta:

```text
LICENSE
```

para más información.

---

# 👨‍💻 Autor

**Benjamín**
**BIMP Software**

Repositorio oficial:

```text
https://github.com/bimp-software/Atenas-v1
```

---

<p align="center">
  <strong>ATENAS</strong>
  <br><br>
  Inteligencia local · Memoria persistente · Autonomía progresiva
</p>
