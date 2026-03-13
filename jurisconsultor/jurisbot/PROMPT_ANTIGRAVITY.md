# 🚀 PROMPT PARA ANTIGRAVITY
## Evolución de JurisBot: De Monolito a Arquitectura Multi-Agente

---

## 📋 CONTEXTO

**Proyecto:** JurisBot - Asistente Legal AI para Derecho Mexicano  
**Código Base:** https://github.com/ijmarquezl/JurisBot  
**Arquitectura Actual:** FastAPI monolítico + RAG (PostgreSQL/pgvector) + Multi-tenant  
**Arquitectura Objetivo:** Sistema multi-agente con 7 agentes especializados + 5 compuertas de calidad  
**Inspiración:** Jurídicon® de Carlos Valderrama (0% alucinaciones)

---

## 🎯 OBJETIVO PRINCIPAL

Evolucionar JurisBot desde su arquitectura monolítica actual hacia un **sistema multi-agente especializado** que garantice **0% de alucinaciones** mediante verificación cruzada y un "abogado del diablo" (agente adversarial).

**NO es un rewrite:** Se debe reutilizar la infraestructura base existente (Docker, PostgreSQL, multi-tenant, procesamiento de PDFs).

---

## 🏗️ ARQUITECTURA ACTUAL (Baseline)

```
JurisBot Actual:
├── Frontend: React App
├── Backend: FastAPI (monolítico)
├── Database: PostgreSQL + pgvector (RAG)
├── Storage: MongoDB (tenant data)
├── Multi-tenant: Script onboard_tenant.sh
├── Reverse Proxy: Nginx
└── Contenerización: Docker Compose
```

**Fortalezas a conservar:**
- ✅ Sistema multi-tenant con aislamiento de datos
- ✅ RAG funcional con PostgreSQL/pgvector
- ✅ Procesamiento de PDFs (legal_scraper.py)
- ✅ Docker Compose completo y funcional
- ✅ Script de onboarding automatizado

---

## 🏛️ ARQUITECTURA OBJETIVO (Multi-Agente)

```
JurisBot Evolucionado:
├── Frontend: React (existente, posibles mejoras)
├── Backend: FastAPI + Redis (nuevo: cola de tareas)
├── Database: PostgreSQL + pgvector (existente)
├── Vector DB: Pinecone o pgvector (existente)
├── Message Queue: Redis (NUEVO)
├── 
├── AGENTES (NUEVO - 7 especializados):
│   ├── 1. Orquestador (Router)
│   ├── 2. Normativo (Leyes y reglamentos)
│   ├── 3. Procedimental (Procesos y plazos)
│   ├── 4. Doctrina (Jurisprudencia y tesis)
│   ├── 5. Síntesis (Verificación y consolidación)
│   ├── 6. Adversarial (Devil's Advocate - CRÍTICO)
│   └── 7. Redacción (Formato profesional)
│
├── COMPUERTAS DE CALIDAD (NUEVO - 5 Gates):
│   ├── Gate 1: Verificación de fuentes primarias
│   ├── Gate 2: Coherencia argumentativa
│   ├── Gate 3: Validación de formato
│   ├── Gate 4: Checklist de requisitos
│   └── Gate 5: Aprobación final
│
└── Multi-tenant: Heredado del sistema actual
```

---

## 🤖 ESPECIFICACIÓN DE AGENTES

### **AGENTE 1: ORQUESTADOR** 🎭

**Rol:** Router y coordinador principal

**Responsabilidades:**
- Recibir consulta del usuario
- Analizar área del derecho (civil, mercantil, penal, laboral, etc.)
- Descomponer problema en subtareas
- Asignar agentes especializados apropiados
- Definir flujo de trabajo y dependencias
- Generar PLAN DE TRABAJO estructurado

