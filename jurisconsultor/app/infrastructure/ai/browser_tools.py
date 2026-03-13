import logging
import asyncio
from typing import List, Dict, Optional, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

logger = logging.getLogger(__name__)

class BrowserManager:
    _instance = None
    _playwright = None
    _browser = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = BrowserManager()
            await cls._instance._init()
        return cls._instance

    async def _init(self):
        self._playwright = await async_playwright().start()
        # Launch headless for server environment
        self._browser = await self._playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        logger.info("Browser launched.")

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed.")

    async def new_page(self) -> Page:
        context = await self._browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        return await context.new_page()

async def navigate_to_page(url: str) -> str:
    """Navigates to a URL and returns the page title."""
    manager = await BrowserManager.get_instance()
    page = await manager.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        title = await page.title()
        await page.close()
        return f"Successfully navigated to {url}. Page Title: {title}"
    except Exception as e:
        await page.close()
        return f"Error navigating to {url}: {str(e)}"

async def get_page_content_summary(url: str) -> str:
    """Navigates to a URL and returns a simplified markdown summary of the content."""
    manager = await BrowserManager.get_instance()
    page = await manager.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)

        # Simple extraction script to get headers and links
        content = await page.evaluate("""() => {
            let text = "";
            document.querySelectorAll('h1, h2, h3, h4, table').forEach(el => {
                text += el.innerText + "\\n";
            });
            return text;
        }""")

        await page.close()
        return content[:5000] # Limit content size
    except Exception as e:
        await page.close()
        return f"Error getting content from {url}: {str(e)}"

async def extract_interactive_elements(url: str, selector: str = "a") -> List[Dict[str, str]]:
    """
    Extracts elements matching the selector. Returns text and attributes.
    Useful for finding links to click.
    """
    manager = await BrowserManager.get_instance()
    page = await manager.new_page()
    try:
        await page.goto(url, wait_until="networkidle", timeout=60000)

        # Wait for some content if needed, e.g., the table
        try:
            await page.wait_for_selector('table', timeout=5000)
        except:
            pass # Continue if no table

        elements = await page.evaluate(f"""(selector) => {{
            const els = Array.from(document.querySelectorAll(selector));
            return els.map(el => ({{
                text: el.innerText.trim() || el.title || el.ariaLabel || 'No Text',
                href: el.href || '',
                id: el.id || '',
                class: el.className || '',
                onclick: el.getAttribute('onclick') || ''
            }})).filter(item => item.href.length > 0);
        }}""", selector)

        await page.close()
        return elements
    except Exception as e:
        await page.close()
        logger.error(f"Error extracting elements: {e}")
        return []

async def resolve_law_pdf_url(base_url: str, law_name: str, law_id: Optional[str] = None, href: Optional[str] = None) -> Optional[str]:
    """
    Attempts to resolve the PDF URL for a law, mimicking the user interaction or logic.
    If 'law_id' is provided, it tries the known logic first.
    If not, it might need to browse.
    """
    # 1. Direct HREF check (Generic Strategy)
    if href:
        logger.info(f"Resolving HREF: '{href}'") # DEBUG TRACE
        lower_href = href.lower()
        if lower_href.endswith('.pdf') or lower_href.endswith('.doc') or lower_href.endswith('.docx') or 'descargapdf' in lower_href:
            if href.startswith('http'):
                return href
            # Resolve relative
            from urllib.parse import urljoin
            return urljoin(base_url, href)
    
    # 2. Deep Resolution via Page Visit (Fallback for unknown HTML pages)
    # Exclude internal anchors or JS links to prevent analyzing non-pages like OrdenJuridico '#' links
    if href and not (href.endswith('#') or 'javascript:' in href.lower()):
        # Double check extensions again just in case (redundant but safe)
        if not (href.lower().endswith('.pdf') or href.lower().endswith('.doc') or href.lower().endswith('.docx')):
            try:
                # Ensure absolute URL
                from urllib.parse import urljoin
                full_deep_url = urljoin(base_url, href)
                
                logger.info(f"Navigating to deep link to find document: {full_deep_url}")
                manager = await BrowserManager.get_instance()
                # Use a fresh context/page prevents side effects
                page = await manager.new_page()
                try:
                    await page.goto(full_deep_url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Find document links with heuristic prioritization
                    doc_link = await page.evaluate("""() => {
                        const anchors = Array.from(document.querySelectorAll('a'));
                        let pdfLink = null;
                        let docLink = null;

                        for (const a of anchors) {
                            const h = a.href.toLowerCase();
                            // Priority 1: Direct PDF or explicit download keyword
                            if (h.endsWith('.pdf') || h.includes('descargapdf')) {
                                pdfLink = a.href;
                                break; // Found best candidate
                            }
                            // Priority 2: Word documents (fallback)
                            if (h.endsWith('.doc') || h.endsWith('.docx')) {
                                if (!docLink) docLink = a.href;
                            }
                        }
                        return pdfLink || docLink;
                    }""")
                    
                    if doc_link:
                        logger.info(f"Resolved deep link: {doc_link}")
                        return doc_link
                finally:
                    await page.close()
            except Exception as e:
                # SPECIAL CASE: If navigation fails because it's a direct download, that's a WIN!
                if "Download is starting" in str(e):
                    logger.info(f"Direct download detected for {full_deep_url}. Returning as PDF URL.")
                    return full_deep_url
                
                logger.error(f"Error deep resolving {href}: {e}")

    # 3. Reusing specific logic for ordenjuridico if ID exists and deep resolution failed/skipped
    if law_id:
        try:
             # Basic check to avoid false positives
             if '/' not in law_id:
                 return None 
                 
             # Logic: Documentos/Federal/pdf/{filename}.pdf
             parts = law_id.split('/')
             filename = parts[-1]
             if '.' in filename:
                 filename = filename.split('.')[0]

             pdf_path = f"Documentos/Federal/pdf/{filename}.pdf"
             full_url = f"https://www.ordenjuridico.gob.mx/{pdf_path}"
             return full_url
        except Exception as e:
            logger.error(f"Error resolving PDF URL logic: {e}")
            return None

    return None
