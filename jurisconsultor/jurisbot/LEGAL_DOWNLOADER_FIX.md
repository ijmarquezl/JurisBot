# 🔧 ANÁLISIS Y CORRECCIÓN: Descarga de Leyes Públicas
## JurisBot - web_downloader.py & legal_scraper.py

---

## 🚨 PROBLEMAS IDENTIFICADOS

### **CRÍTICOS (Seguridad/Estabilidad)**

| Problema | Línea | Severidad | Impacto |
|----------|-------|-----------|---------|
| **SSL Verification desactivado** | 35, 130, 158 | 🔴 Crítico | Vulnerable a MITM attacks |
| **Sin reintentos** | Todo | 🔴 Crítico | Falla ante errores de red temporales |
| **Sin rate limiting** | Todo | 🟡 Alto | Puede bloquear IPs por saturación |
| **Sin validación de PDF** | 168 | 🟡 Alto | Puede procesar archivos corruptos |
| **Conexiones MongoDB sin cerrar** | 56, 97 | 🟡 Alto | Fuga de conexiones |

### **MEDIOS (Funcionalidad)**

| Problema | Línea | Severidad | Impacto |
|----------|-------|-----------|---------|
| **Scraper específico frágil** | 48 | 🟡 Alto | Se rompe si cambia el sitio |
| **Chunking rígido** | 76 | 🟡 Medio | Solo divide por "Artículo" |
| **Sin timeout configurable** | 35 | 🟡 Medio | 30s fijo puede ser insuficiente |
| **Sin logging de progreso** | Todo | 🟢 Bajo | No se ve avance en descargas largas |

---

## 🔒 PROBLEMA CRÍTICO: SSL Verification

### **Código Problemático:**
```python
# Líneas 35, 130, 158 - web_downloader.py
response = requests.get(url, timeout=30, headers=headers, verify=False)
```

### **Riesgo:**
- **Ataque Man-in-the-Middle (MITM)**
- Descarga de documentos falsificados
- Compromiso de integridad legal

### **Solución:**
```python
import certifi

# Opción 1: Usar certificados actualizados
response = requests.get(
    url, 
    timeout=30, 
    headers=headers, 
    verify=certifi.where()  # Certificados actualizados
)

# Opción 2: Si el sitio tiene certificado autofirmado (no recomendado)
# Solo para desarrollo local
verify_ssl = os.getenv('VERIFY_SSL', 'true').lower() == 'true'
response = requests.get(url, timeout=30, headers=headers, verify=verify_ssl)
```

---

## 🔄 PROBLEMA: Sin Sistema de Reintentos

### **Código Actual:**
```python
# Falla inmediatamente ante cualquier error
def download_pdf(pdf_url: str) -> bytes:
    response = requests.get(pdf_url, timeout=30, headers=headers, verify=False)
    response.raise_for_status()
    return response.content
```

### **Solución con Reintentos Exponenciales:**
```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, backoff_factor=2):
    """Decorador para reintentos con backoff exponencial"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3, backoff_factor=2)
def download_pdf(pdf_url: str) -> bytes:
    """Downloads a PDF with retry logic"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(
        pdf_url, 
        timeout=30, 
        headers=headers, 
        verify=certifi.where()
    )
    response.raise_for_status()
    
    # Validar que sea realmente un PDF
    if not response.content.startswith(b'%PDF'):
        raise ValueError(f"Downloaded file is not a valid PDF: {pdf_url}")
    
    return response.content
```

---

## ⏱️ PROBLEMA: Sin Rate Limiting

### **Solución:**
```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    """Rate limiter para respetar servidores"""
    
    def __init__(self, requests_per_minute=10):
        self.requests_per_minute = requests_per_minute
        self.requests = []
    
    def wait_if_needed(self):
        """Espera si se excede el límite de requests"""
        now = datetime.now()
        # Limpiar requests antiguos (> 1 minuto)
        self.requests = [r for r in self.requests if now - r < timedelta(minutes=1)]
        
        if len(self.requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.requests[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.requests.append(now)

# Uso
rate_limiter = RateLimiter(requests_per_minute=6)  # 1 cada 10 segundos

def run_scraper():
    for source in sources:
        rate_limiter.wait_if_needed()  # Respetar límites
        process_source(source)
```

---

## 📄 PROBLEMA: Sin Validación de PDF

