# 🔍 AGENTE DOCUMENT MANAGER - MÓDULO DE SCRAPING
## Descubrimiento y Extracción de Documentos Legales

---

## 🎯 CAPACIDADES DE SCRAPING

El Agente DocumentManager debe ser capaz de:

1. **Navegar sitios web** de fuentes legales
2. **Detectar enlaces** a PDFs, DOCX, y HTML
3. **Extraer contenido** directamente de páginas web
4. **Manejar paginación** en listados de documentos
5. **Identificar metadatos** (fecha, tipo, jurisdicción)
6. **Descargar múltiples formatos**

---

## 🕷️ ARQUITECTURA DE SCRAPING

```
┌─────────────────────────────────────────────────────────────┐
│              DOCUMENT DISCOVERY ENGINE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   Crawler   │───▶│  Parser     │───▶│ Downloader  │    │
│  │   Engine    │    │  Engine     │    │  Engine     │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Format Handlers                        │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  │   │
│  │  │  PDF   │  │ DOCX   │  │  HTML  │  │  TXT   │  │   │
│  │  │Handler │  │Handler │  │Handler │  │Handler │  │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📄 SCRAPERS ESPECÍFICOS POR FUENTE

### **1. Diario Oficial de la Federación (DOF)**

```python
class DOFScraper(BaseScraper):
    """
    Scraper especializado para dof.gob.mx
    """
    
    BASE_URL = "https://www.dof.gob.mx"
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_by_date(self, date: datetime) -> List[DocumentInfo]:
        """
        Obtiene todos los documentos publicados en una fecha específica
        """
        date_str = date.strftime("%Y%m%d")
        url = f"{self.BASE_URL}/nota_detalle.php?codigo={date_str}"
        
        logger.info(f"Scraping DOF for date: {date.strftime('%Y-%m-%d')}")
        
        try:
            response = self.session.get(url, timeout=30, verify=certifi.where())
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            documents = []
            
            # Buscar secciones del DOF
            sections = {
                "Primera Sección": "legislacion",
                "Segunda Sección": "administrativo", 
                "Tercera Sección": "judicial",
                "Cuarta Sección": "varios"
            }
            
            for section_name, doc_type in sections.items():
                section = soup.find('h3', string=re.compile(section_name))
                if section:
                    # Buscar enlaces a PDFs en esta sección
                    pdf_links = section.find_next_siblings('a', href=re.compile(r'.*\.pdf$'))
                    
                    for link in pdf_links[:20]:  # Limitar por sección
                        doc_info = self._extract_document_info(link, date, doc_type)
                        if doc_info:
                            documents.append(doc_info)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error scraping DOF for {date}: {e}")
            return []
    
    def _extract_document_info(self, link, date, doc_type) -> Optional[DocumentInfo]:
        """Extrae metadatos de un enlace"""
        href = link.get('href', '')
        if not href:
            return None
        
        pdf_url = urljoin(self.BASE_URL, href)
        
        # Extraer título
        title = link.get_text(strip=True)
        if not title:
            title = link.get('title', 'Documento sin título')
        
        # Detectar tipo específico
        specific_type = self._classify_dof_document(title)
        
        return DocumentInfo(
            url=pdf_url,
            title=title,
            source="dof",
            source_type=doc_type,
            document_type=specific_type,
            publication_date=date,
            format="pdf"
        )
    
    def _classify_dof_document(self, title: str) -> str:
        """Clasifica el tipo de documento por su título"""
        title_lower = title.lower()
        
        patterns = {
            "decreto": r'decreto',
            "ley": r'ley\s+',
            "reglamento": r'reglamento',
            "acuerdo": r'acuerdo',
            "circular": r'circular',
            "resolucion": r'resolución',
            "nom": r'n[oó]m-\d+',  # Norma Oficial Mexicana
            "convocatoria": r'convocatoria',
            "nombramiento": r'nombramiento'
        }
        
        for doc_type, pattern in patterns.items():
            if re.search(pattern, title_lower):
                return doc_type
        
        return "otro"
    
    def download_document(self, doc_info: DocumentInfo) -> DownloadResult:
        """Descarga documento con metadatos completos"""
        return self._download_with_validation(doc_info)