**Input:** Consulta en lenguaje natural del usuario
**Output:** JSON con plan de trabajo:
```json
{
  "area_derecho": "civil|mercantil|penal|laboral|administrativo|fiscal",
  "tipo_consulta": "opinión_legal|procedimiento|redacción|investigación",
  "agentes_requeridos": ["normativo", "procedimental", "doctrinal"],
  "plan_trabajo": [
    {"paso": 1, "agente": "normativo", "tarea": "..."},
    {"paso": 2, "agente": "doctrinal", "tarea": "..."}
  ],
  "prioridad": "urgente|estándar|profunda",
  "entregable_esperado": "descripción"
}
```

**Modelo recomendado:** GPT-4o o Claude 3.5 Sonnet (razonamiento complejo)

---

### **AGENTE 2: NORMATIVO** 📚

**Rol:** Especialista en leyes, reglamentos y normativa oficial mexicana

**Responsabilidades:**
- Buscar normativa aplicable en base de conocimiento
- Verificar vigencia de leyes (¿derogadas? ¿reformadas?)
- Especificar jerarquía normativa
- Citar artículos específicos con formato correcto
- Usar SOLO fuentes primarias (DOF, Congreso, Poder Judicial)

**Fuentes válidas (jerarquía):**
1. Constitución Política de los Estados Unidos Mexicanos
2. Tratados internacionales
3. Leyes federales
4. Leyes estatales
5. Reglamentos
6. Normas oficiales mexicanas (NOM)

**Input:** Tarea específica del Orquestador + contexto de la consulta
**Output:** JSON con normas aplicables:
```json
{
  "normas_aplicables": [
    {
      "tipo": "constitucion|ley_federal|ley_estatal|reglamento",
      "nombre": "...",
      "articulos": ["..."],
      "vigencia": "vigente|derogada|reformada",
      "fecha_ultima_reforma": "...",
      "contenido_relevante": "..."
    }
  ],
  "jerarquia_normativa": "explicación",
  "conflictos_detectados": "...",
  "fuentes_primarias": ["urls_oficiales"]
}
```

**Integración con RAG existente:** Usar el sistema de embeddings actual (pgvector)

---

### **AGENTE 3: PROCEDIMENTAL** ⚖️

**Rol:** Especialista en procedimientos, plazos y requisitos procesales

**Responsabilidades:**
- Identificar vía procesal correcta
- Detallar requisitos de procedibilidad
- Especificar plazos (hábiles vs naturales)
- Indicar competencia (juzgado, tribunal)
- Mencionar costos aproximados
- Señalar riesgos de caducidad/prescripción

**Áreas de especialidad:**
- Juicios civiles (oral, ordinario, especial)
- Juicios mercantiles
- Amparo indirecto y directo
- Procedimientos administrativos
- Ejecución de garantías

**Output:** JSON con procedimiento:
```json
{
  "via_procesal": "...",
  "juzgado_competente": "...",
  "requisitos_procedibilidad": ["..."],
  "pasos_procesales": [
    {"orden": 1, "paso": "...", "plazo": "...", "costo": "..."}
  ],
  "plazos_criticos": ["..."],
  "riesgos": ["..."],
  "recursos_disponibles": ["..."]
}
```

---

### **AGENTE 4: DOCTRINA** 🔍

**Rol:** Especialista en tesis de jurisprudencia, tesis aisladas y doctrina

**Responsabilidades:**
- Buscar tesis de jurisprudencia relevantes
- Buscar tesis aisladas aplicables
- Buscar doctrina de autores reconocidos
- Priorizar tesis recientes (últimos 5 años)
- Identificar criterios contradictorios

**Fuentes:**
- SCJN (Suprema Corte)
- TFJA (Tribunal Federal)
- TEPJF (Tribunal Electoral)
- Doctrina: Fix-Zamudio, etc.

**Output:** JSON con jurisprudencia:
```json
{
  "tesis_jurisprudencia": [
    {
      "numero": "...",
      "tipo": "jurisprudencia|aislada",
      "instancia": "SCJN|TFJA|TEPJF",
      "fecha": "...",
      "materia": "...",
      "criterio": "...",
      "aplicabilidad": "..."
    }
  ],
  "doctrina_relevante": [...],
  "criterios_contrarios": ["..."],
  "tendencia_actual": "..."
}
```

