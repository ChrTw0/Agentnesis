# Agentnesis - Sistema Multiagente Dinámico con Razonamiento Profundo

Un sistema multiagente que **genera expertos especializados bajo demanda** para resolver problemas complejos mediante razonamiento colaborativo.

## El Problema

Los sistemas LLM tradicionales tienen limitaciones fundamentales:

1.  **Sistemas de agente único** (ChatGPT, Claude) carecen de experiencia de dominio especializada.
2.  **Sistemas multiagente fijos** (AutoGen, CrewAI) utilizan agentes predefinidos que pueden no encajar con el problema.
3.  **Agentes ReAct simples** carecen de profundidad: no planifican, critican ni se automejoran.
4.  **Sin coordinación**: los agentes trabajan de forma aislada, creando resultados contradictorios.

## La Solución: Agentnesis

**Genesis**, el núcleo metacognitivo, analiza tu problema y **despliega dinámicamente el equipo exacto de especialistas que necesitas**. Cada especialista es un **DeepAgent** (Agente Profundo) con su propio ciclo de razonamiento (Planificar → Ejecutar → Criticar), no un simple bucle de llamada a herramientas.

Innovaciones clave:
-   **Generación dinámica**: Sin agentes codificados de forma fija — Genesis crea Desarrolladores Backend, Expertos Legales, Analistas de Investigación, etc., basándose en tu consulta.
-   **Razonamiento profundo**: Cada agente ejecuta ciclos de Planificar-Ejecutar-Criticar (arquitectura fractal).
-   **Validación colaborativa**: Las propuestas se validan contra un Grafo de Conocimiento (Knowledge Graph) compartido para prevenir contradicciones.
-   **Turnos orquestados**: Un Moderador gestiona quién habla y cuándo, evitando el caos y los bloqueos.

## Cómo Funciona

En lugar de usar un solo LLM o un conjunto fijo de agentes, Agentnesis:

1.  **Genesis analiza tu pregunta** para determinar qué experiencia se necesita.
2.  **Genera agentes especializados dinámicamente** (ej. Experto Legal, Desarrollador Backend, Analista de Investigación).
3.  **Cada agente ejecuta un bucle de razonamiento profundo**: Planificar → Ejecutar → Autocriticar (no es simple "tool-calling").
4.  **El Integrador valida las propuestas** buscando consistencia antes de agregarlas al grafo de conocimiento.
5.  **El Moderador orquesta los turnos** para prevenir el caos y detectar bloqueos (deadlocks).
6.  **El Sintetizador consolida** todo el trabajo aprobado en una respuesta final coherente.

## Características clave

-   **Creación Dinámica de Agentes**: Genesis genera agentes bajo demanda basados en el dominio del problema.
-   **Arquitectura Fractal**: Cada agente ejecuta su propio bucle Planificar-Ejecutar-Criticar (patrón DeepAgent).
-   **Grafo de Conocimiento**: La memoria compartida almacena decisiones validadas como entidades y relaciones.
-   **Resolución de Conflictos**: El Integrador valida las propuestas contra el KG para prevenir contradicciones.
-   **Gestión de Turnos**: El Moderador orquesta los turnos de los agentes y detecta bloqueos.
-   **Aislamiento de Estado**: Cada agente tiene su propia cadena LLM y conjunto de herramientas para prevenir contaminación cruzada.

## Arquitectura

```
                      Consulta Usuario
                           ↓
                    ┌──────────────┐
                    │   Genesis    │ ← Genera agentes dinámicamente
                    │ (Arranque)   │
                    └──────────────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        │         Bucle Colaborativo          │
        │   (Se repite hasta FIN o Bloqueo)   │
        └─────────────────────────────────────┘
                           ↓
           ┌───────────────────────────────┐
           │          Moderador            │
           │  - Decide siguiente orador    │
           │  - Monitorea el progreso      │
           └───────────────────────────────┘
                ↓              ↓           ↓
        ┌───────────┐   ┌──────────┐   ┌─────────┐
        │  Trabajo  │   │Integrador│   │ FINISH  │
        │  Agente   │   │(Validar) │   │    ↓    │
        └───────────┘   └──────────┘   │Sintetizar
             ↓                ↓         └─────────┘
    ┌────────────────┐        │
    │ Bucle Fractal: │        │
    │ Plan→Ejecutar  │        │
    │   →Criticar    │        │
    └────────────────┘        │
             ↓                ↓
      Área de Preparación ← Aprobado/Rechazado
             ↓
      Grafo de Conocimiento (Memoria Compartida)
```

**Flujo Clave:**
1. Genesis analiza consulta → genera N agentes.
2. **Bucle** (Moderador orquesta):
   - Turno del agente → Razonamiento fractal → Publicar propuesta
   - Integrador valida → Aprobar/Rechazar
   - Moderador decide siguiente acción
3. Cuando todos los agentes son aprobados → Sintetizador genera respuesta final.

## Limitaciones Actuales

**Herramientas:** Actualmente opera utilizando solo conocimiento y razonamiento del LLM. Herramientas externas (búsqueda web, análisis de PDF, ejecución de código) están planeadas para futuras versiones.

