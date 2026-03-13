# 🚀 PROMPT DE IMPLEMENTACIÓN INMEDIATA PARA ANTIGRAVITY
## JurisBot Multi-Agente - Versión Lista para Desarrollo

**Prioridad:** URGENTE  
**Fecha:** Marzo 2026  
**Estado:** Listo para implementación  
**Tiempo estimado:** 8-10 semanas

---

## 📋 RESUMEN EJECUTIVO

**Objetivo:** Evolucionar JurisBot de arquitectura monolítica a **sistema multi-agente** con 8 agentes especializados y garantía de **0% alucinaciones**.

**Estrategia:** Reutilizar infraestructura base existente (Docker, PostgreSQL, multi-tenant) y agregar capa de agentes.

**NO es un rewrite:** Conservar todo el código existente funcional.

---

## 🏗️ ARQUITECTURA OBJETIVO

```
JurisBot Evolucionado:
├── Frontend: React (existente)
├── Backend: FastAPI + Redis (nuevo)
├── Database: PostgreSQL + pgvector (existente)
├── Message Queue: Redis (NUEVO)
│
├── 8 AGENTES ESPECIALIZADOS:
│   ├── 1. Orquestador (Router)
│   ├── 2. Normativo (Leyes)
│   ├── 3. Procedimental (Procesos)
│   ├── 4. Doctrina (Jurisprudencia)
│   ├── 5. Síntesis (Verificación)
│   ├── 6. Adversarial (Devil's Advocate)
│   ├── 7. Redacción (Formato)
│   └── 8. DocumentManager (Scraping + Curación) ⭐ NUEVO
│
└── 5 COMPUERTAS DE CALIDAD
```

---

## 🤖 ESPECIFICACIÓN DE AGENTES (8 Total)

### **AGENTE 1: ORQUESTADOR** 🎭

```python
class OrchestratorAgent(BaseAgent):
    """
    Recibe consulta, analiza área del derecho, descompone en subtareas,
    asigna agentes especializados, genera PLAN DE TRABAJO estructurado.
    """
    
    def execute(self, consulta: str, context: dict) -> dict:
        # 1. Analizar área del derecho
        # 2. Descomponer problema
        # 3. Asignar agentes
        # 4. Definir flujo de trabajo
        # 5. Generar plan estructurado
        
        return {
            "area_derecho": "civil|mercantil|penal|laboral|administrativo|fiscal",
            "agentes_requeridos": ["normativo", "procedimental", "doctrinal"],
            "plan_trabajo": [...],
            "prioridad": "urgente|estándar|profunda"
        }
```

**Modelo:** GPT-4o / Claude 3.5 Sonnet

---

### **AGENTE 2: NORMATIVO** 📚

```python
class NormativoAgent(BaseAgent):
    """
    Especialista en leyes, reglamentos y normativa oficial mexicana.
    Usa RAG existente (PostgreSQL/pgvector).
    """
    
    def execute(self, task: dict, context: dict) -> dict:
        # 1. Buscar normativa aplicable en base de conocimiento
        # 2. Verificar vigencia (¿derogadas? ¿reformadas?)
        # 3. Especificar jerarquía normativa
        # 4. Citar artículos específicos
        # 5. Usar SOLO fuentes primarias
        
        return {
            "normas_aplicables": [...],
            "jerarquia_normativa": "...",
            "conflictos_detectados": "...",
            "fuentes_primarias": ["urls_oficiales"]
        }
```

**Integración:** Usar sistema RAG existente (`legal_scraper.py`)

---

### **AGENTE 3: PROCEDIMENTAL** ⚖️