---

### **AGENTE 5: SÍNTESIS** 🧪

**Rol:** Consolida hallazgos y detecta inconsistencias

**Responsabilidades:**
- Consolidar hallazgos de todos los agentes especializados
- Detectar contradicciones entre fuentes
- Verificar que citas sean correctas y completas
- Identificar gaps de información
- Marcar conflictos para revisión

**Verificaciones obligatorias:**
- □ Todas las citas tienen fuente primaria
- □ No hay contradicciones entre normas citadas
- □ La jurisprudencia está vigente
- □ Los plazos procesales son los vigentes
- □ La doctrina citada es de autor reconocido

**Output:** JSON con síntesis:
```json
{
  "sintesis_argumento": "...",
  "contradicciones_detectadas": ["..."],
  "verificaciones_pasadas": ["..."],
  "verificaciones_fallidas": ["..."],
  "informacion_faltante": ["..."],
  "recomendacion": "proceder|solicitar_revision|detener"
}
```

---

### **AGENTE 6: ADVERSARIAL** 😈 (CRÍTICO)

**Rol:** Abogado del diablo - intenta DESTRUIR el argumento legal

**Responsabilidades:**
- Buscar jurisprudencia contraria
- Identificar supuestos no probados
- Señalar interpretaciones alternativas
- Proponer escenarios donde el argumento falle
- Cuestionar aplicabilidad de doctrina
- Buscar excepciones a la regla general

**Tácticas:**
1. "¿Qué pasaría si el juez interpreta el artículo de otra forma?"
2. "¿Hay tesis recientes que contradigan este criterio?"
3. "¿Se cumplieron todos los requisitos de procedibilidad?"
4. "¿Hay prescripción o caducidad que se ignore?"
5. "¿Qué diría el abogado de la contraparte?"

**Output:** JSON con debilidades:
```json
{
  "debilidades_identificadas": ["..."],
  "jurisprudencia_contraria": ["..."],
  "escenarios_riesgo": ["..."],
  "interpretaciones_alternativas": ["..."],
  "recomendaciones_fortalecimiento": ["..."],
  "nivel_riesgo": "alto|medio|bajo"
}
```

**IMPORTANTE:** Este agente es CLAVE para 0% alucinaciones. Debe ser implacable.

---

### **AGENTE 7: REDACCIÓN** ✍️

**Rol:** Da formato profesional al documento final

**Responsabilidades:**
- Transformar análisis en documento legal profesional
- Aplicar estructura estándar
- Formatear citas correctamente
- Usar lenguaje preciso pero accesible

**Estructura obligatoria:**
```
I. ANTECEDENTES
   - Hechos relevantes
   - Consulta del cliente

II. MARCO NORMATIVO
   - Fundamento constitucional
   - Leyes aplicables
   - Reglamentos

III. ANÁLISIS
   - Interpretación de normas
   - Aplicación al caso concreto
   - Jurisprudencia relevante

IV. CONCLUSIONES
   - Respuesta directa
   - Recomendaciones prácticas
   - Advertencias de riesgo

V. ANEXOS (si aplica)
```

**Output:** Documento Markdown/LaTeX formateado

---

## 🔒 SISTEMA DE COMPUERTAS DE CALIDAD (5 Gates)

Cada gate es una función de validación que debe pasarse antes de continuar:

### **Gate 1: Verificación de Fuentes**
```python
def gate1_verificar_fuentes(respuesta):
    """
    - ¿Todas las citas son de fuentes primarias?
    - ¿Las URLs/documentos son accesibles?
    - ¿Las normas están vigentes?
    """
    return {"passed": bool, "issues": [...]}
```