### **Solución:**
```python
from pypdf import PdfReader
import io

def validate_pdf(pdf_content: bytes) -> bool:
    """Valida que el contenido sea un PDF válido y legible"""
    try:
        # Verificar header de PDF
        if not pdf_content.startswith(b'%PDF'):
            logger.error("Invalid PDF header")
            return False
        
        # Intentar leer con PyPDF
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        
        # Verificar que tenga páginas
        if len(reader.pages) == 0:
            logger.error("PDF has no pages")
            return False
        
        # Verificar que se pueda extraer texto de al menos una página
        for i, page in enumerate(reader.pages[:3]):  # Primeras 3 páginas
            try:
                text = page.extract_text()
                if text and len(text.strip()) > 0:
                    return True
            except Exception as e:
                logger.warning(f"Could not extract text from page {i}: {e}")
        
        logger.error("PDF appears to be image-based or corrupted")
        return False
        
    except Exception as e:
        logger.error(f"PDF validation failed: {e}")
        return False

# Uso en download_pdf
def download_pdf(pdf_url: str) -> bytes:
    content = _download_with_retry(pdf_url)
    if not validate_pdf(content):
        raise ValueError(f"Downloaded file is not a valid PDF: {pdf_url}")
    return content
```

---

## 🗄️ PROBLEMA: Conexiones MongoDB sin Cerrar

### **Código Problemático:**
```python
# Líneas 56, 97 - mongo_client.close() está comentado
def process_single_document(...):
    mongo_client = get_mongo_client()
    # ... uso ...
    finally:
        # mongo_client.close()  # COMENTADO - FUGA DE CONEXIONES
```

### **Solución:**
```python
from contextlib import contextmanager

@contextmanager
def mongo_connection():
    """Context manager para manejar conexiones MongoDB"""
    mongo_client = None
    try:
        mongo_client = get_mongo_client()
        db = mongo_client.jurisconsultor
        yield db
    finally:
        if mongo_client:
            mongo_client.close()

# Uso
def process_single_document(pdf_path: str, db_type: str, company_id: str = None):
    with mongo_connection() as db:
        documents_collection = db.documents
        # ... procesamiento ...
```

---

## 🔧 PROBLEMA: Chunking Rígido

### **Código Actual:**
```python
# Solo divide por "Artículo" - pierde contenido sin este patrón
chunks = re.split(r'(?=Artículo \d+\.?-?)', text)
```

### **Solución Flexible:**
```python
import re

def smart_chunking(text: str, min_chunk_size: int = 100, max_chunk_size: int = 2000) -> list:
    """
    Divide texto en chunks inteligentes considerando:
    - Artículos
    - Capítulos
    - Secciones
    - Párrafos (fallback)
    """
    # Patrones de división en orden de prioridad
    patterns = [
        r'(?=TÍTULO [IVX]+)',           # Títulos romanos
        r'(?=CAPÍTULO [IVX]+)',          # Capítulos romanos
        r'(?=SECCIÓN [IVX]+)',           # Secciones
        r'(?=Artículo \d+[\.-]?)',       # Artículos
        r'(?=\n\s*\n)',                  # Párrafos dobles (fallback)
    ]
    
    chunks = [text]
    
    for pattern in patterns:
        new_chunks = []
        for chunk in chunks:
            if len(chunk) > max_chunk_size:
                split_chunks = re.split(pattern, chunk)
                new_chunks.extend([c.strip() for c in split_chunks if c.strip()])
            else:
                new_chunks.append(chunk)
        chunks = new_chunks
    
    # Filtrar chunks muy pequeños y limpiar
    processed_chunks = [
        c.strip() for c in chunks 
        if len(c.strip()) >= min_chunk_size
    ]
    
    return processed_chunks

# Uso
def process_single_document(pdf_path: str, ...):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    
    chunks = smart_chunking(text, min_chunk_size=50, max_chunk_size=1500)
    # ... continuar procesamiento ...
```

---

## 📊 CÓDIGO COMPLETO CORREGIDO

### **Nuevo archivo: `enhanced_web_downloader.py`**