**Modelo Recomendado:** [DeepSeek V3.2](https://platform.deepseek.com/) vía [OpenRouter](https://openrouter.ai/)
-   **¿Por qué DeepSeek?** Arquitectura de atención dispersa → bajo costo (~$0.25/1M tokens de entrada).
-   **Rendimiento:** Top 30 en la clasificación de [LMArena](https://lmarena.ai/) (a febrero de 2026).
-   **Calidad:** Produce salidas con 95-98% de confianza en nuestras pruebas.

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/yourusername/Agentnesis.git
cd Agentnesis

# Crear entorno conda
conda create -n Agentnesis python=3.12 -y
conda activate Agentnesis

# Instalar dependencias
pip install -e .
```

## Configuración

Copia `.env.example` a `.env` y configura:

```bash
cp .env.example .env
```

Variables requeridas:
```env
# Clave API - soporta OpenAI u OpenRouter
OPENROUTER_API_KEY=tu_clave_api_aqui

# Selección de modelo (por agente)
GENESIS_MODEL=deepseek/deepseek-v3.2
MODERATOR_MODEL=deepseek/deepseek-v3.2
INTEGRATOR_MODEL=deepseek/deepseek-v3.2
SYNTHESIZER_MODEL=deepseek/deepseek-v3.2
WORKER_MODEL=deepseek/deepseek-v3.2

# Límites del sistema
GRAPH_RECURSION_LIMIT=75
MODERATOR_MAX_ITERATIONS=20
GENESIS_MAX_AGENTS=10
```

## Uso

```bash
python -m src.main "¿Por qué el océano es azul?"
```

## Estructura del Proyecto

```
Agentnesis/
├── src/
│   ├── config/              # Configuraciones y fábrica de LLM
│   ├── core/
│   │   ├── states/          # GlobalState, esquemas, reducers
│   │   └── main_graph.py    # Ensamblaje principal de LangGraph
│   ├── specialists/
│   │   ├── genesis/         # Análisis de dominio y generación dinámica
│   │   ├── moderator/       # Orquestación de turnos y detección de bloqueos
│   │   ├── integrator/      # Validación de propuestas vs KG
│   │   ├── synthesizer/     # Consolidación de salida final
│   │   ├── fractal_agent/   # Bucle Planificar-Ejecutar-Criticar
│   │   └── universal_worker/# Ejecución de agente polimórfico
│   ├── utils/               # Ayudantes (cargador de prompts, parser JSON, logger)
│   ├── tools/               # Herramientas externas (Fase 2 - ver tools/README.md)
│   └── services/            # Integraciones externas (Fase 3 - ver services/__init__.py)
├── tests/                   # Suite de pruebas (futuro - ver tests/README.md)
├── scripts/                 # Scripts de desarrollo
├── .env.example             # Plantilla de configuración
├── pyproject.toml           # Dependencias
└── README.md                # Este archivo
```

## Cómo funciona

### 1. Genesis analiza la consulta
```python
# Determina dominio y experiencia requerida
domain_analysis = genesis.analyze_domain(user_query)
# Resultado: "fisica-y-quimica" → genera PhysicsExpert, OpticsSpecialist
```

### 2. Cada agente ejecuta un ciclo fractal
```python
# Dentro del subgrafo del agente
plan = planner(task, context)   # "Necesito explicar absorción y dispersión"
execution = executor(plan)      # Genera propuesta con structured_data
critique = critic(execution)    # "La propuesta está completa y es precisa"
# → Publica en Área de Preparación
```

### 3. El Integrador valida propuestas
```python
# Verifica contra el Grafo de Conocimiento
if conflicts_with_kg(proposal):
    return {"status": "rejected", "feedback": "..."}
else:
    return {"status": "approved"}
```

### 4. El Moderador decide el siguiente orador
```python
# Considera: propuestas pendientes, estado del agente, dependencias, turnos recientes
next_speaker = moderator.decide_turn(state)
# Retorna: "OpticsSpecialist_001" o "INTEGRATOR" o "FINISH"
```

### 5. El Sintetizador consolida la respuesta final
```python
# Transforma el Grafo de Conocimiento en una respuesta coherente
final_output = synthesizer.synthesize(
    kg_entities=approved_entities,
    kg_relations=approved_relations,
    user_query=original_query
)
```


## Métricas (últimas 5 ejecuciones)

- Confianza promedio: 95-98%
- Llamadas LLM por ejecución: 15-22
- Agentes generados: 2-3
- Tasa de éxito: 100% (5/5)

## Hoja de Ruta (Roadmap)

**Fase 1 (Actual - MVP):** [OK]
- Generación dinámica de agentes
- Bucles de razonamiento fractal
- Integración de grafo de conocimiento
- Validación y orquestación

**Fase 2 (Siguiente - Exploración de Herramientas):**
- **Búsqueda Web**: Tavily/SerpAPI/DuckDuckGo (recuperación de información en tiempo real)
- **Análisis de PDF**: Ingesta y extracción de documentos
- **Web Scraping**: BeautifulSoup/Playwright para datos estructurados
- **Ejecución de Código**: Entornos aislados ("sandboxed") (bajo evaluación)
- **Vinculación Dinámica de Herramientas**: Herramientas asignadas por rol de agente al momento de la generación

**Fase 3 (Futuro):**
- Checkpointing persistente (PostgreSQL)
- Ejecución paralela de agentes
- Resolución avanzada de conflictos
- Humano en el bucle para decisiones críticas

## Licencia

Licencia Apache 2.0 - ver archivo [LICENSE](LICENSE) para más detalles

## Autor

**Christian Sosa** - [christian.sosa.r16@gmail.com](mailto:christian.sosa.r16@gmail.com)

## Contribución

Este es un proyecto de investigación de código abierto. Issues y PRs son bienvenidos.
