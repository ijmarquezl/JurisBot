import asyncio
import logging
from infrastructure.ai.browser_tools import extract_interactive_elements, BrowserManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Assuming this URL based on search patterns, user might need to correct if wrong.
# Common for BC: http://www.congresobc.gob.mx/contenido/legislacion/leyes.html or similar
# Let's try the root and look for 'Leyes'
BC_URL = "https://www.congresobc.gob.mx/"

async def debug_bc():
    logger.info(f"Scanning {BC_URL}...")
    try:
        # 1. Scan Main Page for Laws Link
        elements = await extract_interactive_elements(BC_URL, selector="a")
        laws_url = None
        for el in elements:
            if 'leyes' in el.get('text', '').lower():
                 laws_url = el['href']
                 logger.info(f"Found Laws Link: {laws_url}")
                 break
        
        if not laws_url:
            # Fallback to direct URL if possible
             laws_url = "https://www.congresobc.gob.mx/contenido/legislacion/leyes.html"
             logger.info(f"Using default Laws URL: {laws_url}")
        
        # 2. Scan Laws Page
        logger.info(f"Scanning Laws Page: {laws_url}")
        elements = await extract_interactive_elements(laws_url, selector="a")
        
        # Check for PDF vs DOC
        count_pdf = 0
        count_doc = 0
        for i, el in enumerate(elements[:50]): # Check first 50
            href = el.get('href', '').lower()
            text = el.get('text', '').strip()
            logger.info(f"Link {i}: Text='{text}' Href='{href}'")
            if '.pdf' in href: count_pdf += 1
            if '.doc' in href: count_doc += 1
            
        logger.info(f"Stats: PDF={count_pdf}, DOC={count_doc}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        bm = await BrowserManager.get_instance()
        await bm.close()

if __name__ == "__main__":
    asyncio.run(debug_bc())
