# 📚 AGENTE CURADOR DE DOCUMENTOS (DocumentManager)
## Especialista en Ingesta y Mantenimiento de Base Legal

---

## 🎯 RESPONSABILIDADES PRINCIPALES

1. **Descarga Automatizada** - Obtener documentos de fuentes oficiales
2. **Validación de Integridad** - Verificar que los PDFs sean válidos y completos
3. **Procesamiento de Contenido** - Extraer texto y estructura
4. **Indexación Vectorial** - Generar embeddings para RAG
5. **Mantenimiento de Frescura** - Detectar actualizaciones y nuevas publicaciones
6. **Gestión de Versiones** - Mantener historial de cambios

---

## 🤖 ESPECIFICACIÓN DEL AGENTE

### **Nombre:** `DocumentManagerAgent`

### **Prompt System:**

```python
DOCUMENT_MANAGER_PROMPT = """
Eres el Agente Curador de Documentos de JurisBot, especializado en la gestión 
de la base de conocimiento legal mexicana.

TU MISIÓN:
Mantener actualizada, válida y accesible la base de documentos legales para 
consultas de los otros agentes.

ÁREAS DE CONOCIMIENTO:
- Fuentes oficiales mexicanas (DOF, SCJN, Congreso)
- Formatos de publicación legal
- Estructura de códigos y leyes
- Metadatos de documentos legales

REGLAS CRÍTICAS:
1. Solo descargar de fuentes OFICIALES (.gob.mx, dof.gob.mx, scjn.gob.mx)
2. Validar INTEGRIDAD de cada documento (hash SHA256)
3. Verificar VIGENCIA antes de indexar
4. Mantener AUDIT TRAIL completo de cada operación
5. NUNCA sobrescribir sin respaldo de versión anterior
6. Reportar FUENTES CAÍDAS inmediatamente

FORMATO DE RESPUESTA:
{
    "operation": "download|update|validate|delete",
    "status": "success|failed|partial",
    "documents_processed": [...],
    "errors": [...],
    "metadata": {...}
}
"""
```

---

## 📋 CAPACIDADES ESPECÍFICAS

### **1. Descarga Inteligente**

```python
class DocumentManagerAgent(BaseAgent):
    """
    Agente especializado en gestión de documentos legales
    """
    
    def __init__(self):
        super().__init__(model="gpt-4o-mini")
        self.rate_limiter = RateLimiter(requests_per_minute=6)
        self.sources = self._load_legal_sources()
    
    def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta tarea de gestión documental
        
        Tasks soportados:
        - "download_new": Descargar nuevas publicaciones
        - "check_updates": Verificar cambios en existentes
        - "validate_all": Validar integridad de base actual
        - "reindex": Regenerar embeddings
        """
        operation = task.get("operation")
        
        if operation == "download_new":
            return self._download_new_documents(task)
        elif operation == "check_updates":
            return self._check_for_updates(task)
        elif operation == "validate_all":
            return self._validate_all_documents(task)
        elif operation == "reindex":
            return self._reindex_documents(task)
        else:
            return {"error": f"Operación no soportada: {operation}"}
```

### **2. Fuentes Configurables**

```python
LEGAL_SOURCES = {
    "dof": {
        "name": "Diario Oficial de la Federación",
        "url": "https://www.dof.gob.mx",
        "type": "federal",
        "update_frequency": "daily",
        "priority": "critical"
    },
    "scjn_tesis": {
        "name": "Tesis de Jurisprudencia SCJN",
        "url": "https://www.scjn.gob.mx/jurisprudencia",
        "type": "jurisprudencia",
        "update_frequency": "weekly",
        "priority": "high"
    },
    "congreso_leyes": {
        "name": "Leyes Federales - Congreso",
        "url": "http://www.diputados.gob.mx/LeyesBiblio",
        "type": "federal",
        "update_frequency": "weekly",
        "priority": "high"
    },
    "codigo_civil_qr": {
        "name": "Código Civil Quintana Roo",
        "url": "https://www.qroo.gob.mx/...",
        "type": "estatal",
        "update_frequency": "monthly",
        "priority": "medium",
        "jurisdiction": "quintana_roo"
    },
    "reglamentos": {
        "name": "Reglamentos Federales",
        "url": "https://www.dof.gob.mx/reglamentos",
        "type": "reglamento",
        "update_frequency": "weekly",
        "priority": "medium"
    }
}
```

