import os
import re
import requests
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import logging
from typing import Optional # Added this import

from infrastructure.utils.utils import get_mongo_client
from scripts.legal_scraper import process_single_document, delete_document_by_source

logger = logging.getLogger(__name__)

SOURCES_COLLECTION = "scraping_sources"
PDF_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'documentos_legales'))

def truncate_filename(filename: str, max_length: int = 200) -> str:
    """Truncates a filename to a maximum length, preserving the extension."""
    if len(filename) <= max_length:
        return filename
    
    name, ext = os.path.splitext(filename)
    if len(ext) > 10: # Safety check for weird extensions
        ext = ext[:10]
        
    available_length = max_length - len(ext)
    truncated_name = name[:available_length]
    return truncated_name + ext

def find_pdf_link(page_url: str, html_content: str, pdf_link_contains: Optional[str] = None, pdf_link_ends_with: Optional[str] = None, depth: int = 0) -> str:
    """
    Finds a PDF link on a given HTML page. Supports 1-level deep search.
    """
    logger.info(f"Scanning for PDF links on {page_url} (depth={depth})...")
    soup = BeautifulSoup(html_content, 'lxml')
    
    # 1. Search for Direct PDF Links
    candidates = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_url = urljoin(page_url, href)
        
        # Criteria match
        match_contains = pdf_link_contains and (pdf_link_contains in href)
        match_ends_with = pdf_link_ends_with and href.endswith(pdf_link_ends_with)
        
        # Implicit match: Ends with .pdf (case insensitive)
        is_pdf = absolute_url.lower().endswith('.pdf')
        
        if (match_contains or match_ends_with) and is_pdf:
            return absolute_url
        
        if is_pdf:
            candidates.append(absolute_url)

    # Return first specific candidate if any
    if candidates:
        logger.info(f"Found {len(candidates)} candidate PDF links. Using first: {candidates[0]}")
        return candidates[0]

    # 2. Deep Search (Level 2) - Only if depth == 0
    # If no PDF found, look for "likely detail page" links and dive in.
    if depth == 0:
        logger.info("No direct PDF link found. Attempting Deep Search (Level 2)...")
        potential_links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            text = a_tag.get_text(strip=True).lower()
            absolute_url = urljoin(page_url, href)
            
            # Keywords suggesting a detail page or download section
            keywords = ['ver', 'detalle', 'descargar', 'documento', 'leer', 'texto', 'completo']
            if any(k in text for k in keywords) or any(k in href.lower() for k in keywords):
                potential_links.append(absolute_url)
        
        # Limit deep search to first 3 promising links to save time
        for link in potential_links[:3]:
            try:
                logger.info(f"Deep Search: Diving into {link}...")
                resp = requests.get(link, timeout=15, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
                if resp.status_code == 200:
                    found_pdf = find_pdf_link(link, resp.text, pdf_link_contains, pdf_link_ends_with, depth=1)
                    if found_pdf:
                        logger.info(f"Deep Search SUCCESS! Found PDF at {found_pdf}")
                        return found_pdf
            except Exception as e:
                logger.warning(f"Deep Search failed for {link}: {e}")

    return None


def scrape_ordenjuridico_law(main_page_url: str, law_name: str) -> Optional[str]:
    """
    Specialized scraper for ordenjuridico.gob.mx to find the PDF link for a given law.
    This site uses JavaScript to generate download links in a popup.
    """
    logger.info(f"Using specialized scraper for Orden Jurídico Nacional for law: '{law_name}'")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # 1. Fetch the main page (leyes.php)
        page_response = requests.get(main_page_url, timeout=30, headers=headers, verify=False)
        page_response.raise_for_status()
        soup = BeautifulSoup(page_response.text, 'lxml')
        
        # 2. Find the <a> tag for the specific law name
        # The law names are in <td> elements, and the <a> tag is a child
        # Example: <a href='#' class='basic' id='.././Documentos/Federal/wo17186.doc'>Código Civil Federal</a>
        law_link_tag = None
        # Search within both resultado1 and resultado2 divs
        for div_id in ['resultado1', 'resultado2']:
            result_div = soup.find('div', id=div_id)
            if result_div:
                # Find <a> tags with class 'basic' that contain the law_name
                # Using a regex for law_name to handle potential extra spaces or variations
                law_link_tag = result_div.find('a', class_='basic', string=re.compile(re.escape(law_name), re.IGNORECASE))
                if law_link_tag:
                    break
        
        if not law_link_tag:
            logger.warning(f"Could not find link for law '{law_name}' on {main_page_url}")
            return None
            
        doc_id_attr = law_link_tag.get('id')
        if not doc_id_attr:
            logger.warning(f"Link for law '{law_name}' found, but missing 'id' attribute.")
            return None
            
        # 3. Parse the 'id' attribute to construct the PDF URL
        # Example id: '.././Documentos/Federal/wo17186.doc'
        # The basic.js script extracts 'wo17186' and constructs the PDF path.
        
        # Split by '/' and get the last part, then split by '.' and get the first part
        arr = doc_id_attr.split('/')
        filename_with_ext = arr[-1] # e.g., 'wo17186.doc'
        arrP = filename_with_ext.split('.')
        base_filename = arrP[0] # e.g., 'wo17186'
        
        # Construct the absolute PDF URL based on basic.js logic
        pdf_relative_path = f"Documentos/Federal/pdf/{base_filename}.pdf"
        absolute_pdf_url = urljoin(main_page_url, f".././{pdf_relative_path}")
        
        logger.info(f"Constructed PDF URL for '{law_name}': {absolute_pdf_url}")
        return absolute_pdf_url
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {main_page_url} for specialized scraping: {e}")
        return None
    except Exception as e:
        logger.error(f"Error in specialized Orden Jurídico Nacional scraper for '{law_name}': {e}", exc_info=True)
        return None

def download_pdf(pdf_url: str) -> bytes:
    """Downloads a PDF from a URL and returns its content as bytes."""
    try:
        logger.info(f"Downloading PDF from {pdf_url}...")
        # Add User-Agent header and disable SSL verification for problematic sites
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(pdf_url, timeout=30, headers=headers, verify=False) # verify=False for SSL issues
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Failed to download PDF from {pdf_url}: {e}")
        return None

def calculate_hash(data: bytes) -> str:
    """Calculates the SHA256 hash of the given data."""
    return hashlib.sha256(data).hexdigest()

def run_scraper():
    """
    Main function to run the web scraping and processing pipeline.
    """
    logger.info("Starting web scraper run...")
    mongo_client = get_mongo_client()
    db_name = os.getenv("MONGO_DB_NAME", "jurisconsultor")
    db = mongo_client[db_name]
    sources_collection = db[SOURCES_COLLECTION]
    
    logger.info(f"Scraping sources from database: '{db_name}'")
    # Fetch all active sources
    sources = list(sources_collection.find({"url": {"$ne": None}, "status": {"$ne": "disabled"}}))
    logger.info(f"Found {len(sources)} sources to process.")

    for source in sources:
        source_id = source["_id"]
        scraper_type = source.get('scraper_type', 'generic_html')

        # SKIP Discovery Types (handled by scraper_agent)
        if scraper_type and scraper_type.startswith('discovery_'):
            logger.info(f"Skipping Discovery Source '{source['name']}' (handled by scraper_agent).")
            continue

        logger.info(f"Processing source: {source['name']} (URL: {source['url']})")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            pdf_url = None
            
            if scraper_type == 'ordenjuridico_special':
                # Use specialized scraper for ordenjuridico.gob.mx
                pdf_url = scrape_ordenjuridico_law(source['url'], source['name'])
                if not pdf_url:
                    sources_collection.update_one(
                        {"_id": source_id},
                        {"$set": {"status": "failed", "error_message": "Specialized scraper failed to find PDF link."}}
                    )
                    continue
            elif scraper_type in ['generic_html', 'HTML Genérico']:
                # Option 1: Direct PDF URL provided
                if source.get('pdf_direct_url'):
                    pdf_url = source['pdf_direct_url']
                    logger.info(f"Using direct PDF URL: {pdf_url}")
                else:
                    # Option 2: Scrape HTML page for PDF link (with Deep Search)
                    logger.info(f"Fetching HTML from {source['url']} to find PDF link...")
                    page_response = requests.get(source['url'], timeout=30, headers=headers, verify=False)
                    page_response.raise_for_status()
                    
                    pdf_url = find_pdf_link(
                        source['url'], 
                        page_response.text, 
                        pdf_link_contains=source.get('pdf_link_contains'), 
                        pdf_link_ends_with=source.get('pdf_link_ends_with')
                    )
            else:
                logger.error(f"Unknown scraper_type '{scraper_type}' for source '{source['name']}'.")
                sources_collection.update_one(
                    {"_id": source_id},
                    {"$set": {"status": "failed", "error_message": f"Unknown scraper type: {scraper_type}"}}
                )
                continue
            
            if not pdf_url:
                logger.warning(f"No PDF link found for source: {source['name']}. Check URL and matching criteria.")
                sources_collection.update_one(
                    {"_id": source_id},
                    {"$set": {"status": "failed", "error_message": "No PDF link found matching criteria."}}
                )
                continue

            # 3. Download the PDF and calculate hash
            pdf_content = download_pdf(pdf_url)
            if not pdf_content:
                sources_collection.update_one(
                    {"_id": source_id},
                    {"$set": {"status": "failed", "error_message": f"Failed to download PDF from {pdf_url}."}}
                )
                continue
            
            new_hash = calculate_hash(pdf_content)
            
            # 4. Check if the file has changed
            if new_hash == source.get('last_known_hash'):
                logger.info(f"Source '{source['name']}' is already up to date. Skipping.")
                sources_collection.update_one(
                    {"_id": source_id},
                    {"$set": {"status": "up_to_date", "last_checked_at": datetime.utcnow()}}
                )
                continue
                
            logger.info(f"New version of '{source['name']}' detected (hash: {new_hash[:10]}...).")
            
            # 5. Process the update
            local_filename = source.get('local_filename')
            if not local_filename:
                # Fallback if filename missing
                safe_name = re.sub(r'[^a-zA-Z0-9]', '_', source['name'])
                local_filename = f"{safe_name}.pdf"

            # TRUNCATE FILENAME
            local_filename = truncate_filename(local_filename)
            logger.info(f"Using local filename: {local_filename}")

            # Delete old data before processing new file
            delete_document_by_source(source_name=local_filename, db_type='public', company_id=None)

            # Save new file
            local_pdf_path = os.path.join(PDF_DIRECTORY, local_filename)
            os.makedirs(PDF_DIRECTORY, exist_ok=True)
            with open(local_pdf_path, 'wb') as f:
                f.write(pdf_content)
            logger.info(f"Saved new PDF to {local_pdf_path}")

            # Process the new document
            process_single_document(local_pdf_path, db_type='public', company_id=None)

            # 6. Update the source record in DB
            sources_collection.update_one(
                {"_id": source_id},
                {
                    "$set": {
                        "status": "success",
                        "last_known_hash": new_hash,
                        "last_downloaded_at": datetime.utcnow(),
                        "error_message": None,
                        "local_filename": local_filename # Update DB with truncated name
                    }
                }
            )
            logger.info(f"Successfully updated source '{source['name']}'.")

        except Exception as e:
            logger.error(f"An unexpected error occurred while processing source '{source['name']}': {e}", exc_info=True)
            sources_collection.update_one(
                {"_id": source_id},
                {"$set": {"status": "failed", "error_message": str(e)}}
            )

    logger.info("Web scraper run finished.")

if __name__ == "__main__":
    # This allows running the scraper manually for testing
    run_scraper()
