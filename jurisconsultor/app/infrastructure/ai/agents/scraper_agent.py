import logging
import asyncio
from typing import TypedDict, List, Optional, Annotated
import operator
from datetime import datetime
import os
import json
from slugify import slugify

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

from infrastructure.ai.browser_tools import extract_interactive_elements, resolve_law_pdf_url
from infrastructure.utils.utils import get_mongo_client
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama

logger = logging.getLogger(__name__)

# --- State Definition ---
class LawItem(TypedDict):
    name: str
    selector_id: str
    href: str # NEW: capture the link
    original_url: str # Main page URL
    pdf_url: Optional[str]
    status: str # 'found', 'processed', 'failed'

class ScraperState(TypedDict):
    url: str
    scraper_type: str # e.g., 'discovery_ordenjuridico'
    laws: List[LawItem]
    logs: List[str]
    current_step: str

# --- LLM Factory ---
def get_llm():
    """Factory to get the configured LLM instance."""
    # Try to load from env vars compatible with OpenAI/Groq
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("LLM_URL") or os.getenv("OPENAI_API_BASE")
    model_name = os.getenv("LLM_MODEL_NAME") or os.getenv("MODEL", "llama3")

    if api_key:
        return ChatOpenAI(
            model=model_name,
            temperature=0,
            openai_api_key=api_key,
            openai_api_base=base_url
        )
    else:
        # Fallback to local Ollama if no keys
        return ChatOllama(
            base_url="http://10.29.93.56:11434",
            model="llama3",
            temperature=0
        )

# --- Nodes ---

async def scan_page_node(state: ScraperState):
    """
    Navigates to the page and extracts all 'a' tags that look like they could be laws.
    """
    url = state['url']
    scraper_type = state.get('scraper_type', 'generic')
    logger.info(f"Scanning {url} with strategy {scraper_type}...")

    # --- Estrategias específicas por sitio (HTTP directo, sin navegador) ---
    # Congreso de Aguascalientes: /descargarPdf/<id> (sin extensión)
    if scraper_type == 'discovery_congresoags':
        from scripts.discover_congresoags import scrape_congresoags
        laws_data = scrape_congresoags(url)
        candidates = [{
            "name": l["name"],
            "selector_id": None,
            "href": l["pdf_url"],
            "original_url": url,
            "pdf_url": l["pdf_url"],   # Ya resuelto: descarga directa
            "status": "resolved",
        } for l in laws_data]
        logger.info(f"Estrategia congresoags: {len(candidates)} leyes encontradas.")
        return {"laws": candidates, "logs": [f"CongresoAGS: {len(candidates)} leyes."]}

    # Congreso de Baja California: archivos .PDF directos por TOMOS
    if scraper_type == 'discovery_congresobc':
        from scripts.discover_congresobc import scrape_congresobc
        laws_data = scrape_congresobc(url)
        candidates = [{
            "name": l["name"],
            "selector_id": None,
            "href": l["pdf_url"],
            "original_url": url,
            "pdf_url": l["pdf_url"],   # Ya resuelto: descarga directa
            "status": "resolved",
        } for l in laws_data]
        logger.info(f"Estrategia congresobc: {len(candidates)} leyes encontradas.")
        return {"laws": candidates, "logs": [f"CongresoBC: {len(candidates)} leyes."]}

    # Congreso de Baja California Sur: Joomla con páginas de detalle (?id=NNNN)
    # y archivos .doc/.pdf en cada detalle (crawl de 2 niveles).
    if scraper_type == 'discovery_congresobcs':
        from scripts.discover_congresobcs import scrape_congresobcs
        laws_data = scrape_congresobcs(url)
        candidates = [{
            "name": l["name"],
            "selector_id": None,
            "href": l["file_url"] or "",
            "original_url": url,
            "pdf_url": l["file_url"] or "",
            "status": "resolved" if l["file_url"] else "pdf_not_found",
        } for l in laws_data]
        n_ok = sum(1 for c in candidates if c["status"] == "resolved")
        logger.info(f"Estrategia congresobcs: {len(candidates)} leyes, {n_ok} con archivo.")
        return {"laws": candidates, "logs": [f"CongresoBCS: {len(candidates)} leyes ({n_ok} con archivo)."]}

    selector = "a"
    if scraper_type == 'discovery_ordenjuridico':
        selector = "#resultado1 a, #resultado2 a"

    # We use the browser tool to get all links
    elements = await extract_interactive_elements(url, selector=selector)

    # FALLBACK: If specific selector yields nothing, try generic 'a' tag
    if not elements and selector != "a":
        logger.info(f"Specific selector {selector} yielded 0 elements. Retrying with generic 'a' selector...")
        elements = await extract_interactive_elements(url, selector="a")

    logger.info(f"Found {len(elements)} elements.")

    candidates = []
    for el in elements:
        # Filter obvious noise
        text = el['text']
        if len(text) < 5: continue

        # Heuristic Garbage Filter
        garbage_keywords = ["anterior", "siguiente", "next", "previous", "home", "inicio", "contacto", "mapa", "índice", "regresar", "login", "ingresar", "buscar"]
        if any(k in text.lower() for k in garbage_keywords):
            continue

        # Heuristic Positive Filter (Optional: prioritize but don't discard if not present yet)
        # We keep anything that survives the negative filter.

        candidates.append({
            "name": el['text'],
            "selector_id": el['id'],
            "href": el['href'], # CAPTURE HREF
            "original_url": url,
            "pdf_url": None,
            "status": "found"
        })

    return {"laws": candidates, "logs": [f"Found {len(candidates)} candidate links."]}