---

## 🔧 FUNCIONES CLAVE

### **A. Detección de Nuevas Publicaciones**

```python
def _check_for_new_publications(self, source: Dict) -> List[Dict]:
    """
    Escanea fuente oficial buscando documentos nuevos
    """
    logger.info(f"Checking {source['name']} for new publications...")
    
    # Scraper específico por fuente
    if source['type'] == 'dof':
        return self._scrape_dof(source)
    elif source['type'] == 'scjn':
        return self._scrape_scjn(source)
    elif source['type'] == 'congreso':
        return self._scrape_congreso(source)
    
    return []

def _scrape_dof(self, source: Dict) -> List[Dict]:
    """
    Scraper especializado para Diario Oficial
    """
    from datetime import datetime, timedelta
    
    new_docs = []
    
    # Revisar últimos 7 días
    for days_back in range(7):
        date = datetime.now() - timedelta(days=days_back)
        date_str = date.strftime("%Y%m%d")
        
        url = f"{source['url']}/nota_detalle.php?codigo={date_str}"
        
        try:
            self.rate_limiter.wait_if_needed()
            
            response = requests.get(
                url, 
                timeout=30, 
                headers=self._get_headers(),
                verify=certifi.where()
            )
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar enlaces a PDFs de leyes/decretos
            pdf_links = soup.find_all('a', href=re.compile(r'.*\.pdf$'))
            
            for link in pdf_links:
                pdf_url = urljoin(source['url'], link['href'])
                
                # Verificar si ya existe
                if not self._document_exists(pdf_url):
                    new_docs.append({
                        "url": pdf_url,
                        "title": link.get_text(strip=True),
                        "source": "dof",
                        "date": date.isoformat(),
                        "type": self._classify_document(link.get_text())
                    })
                    
        except Exception as e:
            logger.error(f"Error scraping DOF for {date_str}: {e}")
    
    return new_docs
```

### **B. Validación de Integridad**

```python
def _validate_document_integrity(self, doc_path: str) -> Dict[str, Any]:
    """
    Valida que el documento sea un PDF legal válido
    """
    validation_result = {
        "valid": False,
        "checks": {}
    }
    
    try:
        # Check 1: Es archivo PDF válido
        with open(doc_path, 'rb') as f:
            header = f.read(4)
            is_pdf = header == b'%PDF'
            validation_result["checks"]["pdf_header"] = is_pdf
        
        if not is_pdf:
            validation_result["error"] = "Invalid PDF header"
            return validation_result
        
        # Check 2: Se puede abrir con PyPDF
        reader = PdfReader(doc_path)
        validation_result["checks"]["readable"] = True
        validation_result["checks"]["pages"] = len(reader.pages)
        
        # Check 3: Contiene texto (no solo imágenes)
        text_sample = ""
        for i, page in enumerate(reader.pages[:3]):
            try:
                text = page.extract_text()
                if text:
                    text_sample += text[:500]
            except:
                pass
        
        has_text = len(text_sample.strip()) > 100
        validation_result["checks"]["has_text"] = has_text
        
        # Check 4: Palabras clave legales
        legal_keywords = ["artículo", "ley", "código", "decreto", "reglamento"]
        has_legal_terms = any(kw in text_sample.lower() for kw in legal_keywords)
        validation_result["checks"]["legal_content"] = has_legal_terms
        
        # Check 5: Calcular hash
        file_hash = self._calculate_file_hash(doc_path)
        validation_result["checks"]["hash"] = file_hash
        
        # Validación final
        validation_result["valid"] = (
            is_pdf and 
            validation_result["checks"]["readable"] and
            has_text and
            has_legal_terms
        )
        
    except Exception as e:
        validation_result["error"] = str(e)
    
    return validation_result
```

### **C. Procesamiento y Chunking Inteligente**