```python
class ProcedimentalAgent(BaseAgent):
    """
    Especialista en procedimientos, plazos y requisitos procesales.
    """
    
    def execute(self, task: dict, context: dict) -> dict:
        # 1. Identificar vía procesal correcta
        # 2. Detallar requisitos de procedibilidad
        # 3. Especificar plazos (hábiles vs naturales)
        # 4. Indicar competencia (juzgado, tribunal)
        # 5. Mencionar costos aproximados
        
        return {
            "via_procesal": "...",
            "juzgado_competente": "...",
            "requisitos_procedibilidad": [...],
            "pasos_procesales": [...],
            "plazos_criticos": [...],
            "riesgos": [...]
        }
```

---

### **AGENTE 4: DOCTRINA** 🔍

```python
class DoctrinaAgent(BaseAgent):
    """
    Especialista en tesis de jurisprudencia, tesis aisladas y doctrina.
    """
    
    def execute(self, task: dict, context: dict) -> dict:
        # 1. Buscar tesis de jurisprudencia relevantes
        # 2. Buscar tesis aisladas aplicables
        # 3. Buscar doctrina de autores reconocidos
        # 4. Priorizar tesis recientes (últimos 5 años)
        # 5. Identificar criterios contradictorios
        
        return {
            "tesis_jurisprudencia": [...],
            "doctrina_relevante": [...],
            "criterios_contrarios": [...],
            "tendencia_actual": "..."
        }
```

---

### **AGENTE 5: SÍNTESIS** 🧪

```python
class SintesisAgent(BaseAgent):
    """
    Consolida hallazgos y detecta inconsistencias.
    """
    
    def execute(self, task: dict, context: dict) -> dict:
        # 1. Consolidar hallazgos de todos los agentes
        # 2. Detectar contradicciones entre fuentes
        # 3. Verificar que citas sean correctas
        # 4. Identificar gaps de información
        # 5. Marcar conflictos para revisión
        
        return {
            "sintesis_argumento": "...",
            "contradicciones_detectadas": [...],
            "verificaciones_pasadas": [...],
            "verificaciones_fallidas": [...],
            "recomendacion": "proceder|solicitar_revision|detener"
        }
```

---

### **AGENTE 6: ADVERSARIAL** 😈 (CRÍTICO)

```python
class AdversarialAgent(BaseAgent):
    """
    Abogado del diablo - intenta DESTRUIR el argumento legal.
    CLAVE para 0% alucinaciones.
    """
    
    def execute(self, task: dict, context: dict) -> dict:
        # 1. Buscar jurisprudencia contraria
        # 2. Identificar supuestos no probados
        # 3. Señalar interpretaciones alternativas
        # 4. Proponer escenarios donde el argumento falle
        # 5. Cuestionar aplicabilidad de doctrina
        
        return {
            "debilidades_identificadas": [...],
            "jurisprudencia_contraria": [...],
            "escenarios_riesgo": [...],
            "interpretaciones_alternativas": [...],
            "nivel_riesgo": "alto|medio|bajo"
        }
```

**IMPORTANTE:** Si `nivel_riesgo == "alto"`, solicitar revisión humana.

---

### **AGENTE 7: REDACCIÓN** ✍️

```python
class RedaccionAgent(BaseAgent):
    """
    Da formato profesional al documento final.
    """
    
    def execute(self, task: dict, context: dict) -> dict:
        # 1. Transformar análisis en documento legal
        # 2. Aplicar estructura estándar
        # 3. Formatear citas correctamente
        # 4. Usar lenguaje preciso pero accesible
        
        return {
            "documento": "markdown_formateado",
            "estructura": {
                "antecedentes": "...",
                "marco_normativo": "...",
                "analisis": "...",
                "conclusiones": "..."
            }
        }
```

---

### **AGENTE 8: DOCUMENT MANAGER** 📥 ⭐ NUEVO

