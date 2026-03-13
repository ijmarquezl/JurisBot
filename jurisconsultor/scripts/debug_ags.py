import asyncio
import logging
from infrastructure.ai.browser_tools import extract_interactive_elements, BrowserManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AGUASCALIENTES_URL = "https://congresoags.gob.mx/agenda_legislativa/leyes"

async def debug_ags():
    logger.info(f"Scanning {AGUASCALIENTES_URL}...")
    try:
        # Extract links
        elements = await extract_interactive_elements(AGUASCALIENTES_URL, selector="a")
        logger.info(f"Found {len(elements)} links.")
        
        pdf_links = []
        
        unique_hrefs = set()
        if elements:
             for i, el in enumerate(elements):
                 href = el.get('href', '').lower()
                 if href and href not in unique_hrefs and '#' not in href and 'javascript' not in href:
                     unique_hrefs.add(href)
                     logger.info(f"VALID LINK: Text='{el.get('text')}' Href='{el.get('href')}'")



        for el in elements:
            href = el.get('href', '').lower()
            text = el.get('text', '').strip()
            
            if 'descargapdf' in href or '.pdf' in href:
                logger.info(f"Potential PDF: Text='{text}' -> Href='{el['href']}'")
                pdf_links.append(el)

            
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        bm = await BrowserManager.get_instance()
        await bm.close()

if __name__ == "__main__":
    asyncio.run(debug_ags())