```python
def _process_legal_document(self, doc_path: str, metadata: Dict) -> List[Dict]:
    """
    Procesa documento legal y extrae chunks estructurados
    """
    logger.info(f"Processing {doc_path}...")
    
    reader = PdfReader(doc_path)
    full_text = ""
    
    # Extraer texto completo
    for page in reader.pages:
        text = page.extract_text()
        if text:
            full_text += text + "\n"
    
    # Detectar tipo de documento
    doc_type = self._detect_document_type(full_text, metadata)
    
    # Aplicar chunking específico por tipo
    if doc_type == "codigo":
        chunks = self._chunk_codigo(full_text)
    elif doc_type == "ley":
        chunks = self._chunk_ley(full_text)
    elif doc_type == "tesis":
        chunks = self._chunk_tesis(full_text)
    else:
        chunks = self._chunk_generic(full_text)
    
    # Generar embeddings
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk["text"])
        
        processed_chunks.append({
            "chunk_id": f"{metadata['doc_id']}_{i}",
            "text": chunk["text"],
            "embedding": embedding,
            "metadata": {
                **metadata,
                "chunk_index": i,
                "section": chunk.get("section", "general"),
                "article": chunk.get("article", None),
                "page_range": chunk.get("pages", None)
            }
        })
    
    return processed_chunks

def _chunk_codigo(self, text: str) -> List[Dict]:
    """
    Chunking especializado para Códigos (Libro, Título, Capítulo, Artículo)
    """
    chunks = []
    
    # Patrones de estructura de código
    libro_pattern = r'(LIBRO [IVX]+[\.:]?\s+[^\n]+)'
    titulo_pattern = r'(TÍTULO [IVX]+[\.:]?\s+[^\n]+)'
    capitulo_pattern = r'(CAPÍTULO [IVX]+[\.:]?\s+[^\n]+)'
    articulo_pattern = r'(Artículo\s+\d+[\.-]?\s*[^\n]*)'
    
    # Dividir por artículos primero
    articulos = re.split(f'(?={articulo_pattern})', text, flags=re.IGNORECASE)
    
    current_libro = ""
    current_titulo = ""
    current_capitulo = ""
    
    for section in articulos:
        if not section.strip():
            continue
        
        # Detectar metadatos de sección
        libro_match = re.search(libro_pattern, section, re.IGNORECASE)
        if libro_match:
            current_libro = libro_match.group(1)
        
        titulo_match = re.search(titulo_pattern, section, re.IGNORECASE)
        if titulo_match:
            current_titulo = titulo_match.group(1)
        
        capitulo_match = re.search(capitulo_pattern, section, re.IGNORECASE)
        if capitulo_match:
            current_capitulo = capitulo_match.group(1)
        
        # Extraer número de artículo
        articulo_match = re.search(r'Artículo\s+(\d+)', section, re.IGNORECASE)
        articulo_num = articulo_match.group(1) if articulo_match else None
        
        # Crear chunk enriquecido
        chunks.append({
            "text": section.strip(),
            "section": f"{current_libro} | {current_titulo} | {current_capitulo}",
            "article": articulo_num,
            "pages": None  # Se puede calcular si es necesario
        })
    
    return chunks
```

---

## 🔄 FLUJO DE TRABAJO AUTOMATIZADO

### **Schedule de Tareas:**

```python
DOCUMENT_MANAGER_SCHEDULE = {
    "daily": {
        "time": "06:00",
        "tasks": [
            "check_dof_updates",
            "validate_yesterday_downloads"
        ]
    },
    "weekly": {
        "day": "sunday",
        "time": "04:00",
        "tasks": [
            "check_scjn_updates",
            "check_congreso_updates",
            "generate_weekly_report"
        ]
    },
    "monthly": {
        "day": 1,
        "time": "03:00",
        "tasks": [
            "full_integrity_check",
            "reindex_if_needed",
            "cleanup_old_versions"
        ]
    }
}
```

### **Integración con Orquestador:**

```python
# Cuando el Orquestador detecta consulta sobre norma desconocida
def handle_unknown_reference(self, reference: str):
    """
    El Orquestador llama esto cuando no encuentra una norma citada
    """
    logger.info(f"Unknown reference detected: {reference}")
    
    # Intentar descargar automáticamente
    task = {
        "operation": "search_and_download",
        "reference": reference,
        "priority": "high"
    }
    
    result = self.execute(task, {})
    
    if result["status"] == "success":
        return {
            "action": "downloaded",
            "document": result["document"],
            "message": f"Documento {reference} descargado e indexado"
        }
    else:
        return {
            "action": "failed",
            "error": result.get("error"),
            "message": f"No se pudo obtener {reference}"
        }
```