### **Gate 2: Coherencia Argumentativa**
```python
def gate2_verificar_coherencia(respuesta):
    """
    - ¿El razonamiento es lógico?
    - ¿No hay contradicciones internas?
    - ¿Las conclusiones siguen de las premisas?
    """
    return {"passed": bool, "issues": [...]}
```

### **Gate 3: Validación de Formato**
```python
def gate3_verificar_formato(respuesta):
    """
    - ¿Cumple estructura profesional?
    - ¿Las citas están correctamente formateadas?
    - ¿Es legible para el cliente?
    """
    return {"passed": bool, "issues": [...]}
```

### **Gate 4: Checklist de Requisitos**
```python
def gate4_verificar_requisitos(respuesta, consulta_original):
    """
    - ¿Respondió la pregunta específica?
    - ¿Incluyó todos los elementos solicitados?
    - ¿Mencionó plazos y costos si aplica?
    """
    return {"passed": bool, "issues": [...]}
```

### **Gate 5: Aprobación Final**
```python
def gate5_aprobacion_final(respuesta, contexto_completo):
    """
    - Revisión humana (si es consulta compleja)
    - Firma digital del sistema
    - Entrega al usuario
    """
    return {"approved": bool, "timestamp": "..."}
```

---

## 📁 ESTRUCTURA DE ARCHIVOS SUGERIDA

```
jurisbot/
├── docker-compose.yml              # MODIFICAR: Agregar Redis
├── onboard_tenant.sh               # EXISTENTE (sin cambios)
├── nginx.conf                      # EXISTENTE (sin cambios)
│
├── backend/
│   ├── main.py                     # EXISTENTE (modificar endpoints)
│   ├── config.py                   # EXISTENTE (agregar config Redis)
│   ├── database.py                 # EXISTENTE (sin cambios)
│   ├── auth/                       # EXISTENTE (sin cambios)
│   │   └── ...
│   ├── legal_scraper.py            # EXISTENTE (sin cambios)
│   │
│   ├── agents/                     # 🆕 NUEVO DIRECTORIO
│   │   ├── __init__.py
│   │   ├── base.py                 # Clase base para agentes
│   │   ├── orchestrator.py         # Agente Orquestador
│   │   ├── normativo.py            # Agente Normativo
│   │   ├── procedimental.py        # Agente Procedimental
│   │   ├── doctrina.py             # Agente Doctrina
│   │   ├── sintesis.py             # Agente Síntesis
│   │   ├── adversarial.py          # Agente Adversarial (CRÍTICO)
│   │   └── redaccion.py            # Agente Redacción
│   │
│   ├── gates/                      # 🆕 NUEVO DIRECTORIO
│   │   ├── __init__.py
│   │   ├── gate1_fuentes.py
│   │   ├── gate2_coherencia.py
│   │   ├── gate3_formato.py
│   │   ├── gate4_requisitos.py
│   │   └── gate5_final.py
│   │
│   ├── workflows/                  # 🆕 NUEVO DIRECTORIO
│   │   ├── __init__.py
│   │   └── legal_consultation.py   # Orquestador de workflow
│   │
│   ├── tasks.py                    # 🆕 NUEVO: Celery tasks
│   └── models.py                   # EXISTENTE (posibles adiciones)
│
├── frontend/                       # EXISTENTE (posibles mejoras UI)
│   └── ...
│
└── data/                           # EXISTENTE (sin cambios)
    └── ...
```

---

## 🔧 IMPLEMENTACIÓN TÉCNICA

### **1. Agregar Redis al docker-compose.yml**

```yaml
# Agregar al docker-compose.yml existente
services:
  # ... servicios existentes ...
  
  redis:
    image: redis:7-alpine
    container_name: jurisbot-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    networks:
      - jurisbot-network

volumes:
  # ... volúmenes existentes ...
  redis_data:
```

### **2. Configurar Celery para Workers**

```python
# backend/celery_app.py
from celery import Celery

celery_app = Celery(
    "jurisbot",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    include=["backend.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Mexico_City",
    enable_utc=True,
)
```