```python
"""
Enhanced Web Downloader for JurisBot
Fixes: SSL verification, retry logic, rate limiting, PDF validation
"""

import os
import re
import time
import requests
import hashlib
import certifi
import logging
from io import BytesIO
from functools import wraps
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from pypdf import PdfReader
from utils import get_mongo_client
from legal_scraper import process_single_document, delete_document_by_source

logger = logging.getLogger(__name__)

# Configuration
SOURCES_COLLECTION = "scraping_sources"
PDF_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'documentos_legales'))
VERIFY_SSL = os.getenv('VERIFY_SSL', 'true').lower() == 'true'
MAX_RETRIES = int(os.getenv('DOWNLOAD_MAX_RETRIES', '3'))
BACKOFF_FACTOR = int(os.getenv('DOWNLOAD_BACKOFF_FACTOR', '2'))
REQUESTS_PER_MINUTE = int(os.getenv('DOWNLOAD_RATE_LIMIT', '6'))


class RateLimiter:
    """Rate limiter to respect server limits"""
    
    def __init__(self, requests_per_minute: int = 6):
        self.requests_per_minute = requests_per_minute
        self.requests: List[datetime] = []
    
    def wait_if_needed(self):
        """Wait if rate limit exceeded"""
        now = datetime.now()
        self.requests = [r for r in self.requests if now - r < timedelta(minutes=1)]
        
        if len(self.requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.requests[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Sleeping {sleep_time:.1f}s")
                time.sleep(max(sleep_time, 1))
        
        self.requests.append(now)


def retry_with_backoff(max_retries: int = 3, backoff_factor: int = 2):
    """Decorator for exponential backoff retry"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, ValueError) as e:
                    if attempt == max_retries - 1:
                        logger.error(f"All {max_retries} attempts failed: {e}")
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator


def validate_pdf(pdf_content: bytes) -> bool:
    """Validate PDF content"""
    try:
        if not pdf_content.startswith(b'%PDF'):
            logger.error("Invalid PDF header")
            return False
        
        pdf_file = BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        
        if len(reader.pages) == 0:
            logger.error("PDF has no pages")
            return False
        
        # Check extractable text
        for i, page in enumerate(reader.pages[:3]):
            try:
                text = page.extract_text()
                if text and len(text.strip()) > 10:
                    return True
            except Exception as e:
                logger.warning(f"Page {i} text extraction failed: {e}")
        
        logger.error("PDF appears image-based or corrupted")
        return False
        
    except Exception as e:
        logger.error(f"PDF validation failed: {e}")
        return False


@retry_with_backoff(max_retries=MAX_RETRIES, backoff_factor=BACKOFF_FACTOR)
def download_pdf(pdf_url: str) -> bytes:
    """Download PDF with validation and retry"""
    logger.info(f"Downloading PDF from {pdf_url}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(
        pdf_url,
        timeout=60,
        headers=headers,
        verify=certifi.where() if VERIFY_SSL else False
    )
    response.raise_for_status()
    
    if not validate_pdf(response.content):
        raise ValueError(f"Invalid PDF downloaded from {pdf_url}")
    
    logger.info(f"Successfully downloaded and validated PDF ({len(response.content)} bytes)")
    return response.content


def calculate_hash(data: bytes) -> str:
    """Calculate SHA256 hash"""
    return hashlib.sha256(data).hexdigest()


def run_enhanced_scraper():
    """Enhanced scraper with all fixes"""
    logger.info("Starting enhanced web scraper...")
    
    mongo_client = get_mongo_client()
    db_name = os.getenv("MONGO_DB_NAME", "jurisconsultor")
    db = mongo_client[db_name]
    sources_collection = db[SOURCES_COLLECTION]
    
    rate_limiter = RateLimiter(requests_per_minute=REQUESTS_PER_MINUTE)
    
    sources = list(sources_collection.find({"url": {"$ne": None}}))
    logger.info(f"Found {len(sources)} sources to process")
    
    success_count = 0
    failed_count = 0
    
    for i, source in enumerate(sources, 1):
        source_id = source["_id"]
        logger.info(f"[{i}/{len(sources)}] Processing: {source['name']}")
        
        try:
            rate_limiter.wait_if_needed()
            
            # Get PDF URL (simplified for example)
            pdf_url = source.get('pdf_direct_url')
            if not pdf_url:
                logger.warning(f"No PDF URL for {source['name']}")
                failed_count += 1
                continue
            
            # Download with retry and validation
            pdf_content = download_pdf(pdf_url)
            new_hash = calculate_hash(pdf_content)
            
            # Check if changed
            if new_hash == source.get('last_known_hash'):
                logger.info(f"'{source['name']}' is up to date")
                sources_collection.update_one(
                    {"_id": source_id},
                    {"$set": {"status": "up_to_date", "last_checked": datetime.utcnow()}}
                )
                continue
            
            # Process update
            local_filename = source.get('local_filename')
            if not local_filename:
                raise ValueError(f"Missing local_filename for {source['name']}")
            
            # Save new file
            local_pdf_path = os.path.join(PDF_DIRECTORY, local_filename)
            os.makedirs(PDF_DIRECTORY, exist_ok=True)
            
            with open(local_pdf_path, 'wb') as f:
                f.write(pdf_content)
            
            # Delete old and process new
            delete_document_by_source(local_filename, 'public', None)
            process_single_document(local_pdf_path, 'public', None)
            
            # Update source record
            sources_collection.update_one(
                {"_id": source_id},
                {
                    "$set": {
                        "status": "success",
                        "last_known_hash": new_hash,
                        "last_downloaded": datetime.utcnow(),
                        "error_message": None
                    }
                }
            )
            
            success_count += 1
            logger.info(f"✓ Successfully updated '{source['name']}'")
            
        except Exception as e:
            logger.error(f"✗ Failed to process '{source['name']}': {e}", exc_info=True)
            sources_collection.update_one(
                {"_id": source_id},
                {"$set": {"status": "failed", "error_message": str(e)[:500]}}
            )
            failed_count += 1
    
    mongo_client.close()
    
    logger.info(f"Scraper complete: {success_count} success, {failed_count} failed")
    return {"success": success_count, "failed": failed_count}


if __name__ == "__main__":
    run_enhanced_scraper()
```