```python
class DocumentManagerAgent(BaseAgent):
    """
    Especialista en descarga, validación y mantenimiento de base documental.
    Scraping de fuentes oficiales + curación de documentos.
    """
    
    def __init__(self):
        self.scrapers = {
            "dof": DOFScraper(),
            "scjn": SCJNScraper(),
            "congreso": CongresoScraper(),
            "estatales": GenericLegalScraper()
        }
    
    def execute(self, task: dict, context: dict) -> dict:
        operation = task.get("operation")
        
        if operation == "download_new":
            return self._download_new_documents(task)
        elif operation == "check_updates":
            return self._check_for_updates(task)
        elif operation == "scrape_source":
            return self._scrape_legal_source(task)
        elif operation == "validate_document":
            return self._validate_document(task)
        elif operation == "reindex":
            return self._reindex_documents(task)
    
    def _scrape_legal_source(self, task: dict) -> dict:
        """
        Scraping de fuentes legales con múltiples formatos.
        Soporta: PDF, DOCX, DOC, HTML
        """
        source = task.get("source")  # "dof", "scjn", "congreso", etc.
        scraper = self.scrapers.get(source)
        
        if not scraper:
            return {"error": f"Source {source} not supported"}
        
        # Ejecutar scraping
        documents = scraper.scrape()
        
        # Procesar cada documento
        processed = []
        for doc in documents:
            # Descargar según formato
            if doc.format == "pdf":
                result = self._download_pdf(doc)
            elif doc.format in ["docx", "doc"]:
                result = self._download_docx(doc)
            elif doc.format == "html":
                result = self._scrape_html(doc)
            
            if result.success:
                # Validar integridad
                if self._validate_integrity(result.file_path):
                    # Extraer texto y chunking
                    chunks = self._process_document(result.file_path, doc)
                    # Indexar en vector DB
                    self._index_document(chunks, doc)
                    processed.append(doc)
        
        return {
            "operation": "scrape_source",
            "source": source,
            "documents_found": len(documents),
            "documents_processed": len(processed),
            "status": "success"
        }
```

**Scrapers Implementar:**

```python
# DOFScraper - Diario Oficial
class DOFScraper(BaseScraper):
    BASE_URL = "https://www.dof.gob.mx"
    
    def scrape(self) -> List[DocumentInfo]:
        # Navegar por fechas
        # Detectar secciones (Primera, Segunda, Tercera, Cuarta)
        # Extraer enlaces a PDFs
        # Clasificar por tipo (decreto, ley, reglamento, NOM)
        pass

# SCJNScraper - Tesis de Jurisprudencia  
class SCJNScraper(BaseScraper):
    BASE_URL = "https://www.scjn.gob.mx"
    
    def scrape(self) -> List[DocumentInfo]:
        # Usar buscador de tesis
        # Manejar paginación
        # Extraer metadatos (número, materia, fecha)
        pass

# CongresoScraper - Leyes Federales
class CongresoScraper(BaseScraper):
    BASE_URL = "http://www.diputados.gob.mx/LeyesBiblio"
    
    def scrape(self) -> List[DocumentInfo]:
        # Obtener catálogo de leyes
        # Detectar formatos (PDF, DOCX, DOC)
        # Descargar con validación
        pass

# GenericLegalScraper - Sitios estatales
class GenericLegalScraper(BaseScraper):
    def scrape(self, config: dict) -> List[DocumentInfo]:
        # Configurable por URL
        # Soporta múltiples selectores CSS
        # Manejo de paginación
        pass
```

**Características del DocumentManager:**
- ✅ Scraping de DOF, SCJN, Congreso
- ✅ Soporte PDF, DOCX, DOC, HTML
- ✅ Validación de integridad (hash SHA256)
- ✅ Rate limiting (6-10 req/min por fuente)
- ✅ Reintentos con backoff exponencial
- ✅ Detección de actualizaciones
- ✅ Chunking inteligente por tipo de documento

---

## 🔒 COMPUERTAS DE CALIDAD (5 Gates)

