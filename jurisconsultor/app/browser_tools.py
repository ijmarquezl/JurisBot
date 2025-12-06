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
                text: el.innerText.trim(),
                href: el.href || '',
                id: el.id || '',
                class: el.className || '',
                onclick: el.getAttribute('onclick') || ''
            }})).filter(item => item.text.length > 0);
        }}""", selector)

        await page.close()
        return elements
    except Exception as e:
        await page.close()
        logger.error(f"Error extracting elements: {e}")
        return []

async def resolve_law_pdf_url(base_url: str, law_name: str, law_id: Optional[str] = None) -> Optional[str]:
    """
    Attempts to resolve the PDF URL for a law, mimicking the user interaction or logic.
    If 'law_id' is provided, it tries the known logic first.
    If not, it might need to browse.
    """
    # Based on the user requirement, the agent needs to 'click' or resolve the link.
    # The existing logic in web_downloader.py suggests the ID contains the path.
    # But if we want to be robust and 'agentic', we can try to actually click if logic fails?
    # For now, let's implement the logic derivation in the tool, as clicking 500 links is slow.
    # BUT, the Agent's job is to update the DB.

    # Let's keep this tool simple for now: it just validates the URL if possible or returns the logic-derived one.

    # Reusing logic from web_downloader.py but as a standalone tool for the agent
    if law_id:
        try:
            # Example id: '.././Documentos/Federal/wo17186.doc'
            # Logic: Documentos/Federal/pdf/{filename}.pdf
            parts = law_id.split('/')
            filename = parts[-1]
            if '.' in filename:
                filename = filename.split('.')[0]

            # The structure seems to be relative to the domain root or current path
            # Current URL: https://www.ordenjuridico.gob.mx/leyes.php
            # Logic in basic.js:
            # function ver(doc) { ... window.open(doc ... }
            # Wait, the ID in web_downloader was used to construct a PDF path.

            # Let's trust the existing reverse-engineering for speed, but allow the Agent to use it.
            pdf_path = f"Documentos/Federal/pdf/{filename}.pdf"
            full_url = f"https://www.ordenjuridico.gob.mx/{pdf_path}"
            return full_url
        except Exception as e:
            logger.error(f"Error resolving PDF URL logic: {e}")
            return None
    return None