---

## 🧪 TESTS RECOMENDADOS

```python
# tests/test_web_downloader.py
import pytest
from unittest.mock import Mock, patch
from enhanced_web_downloader import validate_pdf, download_pdf, RateLimiter

def test_validate_pdf_valid():
    """Test valid PDF validation"""
    valid_pdf = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\ntrailer\n<<\n/Size 1\n/Root 1 0 R\n>>\nstartxref\n9\n%%EOF'
    assert validate_pdf(valid_pdf) == False  # No pages, but header valid

def test_validate_pdf_invalid():
    """Test invalid PDF rejection"""
    invalid_pdf = b'Not a PDF file'
    assert validate_pdf(invalid_pdf) == False

def test_rate_limiter():
    """Test rate limiting"""
    limiter = RateLimiter(requests_per_minute=2)
    limiter.wait_if_needed()  # Should not block
    limiter.wait_if_needed()  # Should not block
    # Third call might block if within same minute

def test_download_pdf_retry(mocker):
    """Test retry mechanism"""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = [
            requests.ConnectionError("Network error"),
            Mock(content=b'%PDF-1.4...', status_code=200)
        ]
        # Should retry and succeed on second attempt
```

---

## 📋 CHECKLIST DE IMPLEMENTACIÓN

### **Inmediato (Seguridad)**
- [ ] Reemplazar `verify=False` con `certifi.where()`
- [ ] Agregar variable de entorno `VERIFY_SSL`
- [ ] Implementar sistema de reintentos
- [ ] Agregar validación de PDF

### **Corto plazo (Estabilidad)**
- [ ] Implementar RateLimiter
- [ ] Usar context managers para MongoDB
- [ ] Mejorar chunking flexible
- [ ] Agregar logging de progreso

### **Mediano plazo (Robustez)**
- [ ] Tests unitarios
- [ ] Monitoreo de scraper
- [ ] Alertas de fallos
- [ ] Dashboard de estado

---

## 🎯 RESUMEN

| Problema | Solución | Prioridad |
|----------|----------|-----------|
| SSL `verify=False` | Usar `certifi.where()` | 🔴 Crítico |
| Sin reintentos | Decorador `retry_with_backoff` | 🔴 Crítico |
| Sin rate limiting | Clase `RateLimiter` | 🟡 Alta |
| Sin validación PDF | Función `validate_pdf()` | 🟡 Alta |
| Conexiones sin cerrar | Context manager `mongo_connection` | 🟡 Alta |
| Chunking rígido | `smart_chunking()` flexible | 🟢 Media |

**Tiempo estimado de implementación:** 2-3 días
**Riesgo si no se corrige:** Alto (seguridad + estabilidad)

---

**¿Listo para implementar estas correcciones?** 🚀