```python
class QualityGateSystem:
    """
    Sistema de 5 compuertas para garantizar 0% alucinaciones
    """
    
    def validate(self, document: dict, original_query: str) -> dict:
        gates = [
            self._gate1_fuentes(document),
            self._gate2_coherencia(document),
            self._gate3_formato(document),
            self._gate4_requisitos(document, original_query),
            self._gate5_final(document)
        ]
        
        failed_gates = [g for g in gates if not g["passed"]]
        
        return {
            "approved": len(failed_gates) == 0,
            "gates_passed": len([g for g in gates if g["passed"]]),
            "gates_failed": failed_gates,
            "can_proceed": len(failed_gates) == 0
        }
    
    def _gate1_fuentes(self, doc: dict) -> dict:
        """Verificación de fuentes primarias"""
        checks = [
            all(cita.get("es_primaria") for cita in doc.get("citas", [])),
            all(cita.get("url") for cita in doc.get("citas", [])),
            all(cita.get("vigente") for cita in doc.get("citas", []))
        ]
        return {"passed": all(checks), "gate": 1}
    
    def _gate2_coherencia(self, doc: dict) -> dict:
        """Coherencia argumentativa"""
        # Verificar que conclusiones sigan de premisas
        # Detectar contradicciones internas
        pass
    
    def _gate3_formato(self, doc: dict) -> dict:
        """Validación de formato profesional"""
        # Verificar estructura I-V
        # Citas correctamente formateadas
        pass
    
    def _gate4_requisitos(self, doc: dict, query: str) -> dict:
        """Checklist de requisitos del usuario"""
        # Verificar que respondió la pregunta específica
        # Incluyó todos los elementos solicitados
        pass
    
    def _gate5_final(self, doc: dict) -> dict:
        """Aprobación final"""
        # Revisión humana si es consulta compleja
        # Firma digital del sistema
        pass
```

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
jurisbot/
├── docker-compose.yml              # MODIFICAR: Agregar Redis
├── onboard_tenant.sh               # EXISTENTE
├── nginx.conf                      # EXISTENTE
│
├── backend/
│   ├── main.py                     # MODIFICAR: Agregar endpoints
│   ├── config.py                   # MODIFICAR: Config Redis
│   ├── database.py                 # EXISTENTE
│   ├── auth/                       # EXISTENTE
│   ├── legal_scraper.py            # EXISTENTE (integrar con Agente 8)
│   │
│   ├── agents/                     # 🆕 NUEVO DIRECTORIO
│   │   ├── __init__.py
│   │   ├── base.py                 # Clase BaseAgent
│   │   ├── orchestrator.py         # Agente 1
│   │   ├── normativo.py            # Agente 2
│   │   ├── procedimental.py        # Agente 3
│   │   ├── doctrina.py             # Agente 4
│   │   ├── sintesis.py             # Agente 5
│   │   ├── adversarial.py          # Agente 6 (CRÍTICO)
│   │   ├── redaccion.py            # Agente 7
│   │   └── document_manager.py     # Agente 8 ⭐ NUEVO
│   │
│   ├── scrapers/                   # 🆕 NUEVO DIRECTORIO
│   │   ├── __init__.py
│   │   ├── base.py                 # BaseScraper
│   │   ├── dof_scraper.py          # DOFScraper
│   │   ├── scjn_scraper.py         # SCJNScraper
│   │   ├── congreso_scraper.py     # CongresoScraper
│   │   └── generic_scraper.py      # GenericLegalScraper
│   │
│   ├── gates/                      # 🆕 NUEVO DIRECTORIO
│   │   ├── __init__.py
│   │   └── quality_system.py       # QualityGateSystem
│   │
│   ├── workflows/                  # 🆕 NUEVO DIRECTORIO
│   │   ├── __init__.py
│   │   └── legal_workflow.py       # Orquestador de flujo
│   │
│   ├── celery_app.py               # 🆕 NUEVO
│   └── tasks.py                    # 🆕 NUEVO
│
└── frontend/                       # EXISTENTE
    └── ...
```

---

## 🔧 IMPLEMENTACIÓN TÉCNICA

### **1. Agregar Redis a docker-compose.yml**

```yaml
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

