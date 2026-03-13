import asyncio
import logging
import sys
import os

# Adjust path to find app modules
sys.path.append('/app')
sys.path.append(os.getcwd())

from infrastructure.ai.browser_tools import extract_interactive_elements
from infrastructure.ai.agents.scraper_agent import get_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_cbcs():
    url = "https://www.cbcs.gob.mx/index.php/trabajos-legislativos/leyes"
    logger.info(f"Scanning {url}...")
    
    # 1. Try default generic extraction
    logger.info("Attempt 1: Generic 'a' selector")
    elements = await extract_interactive_elements(url, selector="a")
    logger.info(f"Found {len(elements)} raw elements.")
    
    # 2. Analyze extensions
    doc_count = 0
    pdf_count = 0
    garbage_count = 0
    
    garbage_keywords = ["anterior", "siguiente", "next", "previous", "home", "inicio", "contacto", "mapa", "índice", "regresar", "login", "ingresar", "buscar"]

    for el in elements:
        href = el.get('href', '').lower()
        text = el.get('text', '').lower()
        
        if '.doc' in href:
            doc_count += 1
            # logger.info(f"DOC link found: {el['text']} -> {el['href']}")
        if '.pdf' in href:
            pdf_count += 1
        
        if any(k in text for k in garbage_keywords):
            garbage_count += 1
            
    logger.info(f"Stats: DOCs={doc_count}, PDFs={pdf_count}, Garbage={garbage_count}")
    
    # Analyze 20 links with 'ley' or 'codigo' in text
    logger.info("--- Keyword Inspection (first 20 matches) ---")
    seen = 0
    for el in elements:
        text = el.get('text', '').strip().lower()
        href = el.get('href', '').strip()
        
        if 'ley' in text or 'código' in text or 'codigo' in text:
            # logger.info(f"MATCH: '{el['text']}' -> HREF: '{href}'")
            # Analyze DEEP LINK
            if seen == 0:
                logger.info(f"--- Deep Link Analysis for: {text} ---")
                logger.info(f"Navigating to: {href}")
                from infrastructure.ai.browser_tools import BrowserManager
                bm = await BrowserManager.get_instance()
                p = await bm.new_page()
                try:
                    await p.goto(href)
                    c = await p.content()
                    logger.info(f"--- Deep Page Content Dump (matches for .doc, .pdf, descargar) ---")
                    lines = c.splitlines()
                    for line in lines:
                        if '.doc' in line.lower() or '.pdf' in line.lower() or 'descargar' in line.lower():
                            logger.info(f"MATCH LINE: {line.strip()[:200]}")
                    await p.close()
                except Exception as e:
                    logger.error(f"Error checking deep page: {e}")
                    await p.close()

            seen += 1
            if seen >= 5: break

    if doc_count < 10:
        logger.warning("Very few docs found. Page might need scrolling or specific waiting.")
        # Attempt detailed extraction if needed (not implemented here, just diagnosis)

if __name__ == "__main__":
    asyncio.run(debug_cbcs())