### **3. Clase Base para Agentes**

```python
# backend/agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC):
    """Clase base para todos los agentes de JurisBot"""
    
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.agent_name = self.__class__.__name__
    
    @abstractmethod
    def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la tarea asignada y retorna resultado estructurado
        """
        pass
    
    def log_execution(self, task: Dict, result: Dict):
        """Registra ejecución en audit trail"""
        # Implementar logging
        pass
```

### **4. Workflow Principal**

```python
# backend/workflows/legal_consultation.py
from celery import chain, group
from backend.agents import (
    OrchestratorAgent,
    NormativoAgent,
    ProcedimentalAgent,
    DoctrinaAgent,
    SintesisAgent,
    AdversarialAgent,
    RedaccionAgent
)
from backend.gates import (
    Gate1, Gate2, Gate3, Gate4, Gate5
)

def process_legal_consultation(consulta: str, tenant_id: str) -> dict:
    """
    Workflow completo de consulta legal multi-agente
    """
    # Paso 1: Orquestador analiza y planifica
    orchestrator = OrchestratorAgent()
    plan = orchestrator.execute(consulta)
    
    # Paso 2: Ejecutar agentes especializados en paralelo (donde sea posible)
    agents_tasks = []
    
    if "normativo" in plan["agentes_requeridos"]:
        agents_tasks.append(NormativoAgent().execute.s(plan))
    
    if "procedimental" in plan["agentes_requeridos"]:
        agents_tasks.append(ProcedimentalAgent().execute.s(plan))
    
    if "doctrinal" in plan["agentes_requeridos"]:
        agents_tasks.append(DoctrinaAgent().execute.s(plan))
    
    # Ejecutar en paralelo y esperar resultados
    results = group(agents_tasks).apply_async().get()
    
    # Paso 3: Agente de Síntesis consolida
    sintesis = SintesisAgent().execute(plan, results)
    
    # Gate 1 y 2
    if not Gate1().verify(sintesis):
        return {"error": "Gate 1 fallido", "details": sintesis}
    
    if not Gate2().verify(sintesis):
        return {"error": "Gate 2 fallido", "details": sintesis}
    
    # Paso 4: Agente Adversarial (CRÍTICO)
    adversarial = AdversarialAgent().execute(sintesis)
    
    # Si hay riesgo alto, solicitar revisión
    if adversarial["nivel_riesgo"] == "alto":
        return {
            "warning": "Riesgo alto detectado",
            "adversarial_feedback": adversarial,
            "requires_human_review": True
        }
    
    # Paso 5: Agente de Redacción
    documento = RedaccionAgent().execute(sintesis, adversarial)
    
    # Gates 3, 4, 5
    if not Gate3().verify(documento):
        return {"error": "Gate 3 fallido"}
    
    if not Gate4().verify(documento, consulta):
        return {"error": "Gate 4 fallido"}
    
    if not Gate5().verify(documento):
        return {"error": "Gate 5 fallido"}
    
    return {
        "status": "success",
        "document": documento,
        "audit_trail": {
            "plan": plan,
            "agent_results": results,
            "sintesis": sintesis,
            "adversarial": adversarial,
            "gates_passed": [1, 2, 3, 4, 5]
        }
    }
```

---

## 📊 MODELOS DE IA RECOMENDADOS

| Agente | Modelo Recomendado | Justificación |
|--------|-------------------|---------------|
| **Orquestador** | GPT-4o / Claude 3.5 Sonnet | Razonamiento complejo, planificación |
| **Normativo** | GPT-4o-mini + RAG | Precisión en citas, costo moderado |
| **Procedimental** | GPT-4o-mini | Procesos estructurados |
| **Doctrina** | GPT-4o | Interpretación de tesis complejas |
| **Síntesis** | Claude 3.5 Sonnet | Detección de contradicciones |
| **Adversarial** | GPT-4o | Necesita ser "inteligente" para destruir argumentos |
| **Redacción** | Claude 3.5 Sonnet | Excelente redacción formal |