```

---

### **2. Suprema Corte de Justicia (SCJN - Tesis)**

```python
class SCJNScraper(BaseScraper):
    """
    Scraper para tesis de jurisprudencia SCJN
    """
    
    BASE_URL = "https://www.scjn.gob.mx"
    
    def scrape_tesis(self, filters: Dict = None) -> List[DocumentInfo]:
        """
        Obtiene tesis de jurisprudencia
        """
        # La SCJN tiene buscador por materia, tipo, fecha
        search_url = f"{self.BASE_URL}/jurisprudencia/busqueda"
        
        params = {
            "tipo": filters.get("tipo", "jurisprudencia"),  # jurisprudencia|aislada
            "materia": filters.get("materia", ""),
            "fecha_inicio": filters.get("fecha_inicio", ""),
            "fecha_fin": filters.get("fecha_fin", "")
        }
        
        documents = []
        page = 1
        
        while True:
            params["pagina"] = page
            
            try:
                response = self.session.get(
                    search_url, 
                    params=params, 
                    timeout=30,
                    verify=certifi.where()
                )
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar resultados
                results = soup.find_all('div', class_='resultado-tesis')
                
                if not results:
                    break
                
                for result in results:
                    doc_info = self._parse_tesis_result(result)
                    if doc_info:
                        documents.append(doc_info)
                
                # Verificar si hay más páginas
                next_page = soup.find('a', text=re.compile('Siguiente'))
                if not next_page:
                    break
                
                page += 1
                self.rate_limiter.wait_if_needed()
                
            except Exception as e:
                logger.error(f"Error scraping SCJN page {page}: {e}")
                break
        
        return documents
    
    def _parse_tesis_result(self, result_html) -> Optional[DocumentInfo]:
        """Parsea HTML de resultado de tesis"""
        try:
            # Extraer número de tesis
            numero = result_html.find('span', class_='numero-tesis')
            numero_text = numero.get_text(strip=True) if numero else ""
            
            # Extraer materia
            materia = result_html.find('span', class_='materia')
            materia_text = materia.get_text(strip=True) if materia else ""
            
            # Extraer enlace a PDF
            pdf_link = result_html.find('a', href=re.compile(r'.*\.pdf$'))
            if not pdf_link:
                return None
            
            pdf_url = urljoin(self.BASE_URL, pdf_link['href'])
            
            # Extraer fecha
            fecha = result_html.find('span', class_='fecha')
            fecha_text = fecha.get_text(strip=True) if fecha else ""
            
            return DocumentInfo(
                url=pdf_url,
                title=f"Tesis {numero_text} - {materia_text}",
                source="scjn",
                source_type="jurisprudencia",
                document_type="tesis",
                publication_date=self._parse_date(fecha_text),
                format="pdf",
                metadata={
                    "numero_tesis": numero_text,
                    "materia": materia_text
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing tesis result: {e}")
            return None
```

---

### **3. Congreso de la Unión (Leyes Federales)**

```python
class CongresoScraper(BaseScraper):
    """
    Scraper para leyes federales del Congreso
    """
    
    BASE_URL = "http://www.diputados.gob.mx/LeyesBiblio"
    
    def scrape_all_laws(self) -> List[DocumentInfo]:
        """
        Obtiene catálogo de todas las leyes federales
        """
        url = f"{self.BASE_URL}/index.htm"
        
        try:
            response = self.session.get(url, timeout=30, verify=certifi.where())
            soup = BeautifulSoup(response.content, 'html.parser')
            
            documents = []
            
            # Buscar tabla de leyes
            law_links = soup.find_all('a', href=re.compile(r'.*\.pdf$|.*\.docx?$'))
            
            for link in law_links:
                doc_info = self._extract_law_info(link)
                if doc_info:
                    documents.append(doc_info)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error scraping Congreso: {e}")
            return []
    
    def _extract_law_info(self, link) -> Optional[DocumentInfo]:
        """Extrae información de una ley"""
        href = link.get('href', '')
        if not href:
            return None
        
        # Determinar formato
        format_type = "pdf" if href.endswith('.pdf') else "docx"
        
        # Construir URL completa
        if href.startswith('http'):
            doc_url = href
        else:
            doc_url = urljoin(self.BASE_URL, href)
        
        # Extraer nombre de la ley
        title = link.get_text(strip=True)
        if not title:
            # Intentar extraer del filename
            title = os.path.basename(href).replace('_', ' ').replace('-', ' ')
            title = os.path.splitext(title)[0]
        
        # Detectar si es código o ley ordinaria
        doc_type = "codigo" if "codigo" in title.lower() else "ley"
        
        return DocumentInfo(
            url=doc_url,
            title=title,
            source="congreso",
            source_type="federal",
            document_type=doc_type,
            format=format_type
        )
```

---

### **4. Scraper Genérico para Sitios Estatales**

```python
class GenericLegalScraper(BaseScraper):
    """
    Scraper configurable para sitios de gobierno estatal
    """
    
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.base_url = config['base_url']
        
    def scrape(self) -> List[DocumentInfo]:
        """
        Scrapea según configuración proporcionada
        """
        documents = []
        
        for page_config in self.config.get('pages', []):
            page_docs = self._scrape_page(page_config)
            documents.extend(page_docs)
        
        return documents
    
    def _scrape_page(self, page_config: Dict) -> List[DocumentInfo]:
        """Scrapea una página específica"""
        url = urljoin(self.base_url, page_config['path'])
        
        try:
            response = self.session.get(url, timeout=30, verify=certifi.where())
            soup = BeautifulSoup(response.content, 'html.parser')
            
            documents = []
            
            # Buscar según selectores configurados
            for selector in page_config.get('document_selectors', []):
                elements = soup.select(selector)
                
                for elem in elements:
                    doc_info = self._parse_element(elem, page_config)
                    if doc_info:
                        documents.append(doc_info)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return []
    
    def _parse_element(self, element, config) -> Optional[DocumentInfo]:
        """Parsea elemento HTML según reglas de configuración"""
        try:
            # Extraer enlace
            link = element.find('a') if element.name != 'a' else element
            if not link:
                return None
            
            href = link.get('href', '')
            if not href:
                return None
            
            # Filtrar por extensiones permitidas
            allowed_exts = config.get('allowed_extensions', ['.pdf', '.docx', '.doc'])
            if not any(href.lower().endswith(ext) for ext in allowed_exts):
                return None
            
            doc_url = urljoin(self.base_url, href)
            
            # Extraer título
            title_selectors = config.get('title_selectors', ['.title', 'h3', 'h2', 'a'])
            title = self._extract_text(element, title_selectors)
            
            # Extraer fecha si está disponible
            date_selectors = config.get('date_selectors', ['.date', '.fecha', 'time'])
            date_text = self._extract_text(element, date_selectors)
            
            return DocumentInfo(
                url=doc_url,
                title=title or "Documento sin título",
                source=config.get('source_name', 'generic'),
                format=self._detect_format(href),
                publication_date=self._parse_date(date_text) if date_text else None
            )
            
        except Exception as e:
            logger.error(f"Error parsing element: {e}")
            return None
```

---

## 📥 MANEJO DE MÚLTIPLES FORMATOS

### **Descargador Universal:**

```python
class UniversalDownloader:
    """
    Descarga y procesa múltiples formatos de documentos
    """
    
    SUPPORTED_FORMATS = ['pdf', 'docx', 'doc', 'html', 'txt']
    
    def download(self, doc_info: DocumentInfo) -> DownloadResult:
        """
        Descarga documento según su formato
        """
        format_handlers = {
            'pdf': self._handle_pdf,
            'docx': self._handle_docx,
            'doc': self._handle_doc,
            'html': self._handle_html,
            'txt': self._handle_txt
        }
        
        handler = format_handlers.get(doc_info.format.lower())
        if not handler:
            return DownloadResult(
                success=False,
                error=f"Formato no soportado: {doc_info.format}"
            )
        
        return handler(doc_info)
    
    def _handle_pdf(self, doc_info: DocumentInfo) -> DownloadResult:
        """Descarga y valida PDF"""
        try:
            response = requests.get(
                doc_info.url, 
                timeout=60,
                headers={'User-Agent': 'Mozilla/5.0'},
                verify=certifi.where()
            )
            response.raise_for_status()
            
            content = response.content
            
            # Validar que sea PDF
            if not content.startswith(b'%PDF'):
                return DownloadResult(
                    success=False,
                    error="El archivo descargado no es un PDF válido"
                )
            
            # Guardar temporalmente
            temp_path = self._save_temp(content, '.pdf')
            
            # Extraer texto para preview
            text_preview = self._extract_pdf_text(temp_path, max_pages=3)
            
            return DownloadResult(
                success=True,
                file_path=temp_path,
                content=content,
                text_preview=text_preview,
                metadata={
                    "size": len(content),
                    "pages": self._count_pdf_pages(temp_path)
                }
            )
            
        except Exception as e:
            return DownloadResult(success=False, error=str(e))
    
    def _handle_docx(self, doc_info: DocumentInfo) -> DownloadResult:
        """Descarga y procesa DOCX"""
        try:
            response = requests.get(
                doc_info.url,
                timeout=60,
                headers={'User-Agent': 'Mozilla/5.0'},
                verify=certifi.where()
            )
            response.raise_for_status()
            
            content = response.content
            
            # Validar DOCX (ZIP con estructura específica)
            if not content.startswith(b'PK'):
                return DownloadResult(
                    success=False,
                    error="El archivo no es un DOCX válido"
                )
            
            # Guardar temporalmente
            temp_path = self._save_temp(content, '.docx')
            
            # Extraer texto
            text_content = self._extract_docx_text(temp_path)
            
            return DownloadResult(
                success=True,
                file_path=temp_path,
                content=content,
                text_preview=text_content[:2000],
                metadata={
                    "size": len(content),
                    "word_count": len(text_content.split())
                }
            )
            
        except Exception as e:
            return DownloadResult(success=False, error=str(e))
    
    def _handle_html(self, doc_info: DocumentInfo) -> DownloadResult:
        """Scrapea contenido HTML directamente"""
        try:
            response = requests.get(
                doc_info.url,
                timeout=30,
                headers={'User-Agent': 'Mozilla/5.0'},
                verify=certifi.where()
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Limpiar HTML (quitar scripts, styles)
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Extraer texto
            text = soup.get_text(separator='\n', strip=True)
            
            # Limpiar espacios en blanco
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)
            
            return DownloadResult(
                success=True,
                content=clean_text.encode('utf-8'),
                text_preview=clean_text[:2000],
                metadata={
                    "source_url": doc_info.url,
                    "title": soup.title.string if soup.title else "Sin título"
                }
            )
            
        except Exception as e:
            return DownloadResult(success=False, error=str(e))
```

---

## 🔄 SISTEMA DE PAGINACIÓN

```python
class PaginationHandler:
    """
    Maneja paginación en sitios de listados legales
    """
    
    def crawl_paginated(self, start_url: str, config: Dict) -> List[DocumentInfo]:
        """
        Recorre todas las páginas de un listado
        """
        all_documents = []
        current_url = start_url
        page = 1
        
        while current_url and page <= config.get('max_pages', 100):
            logger.info(f"Crawling page {page}: {current_url}")
            
            try:
                response = requests.get(
                    current_url,
                    timeout=30,
                    headers={'User-Agent': 'Mozilla/5.0'},
                    verify=certifi.where()
                )
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraer documentos de esta página
                page_docs = self._extract_from_page(soup, config)
                all_documents.extend(page_docs)
                
                # Buscar enlace a siguiente página
                next_link = self._find_next_page(soup, config, current_url)
                current_url = next_link
                
                page += 1
                
                # Rate limiting
                time.sleep(config.get('delay_between_pages', 2))
                
            except Exception as e:
                logger.error(f"Error on page {page}: {e}")
                break
        
        return all_documents
    
    def _find_next_page(self, soup, config, current_url) -> Optional[str]:
        """Encuentra URL de siguiente página"""
        # Estrategias comunes de paginación
        strategies = [
            # Enlace con texto "Siguiente" o "Next"
            lambda s: s.find('a', text=re.compile(r'(Siguiente|Next|»)', re.I)),
            # Enlace con clase "next"
            lambda s: s.find('a', class_='next'),
            # Enlace con rel="next"
            lambda s: s.find('a', rel='next'),
            # Selector CSS configurable
            lambda s: s.select_one(config.get('next_page_selector', ''))
        ]
        
        for strategy in strategies:
            try:
                link = strategy(soup)
                if link and link.get('href'):
                    return urljoin(current_url, link['href'])
            except:
                continue
        
        return None
```

---

## 🛡️ MANEJO DE ERRORES Y ROBUSTEZ

```python
class RobustScraper:
    """
    Scraper con manejo robusto de errores
    """
    
    @retry_with_backoff(max_retries=3)
    def fetch_with_fallback(self, url: str) -> Optional[requests.Response]:
        """
        Intenta obtener URL con múltiples estrategias
        """
        # Intento 1: HTTPS con verificación
        try:
            if url.startswith('http://'):
                https_url = url.replace('http://', 'https://')
                response = requests.get(
                    https_url, 
                    timeout=30, 
                    verify=certifi.where()
                )
                if response.status_code == 200:
                    return response
        except:
            pass
        
        # Intento 2: URL original
        try:
            response = requests.get(
                url, 
                timeout=30,
                verify=certifi.where()
            )
            if response.status_code == 200:
                return response
        except:
            pass
        
        # Intento 3: Sin verificación SSL (último recurso)
        try:
            logger.warning(f"Attempting download without SSL verification: {url}")
            response = requests.get(
                url,
                timeout=30,
                verify=False
            )
            if response.status_code == 200:
                return response
        except Exception as e:
            logger.error(f"All fetch attempts failed for {url}: {e}")
        
        return None
    
    def detect_site_structure(self, url: str) -> Dict:
        """
        Analiza estructura de sitio para configurar scraper
        """
        try:
            response = requests.get(url, timeout=30, verify=certifi.where())
            soup = BeautifulSoup(response.content, 'html.parser')
            
            analysis = {
                "has_pagination": bool(soup.find('a', text=re.compile(r'(Siguiente|Next)'))),
                "document_links": len(soup.find_all('a', href=re.compile(r'\.(pdf|docx?)$'))),
                "requires_javascript": len(soup.find_all('script')) > 10,
                "has_search_form": bool(soup.find('form', action=re.compile(r'(search|buscar)')))
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing site structure: {e}")
            return {}
```

---

## 📋 CONFIGURACIÓN DE FUENTES

```python
SCRAPER_CONFIGS = {
    "dof": {
        "name": "Diario Oficial de la Federación",
        "scraper_class": "DOFScraper",
        "update_frequency": "daily",
        "requires_auth": False,
        "rate_limit": 6,  # requests per minute
        "supported_formats": ["pdf"]
    },
    "scjn": {
        "name": "Suprema Corte de Justicia",
        "scraper_class": "SCJNScraper", 
        "update_frequency": "weekly",
        "requires_auth": False,
        "rate_limit": 10,
        "supported_formats": ["pdf"]
    },
    "congreso": {
        "name": "Congreso de la Unión",
        "scraper_class": "CongresoScraper",
        "update_frequency": "weekly",
        "requires_auth": False,
        "rate_limit": 6,
        "supported_formats": ["pdf", "docx", "doc"]
    },
    "codigo_civil_qr": {
        "name": "Código Civil Quintana Roo",
        "scraper_class": "GenericLegalScraper",
        "base_url": "https://www.qroo.gob.mx/...",
        "config": {
            "pages": [
                {
                    "path": "/codigo-civil",
                    "document_selectors": [".document-link", "a[href$='.pdf']"],
                    "title_selectors": ["h3", ".doc-title"]
                }
            ]
        }
    }
}
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### **Core Scraping:**
- [ ] Implementar DOFScraper
- [ ] Implementar SCJNScraper  
- [ ] Implementar CongresoScraper
- [ ] Implementar GenericLegalScraper
- [ ] Sistema de paginación
- [ ] Rate limiting por fuente

### **Formatos:**
- [ ] Handler de PDFs
- [ ] Handler de DOCX/DOC
- [ ] Handler de HTML
- [ ] Validación de integridad
- [ ] Extracción de texto

### **Robustez:**
- [ ] Sistema de reintentos
- [ ] Fallback de conexión
- [ ] Manejo de errores
- [ ] Logging detallado
- [ ] Detección de cambios en sitios

---

**¿Te gustaría que profundice en algún scraper específico o en el sistema de detección de cambios?** 🕷️