### **2. Clase Base para Agentes**

```python
# backend/agents/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Clase base para todos los agentes de JurisBot"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.agent_name = self.__class__.__name__
    
    @abstractmethod
    def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la tarea asignada y retorna resultado estructurado"""
        pass
    
    def log_execution(self, task: Dict, result: Dict):
        """Registra ejecución en audit trail"""
        logger.info(f"[{self.agent_name}] Task: {task.get('type')} | Status: {result.get('status')}")
```

### **3. Workflow Principal**

```python
# backend/workflows/legal_workflow.py
from celery import chain, group
from backend.agents import *
from backend.gates import QualityGateSystem

def process_legal_consultation(consulta: str, tenant_id: str) -> dict:
    """
    Workflow completo de consulta legal multi-agente
    """
    # Paso 1: Orquestador
    orchestrator = OrchestratorAgent()
    plan = orchestrator.execute({"consulta": consulta}, {})
    
    # Paso 2: Ejecutar agentes especializados en paralelo
    agents_tasks = []
    
    if "normativo" in plan["agentes_requeridos"]:
        agents_tasks.append(NormativoAgent().execute.s(plan))
    
    if "procedimental" in plan["agentes_requeridos"]:
        agents_tasks.append(ProcedimentalAgent().execute.s(plan))
    
    if "doctrinal" in plan["agentes_requeridos"]:
        agents_tasks.append(DoctrinaAgent().execute.s(plan))
    
    # Ejecutar en paralelo
    results = group(agents_tasks).apply_async().get()
    
    # Paso 3: Síntesis
    sintesis = SintesisAgent().execute(plan, {"results": results})
    
    # Gates 1-2
    gate_system = QualityGateSystem()
    gate_check = gate_system.validate(sintesis, consulta)
    
    if not gate_check["can_proceed"]:
        return {"error": "Quality gates failed", "details": gate_check}
    
    # Paso 4: Adversarial (CRÍTICO)
    adversarial = AdversarialAgent().execute(sintesis)
    
    if adversarial["nivel_riesgo"] == "alto":
        return {
            "warning": "Riesgo alto detectado",
            "requires_human_review": True,
            "adversarial_feedback": adversarial
        }
    
    # Paso 5: Redacción
    documento = RedaccionAgent().execute(sintesis, adversarial)
    
    # Gates 3-5
    final_check = gate_system.validate(documento, consulta)
    
    if not final_check["can_proceed"]:
        return {"error": "Final quality gates failed"}
    
    return {
        "status": "success",
        "document": documento,
        "audit_trail": {
            "plan": plan,
            "agent_results": results,
            "sintesis": sintesis,
            "adversarial": adversarial,
            "gates": final_check
        }
    }
```

---

## 📊 MODELOS DE IA

| Agente | Modelo | Costo aprox |
|--------|--------|-------------|
| Orquestador | GPT-4o / Claude 3.5 | $0.03-0.06/1K tokens |
| Normativo | GPT-4o-mini + RAG | $0.005/1K tokens |
| Procedimental | GPT-4o-mini | $0.005/1K tokens |
| Doctrina | GPT-4o | $0.03/1K tokens |
| Síntesis | Claude 3.5 | $0.03/1K tokens |
| Adversarial | GPT-4o | $0.03/1K tokens |
| Redacción | Claude 3.5 | $0.03/1K tokens |
| DocumentManager | GPT-4o-mini | $0.005/1K tokens |

**Estimado:** $300-600 USD/mes en APIs

---

## ✅ CRITERIOS DE ÉXITO

### **Funcionales:**
- [ ] Los 8 agentes ejecutan correctamente
- [ ] Workflow completo funciona end-to-end
- [ ] Las 5 compuertas de calidad validan correctamente
- [ ] DocumentManager descarga y procesa documentos automáticamente
- [ ] Multi-tenant sigue funcionando