async def filter_laws_node(state: ScraperState):
    """
    Uses LLM to verify and normalize the found items.
    Las leyes ya resueltas (estrategias específicas por sitio) pasan sin filtrar.
    """
    candidates = state['laws']
    logger.info(f"Filtering {len(candidates)} candidates with heuristics & LLM...")

    if not candidates:
        return {"laws": []}

    # Si todas vienen ya resueltas (discovery_congresoags/bc), no hace falta LLM
    if all(c.get('status') == 'resolved' and c.get('pdf_url') for c in candidates):
        logger.info(f"Todas las {len(candidates)} leyes ya están resueltas; omitiendo filtro LLM.")
        return {"laws": candidates}

    llm = get_llm()
    valid_laws = []
    
    # Process in batches to avoid context limit
    BATCH_SIZE = 20
    
    for i in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[i:i+BATCH_SIZE]
        batch_text = "\n".join([f"{idx}. {c['name']} (HREF: {c.get('href', 'N/A')})" for idx, c in enumerate(batch)])
        
        prompt = f"""
        Analyze the following list of links from a government website. 
        Identify which ones are likely links to **DOWNLOADABLE LEGAL DOCUMENTS** (Laws, Codes, Regulations, Constitutions).
        Ignore navigation links, menus, or general pages.
        
        Items:
        {batch_text}
        
        Return a JSON object with a single key "valid_indices" containing the LIST of integers (from the list above) that are valid legal documents.
        Example: {{"valid_indices": [0, 2, 5]}}
        """
        
        try:
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            analysis = json.loads(content)
            indices = analysis.get("valid_indices", [])
            
            for idx in indices:
                if 0 <= idx < len(batch):
                    valid_laws.append(batch[idx])
                    
        except Exception as e:
            logger.error(f"LLM filtering failed for batch {i}: {e}")
            # Fallback: keep all if LLM fails? Or discard? 
            # Safe fallback: keep items with 'ley', 'codigo', 'reglamento' in name or '.pdf' in href
            for item in batch:
                name_lower = item['name'].lower()
                href_lower = item.get('href', '').lower()
                if any(kw in name_lower for kw in ['ley', 'código', 'codigo', 'reglamento', 'constitución']) or '.pdf' in href_lower:
                    valid_laws.append(item)

    logger.info(f"Filtered down to {len(valid_laws)} valid laws.")
    return {"laws": valid_laws}


async def resolve_pdfs_node(state: ScraperState):
    """
    Iterates through laws and resolves their PDF URLs.
    """
    laws = state['laws']
    updated_laws = []

    logger.info(f"Resolve PDFs Node: Processing {len(laws)} laws.") # TRACE
    for i, law in enumerate(laws):
        logger.info(f"Law {i}: Name='{law['name']}' Href='{law.get('href')}' ID='{law['selector_id']}'") # TRACE
        # Las estrategias específicas ya entregan el PDF resuelto
        if law.get('status') == 'resolved' and law.get('pdf_url'):
            updated_laws.append(law)
            continue
        if law.get('href') or law['selector_id']:
            # Try to resolve PDF using href first, then ID logic
            pdf_url = await resolve_law_pdf_url(state['url'], law['name'], law['selector_id'], law.get('href'))
            if pdf_url:
                law['pdf_url'] = pdf_url
                law['status'] = 'resolved'
            else:
                law['status'] = 'pdf_not_found'
        else:
            law['status'] = 'no_id_attribute'

        updated_laws.append(law)

    return {"laws": updated_laws}