**Alternativa económica:** Usar Llama 3.1 70B self-hosted para todos los agentes (requiere GPU)

---

## ✅ CRITERIOS DE ÉXITO

### **Funcionales:**
- [ ] Los 7 agentes ejecutan correctamente
- [ ] El workflow completo funciona end-to-end
- [ ] Las 5 compuertas de calidad validan correctamente
- [ ] El sistema multi-tenant sigue funcionando
- [ ] El RAG existente se integra con agentes

### **De Calidad:**
- [ ] 0% de alucinaciones en entregables finales
- [ ] Tiempo de respuesta < 30 segundos (consulta simple)
- [ ] Tiempo de respuesta < 2 minutos (consulta compleja)
- [ ] Audit trail completo para cada consulta
- [ ] El agente adversarial detecta al menos 1 debilidad por consulta

### **Técnicos:**
- [ ] Redis funciona correctamente
- [ ] Celery workers procesan tareas en paralelo
- [ ] Docker Compose levanta todos los servicios
- [ ] Tests unitarios para cada agente
- [ ] Tests de integración para workflow completo

---

## 📅 CRONOGRAMA SUGERIDO

### **Fase 1: Fundamentos (Semana 1-2)**
- [ ] Agregar Redis a docker-compose.yml
- [ ] Configurar Celery
- [ ] Crear estructura de carpetas /agents y /gates
- [ ] Implementar clase base BaseAgent

### **Fase 2: Agentes Core (Semana 3-4)**
- [ ] Implementar Orquestador
- [ ] Implementar Normativo (integrar con RAG existente)
- [ ] Implementar Procedimental
- [ ] Implementar Síntesis

### **Fase 3: Calidad (Semana 5-6)**
- [ ] Implementar Adversarial (CRÍTICO)
- [ ] Implementar Gates 1-3
- [ ] Tests de no-alucinación

### **Fase 4: Completar (Semana 7-8)**
- [ ] Implementar Doctrina
- [ ] Implementar Redacción
- [ ] Implementar Gates 4-5
- [ ] Integrar con frontend existente

### **Fase 5: Testing (Semana 9-10)**
- [ ] Tests unitarios
- [ ] Tests de integración
- [ ] Pruebas con usuarios reales
- [ ] Optimización de performance

---

## 🎁 ENTREGABLES ESPERADOS

1. **Código fuente** en repositorio Git
2. **Documentación técnica** de cada agente
3. **Tests** unitarios y de integración
4. **Docker Compose** actualizado y funcional
5. **Guía de deployment** paso a paso
6. **Ejemplos** de consultas procesadas

---

## ❓ PREGUNTAS PARA ANTIGRAVITY

Antes de comenzar, por favor confirma:

1. **¿Tienes acceso al repositorio actual de JurisBot?**
2. **¿Qué modelo de IA prefieres usar?** (OpenAI, Anthropic, o self-hosted)
3. **¿Hay alguna parte del código actual que NO deba modificarse?**
4. **¿Prefieres implementar todos los agentes de una vez o iterativamente?**
5. **¿Hay restricciones de presupuesto para las APIs de IA?**

---

## 🚀 MENSAJE FINAL

**Antigravity:** Este es un proyecto ambicioso pero factible. La clave está en:

1. **Reutilizar** la infraestructura base existente
2. **Implementar** el Agente Adversarial correctamente (es el seguro contra alucinaciones)
3. **Probar** exhaustivamente cada gate de calidad
4. **Documentar** todo para mantenimiento futuro

El resultado será un sistema legal AI de clase mundial, específicamente diseñado para el derecho mexicano, con la garantía de calidad que distingue a los mejores despachos.

**¿Listo para comenzar?** 🚀

---

**Contacto:** Iván Márquez Larios (ivanjose@gmail.com)  
**Fecha:** Marzo 2026  
**Prioridad:** Alta (lanzamiento post-mudanza a Puerto Morelos)