### **De Calidad:**
- [ ] 0% de alucinaciones en entregables finales
- [ ] Tiempo de respuesta < 30 segundos (simple)
- [ ] Tiempo de respuesta < 2 minutos (compleja)
- [ ] Audit trail completo
- [ ] Agente adversarial detecta debilidades

### **Técnicos:**
- [ ] Redis funciona correctamente
- [ ] Celery workers procesan tareas en paralelo
- [ ] Docker Compose levanta todos los servicios
- [ ] Scrapers funcionan con todas las fuentes configuradas
- [ ] Tests unitarios y de integración

---

## 📅 CRONOGRAMA DE IMPLEMENTACIÓN

### **Fase 1: Fundamentos (Semana 1-2)**
- [ ] Agregar Redis a docker-compose.yml
- [ ] Configurar Celery
- [ ] Crear estructura de carpetas /agents, /scrapers, /gates
- [ ] Implementar clase base BaseAgent
- [ ] Implementar BaseScraper

### **Fase 2: Agentes Core (Semana 3-4)**
- [ ] Implementar Orquestador (Agente 1)
- [ ] Implementar Normativo (Agente 2) - integrar con RAG existente
- [ ] Implementar Procedimental (Agente 3)
- [ ] Implementar Síntesis (Agente 5)

### **Fase 3: Calidad (Semana 5-6)**
- [ ] Implementar Adversarial (Agente 6) - CRÍTICO
- [ ] Implementar Gates 1-3
- [ ] Tests de no-alucinación

### **Fase 4: Completar Agentes (Semana 7-8)**
- [ ] Implementar Doctrina (Agente 4)
- [ ] Implementar Redacción (Agente 7)
- [ ] Implementar Gates 4-5

### **Fase 5: DocumentManager (Semana 9-10)** ⭐ NUEVO
- [ ] Implementar DOFScraper
- [ ] Implementar SCJNScraper
- [ ] Implementar CongresoScraper
- [ ] Implementar DocumentManagerAgent (Agente 8)
- [ ] Sistema de schedule automático
- [ ] Dashboard de monitoreo

### **Fase 6: Testing (Semana 11-12)**
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
7. **Dashboard** de monitoreo de DocumentManager

---

## 🚨 NOTAS IMPORTANTES

1. **NO modificar** el sistema multi-tenant existente - solo extender
2. **Reutilizar** `legal_scraper.py` existente - integrar con Agente 8
3. **Corregir** problemas de SSL (`verify=False`) en descargas
4. **Implementar** rate limiting en todos los scrapers
5. **Mantener** backward compatibility con API existente

---

## ❓ PREGUNTAS PARA CONFIRMAR

Antes de comenzar, confirma:

1. **¿Tienes acceso al repositorio actual de JurisBot?**
2. **¿Qué modelo de IA prefieres usar?** (OpenAI, Anthropic, o self-hosted)
3. **¿Prefieres implementar todos los agentes de una vez o iterativamente?**
4. **¿Hay restricciones de presupuesto para las APIs de IA?**
5. **¿Cuál es el timeline objetivo?** (¿8 semanas es realista?)

---

## 🚀 MENSAJE FINAL

**Antigravity:** Este es un proyecto ambicioso pero bien definido. La clave está en:

1. **Reutilizar** la infraestructura base existente
2. **Implementar** el Agente Adversarial correctamente (seguro contra alucinaciones)
3. **Implementar** el DocumentManager con scraping robusto (Agente 8)
4. **Probar** exhaustivamente cada gate de calidad
5. **Documentar** todo para mantenimiento futuro

El resultado será un sistema legal AI de clase mundial, específicamente diseñado para el derecho mexicano, con garantía de calidad y base documental actualizada automáticamente.

**¿Listo para comenzar?** 🚀

---

**Contacto:** Iván Márquez Larios (ivanjose@gmail.com)  
**Fecha:** Marzo 2026  
**Prioridad:** URGENTE - Lanzamiento post-mudanza a Puerto Morelos