async def update_db_node(state: ScraperState):
    """
    Updates the MongoDB 'scraping_sources' collection.
    """
    laws = state['laws']
    client = get_mongo_client()
    db_name = os.getenv("MONGO_DB_NAME", "jurisconsultor")
    db = client[db_name]
    collection = db["scraping_sources"]

    count_new = 0
    count_updated = 0

    for law in laws:
        if law['status'] == 'resolved' and law['pdf_url']:
            # Check if exists
            existing = collection.find_one({"name": law['name']})

            # Use slugify for safe filename but preserve extension
            ext = ".pdf"
            if law['pdf_url']:
                _, raw_ext = os.path.splitext(law['pdf_url'])
                if raw_ext:
                    # Clean extension (remove query params)
                    raw_ext = raw_ext.split('?')[0].lower()
                    if raw_ext in ['.pdf', '.doc', '.docx']:
                        ext = raw_ext
            
            safe_filename = slugify(law['name']) + ext

            doc = {
                "name": law['name'],
                "url": law['original_url'],
                "pdf_direct_url": law['pdf_url'],
                # pdf_direct_url presente => run_scraper lo descarga (Prioridad 0),
                # sin importar el scraper_type concreto.
                "scraper_type": "generic_html",
                "last_seen_at": datetime.utcnow()
            }

            if existing:
                # Update if PDF URL changed
                if existing.get('pdf_direct_url') != law['pdf_url']:
                    collection.update_one({"_id": existing["_id"]}, {"$set": doc})
                    count_updated += 1
            else:
                # Insert new
                doc["created_at"] = datetime.utcnow()
                doc["status"] = "pending"
                doc["local_filename"] = safe_filename
                collection.insert_one(doc)
                count_new += 1

    msg = f"DB Update: {count_new} new laws, {count_updated} updated."
    logger.info(msg)
    return {"logs": [msg]}

# --- Graph Construction ---

def create_scraper_graph():
    workflow = StateGraph(ScraperState)

    workflow.add_node("scan", scan_page_node)
    workflow.add_node("filter", filter_laws_node) # Added filter step
    workflow.add_node("resolve", resolve_pdfs_node)
    workflow.add_node("save", update_db_node)

    workflow.set_entry_point("scan")
    workflow.add_edge("scan", "filter")
    workflow.add_edge("filter", "resolve")
    workflow.add_edge("resolve", "save")
    workflow.add_edge("save", END)

    return workflow.compile()

async def run_scraper_agent():
    """
    Fetches discovery sources from DB and runs the scraper graph for each.
    """
    client = get_mongo_client()
    db_name = os.getenv("MONGO_DB_NAME", "jurisconsultor")
    db = client[db_name]
    collection = db["scraping_sources"]

    # Fetch all active discovery sources
    # We look for entries that start with 'discovery_'
    cursor = collection.find({
        "scraper_type": {"$regex": "^discovery_"}, 
        "$or": [
            {"status": "active"}, 
            {"status": "pending"},
            {"status": "failed"},
            {"status": {"$exists": False}}
        ]
    })
    sources = list(cursor)

    logger.info(f"Found {len(sources)} discovery sources to process.")

    graph = create_scraper_graph()
    results = []

    for source in sources:
        logger.info(f"Running scraper agent for source: {source['name']} ({source['url']})")

        initial_state = ScraperState(
            url=source['url'],
            scraper_type=source.get('scraper_type', 'discovery_ordenjuridico'),
            laws=[],
            logs=[],
            current_step="start"
        )

        try:
            result = await graph.ainvoke(initial_state)
            results.append(result)
            # Update source status to success
            collection.update_one({"_id": source["_id"]}, {"$set": {"status": "active", "last_run": datetime.utcnow()}})
        except Exception as e:
            logger.error(f"Error processing source {source['name']}: {e}", exc_info=True)
            collection.update_one({"_id": source["_id"]}, {"$set": {"status": "failed", "last_error": str(e)}})

    return results