---

## 📊 MONITOREO Y REPORTES

### **Dashboard de Estado:**

```python
class DocumentManagerDashboard:
    """
    Dashboard para monitorear estado de base documental
    """
    
    def get_status_summary(self) -> Dict:
        return {
            "total_documents": self.db.documents.count(),
            "total_chunks": self.db.chunks.count(),
            "last_update": self._get_last_update(),
            "sources_status": self._check_sources_health(),
            "pending_downloads": self._get_pending_count(),
            "failed_downloads": self._get_failed_count(),
            "storage_used": self._get_storage_stats()
        }
    
    def _check_sources_health(self) -> List[Dict]:
        """Verifica salud de cada fuente"""
        health = []
        for source_id, source in LEGAL_SOURCES.items():
            try:
                response = requests.head(
                    source["url"], 
                    timeout=10,
                    verify=certifi.where()
                )
                health.append({
                    "source": source_id,
                    "name": source["name"],
                    "status": "online" if response.status_code == 200 else "degraded",
                    "last_check": datetime.utcnow().isoformat()
                })
            except Exception as e:
                health.append({
                    "source": source_id,
                    "name": source["name"],
                    "status": "offline",
                    "error": str(e)
                })
        return health
```

---

## 🚨 MANEJO DE ERRORES

### **Estrategia de Recuperación:**

```python
ERROR_HANDLING_STRATEGY = {
    "source_unavailable": {
        "action": "retry_with_backoff",
        "max_retries": 3,
        "notify_after": 3
    },
    "pdf_corrupted": {
        "action": "quarantine_and_report",
        "notify": True
    },
    "hash_mismatch": {
        "action": "re_download",
        "verify": True
    },
    "source_permanently_down": {
        "action": "switch_to_mirror",
        "notify": True
    }
}
```

---

## 🎯 INTEGRACIÓN CON SISTEMA MULTI-AGENTE

### **Comunicación con otros agentes:**

```
Orquestador → DocumentManager (solicita documento)
                    ↓
DocumentManager → Descarga/Valida/Indexa
                    ↓
DocumentManager → Notifica a Orquestador
                    ↓
Orquestador → Continúa con Agente Normativo
```

### **Eventos emitidos:**

```python
class DocumentEvents:
    DOCUMENT_DOWNLOADED = "document.downloaded"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_INVALID = "document.invalid"
    SOURCE_OFFLINE = "source.offline"
    INDEX_COMPLETED = "index.completed"
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### **Fase 1: Core (Semana 1)**
- [ ] Implementar clase DocumentManagerAgent
- [ ] Configurar fuentes legales
- [ ] Implementar descarga con validación
- [ ] Integrar con MongoDB existente

### **Fase 2: Procesamiento (Semana 2)**
- [ ] Implementar chunking por tipo de documento
- [ ] Integrar con sistema de embeddings existente
- [ ] Generar metadatos enriquecidos
- [ ] Tests de integridad

### **Fase 3: Automatización (Semana 3)**
- [ ] Schedule de tareas automáticas
- [ ] Sistema de notificaciones
- [ ] Dashboard de monitoreo
- [ ] Manejo de errores y recuperación

### **Fase 4: Integración (Semana 4)**
- [ ] Conectar con Orquestador
- [ ] API para solicitudes de documentos
- [ ] Sistema de "documento no encontrado"
- [ ] Tests end-to-end

---

## 💡 VENTAJAS DE ESTE AGENTE

1. **Autonomía** - Opera sin intervención humana
2. **Proactividad** - Detecta actualizaciones automáticamente
3. **Confiabilidad** - Validación multi-capa de documentos
4. **Eficiencia** - Reutiliza chunking inteligente por tipo
5. **Transparencia** - Audit trail completo
6. **Resiliencia** - Manejo de errores y recuperación

---

**¿Te gustaría que profundice en algún aspecto específico del DocumentManager?** 🚀