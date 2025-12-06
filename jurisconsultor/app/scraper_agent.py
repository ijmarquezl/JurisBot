import logging
import asyncio
from typing import TypedDict, List, Optional, Annotated
import operator
from datetime import datetime

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

from app.browser_tools import extract_interactive_elements, resolve_law_pdf_url
from app.utils import get_mongo_client
# Actually, I'll build a specific graph for this to be precise.
from langchain_openai import ChatOpenAI # Or whatever LLM is used.
# The user mentioned "same LLM configured for the other agents".
# Usually via 'graph_agent.py' or 'models.py'
# If get_llm doesn't exist, I'll define it based on Context.md info (Ollama)
from langchain_community.chat_models import ChatOllama

logger = logging.getLogger(__name__)

# --- State Definition ---
class LawItem(TypedDict):
    name: str
    selector_id: str
    original_url: str # Main page URL
    pdf_url: Optional[str]
    status: str # 'found', 'processed', 'failed'

class ScraperState(TypedDict):
    url: str
    laws: List[LawItem]
    logs: List[str]
    current_step: str

# --- Tools for the Agent ---

# We'll use the browser_tools directly in the nodes for efficiency,
# but we can also expose them if we want the LLM to call them.
# For this specific task (scan -> list -> update), a structured graph is better than a free-form ReAct agent.
# Node 1: Scan
# Node 2: Filter/Parse (LLM)
# Node 3: Update DB

def get_ollama_llm():
    # URL from Context.md: http://10.29.93.56:11434, model: llama3
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
    logger.info(f"Scanning {url} for laws...")

    # We use the browser tool to get all links
    # We focus on the tables or specific divs if known, or just all links.
    # The existing scraper looks in 'resultado1' and 'resultado2'.
    elements = await extract_interactive_elements(url, selector="#resultado1 a, #resultado2 a")

    logger.info(f"Found {len(elements)} elements.")

    # We pass these elements to the next step (or filter here if simple)
    # Let's map them to a temporary structure
    candidates = []
    for el in elements:
        # Filter obvious noise
        if len(el['text']) < 5: continue

        candidates.append({
            "name": el['text'],
            "selector_id": el['id'], # This ID is crucial for the PDF logic
            "original_url": url,
            "pdf_url": None,
            "status": "found"
        })

    return {"laws": candidates, "logs": [f"Found {len(candidates)} candidate links."]}

async def filter_laws_node(state: ScraperState):
    """
    Uses LLM to verify if the found items are indeed laws we want to track.
    (Optional if the selector was strict enough, but good for 'reasoning').
    """
    # If the list is huge, LLM processing might be slow.
    # Since the user wants "Discovery", we can assume anything in 'resultado1' (Leyes Federales) is a law.
    # We'll skip LLM filtering for the *entire* list for performance,
    # but we could use LLM to parse the name properly if it's messy.

    # For now, pass through.
    return {"current_step": "filtering_complete"}

async def resolve_pdfs_node(state: ScraperState):
    """
    Iterates through laws and resolves their PDF URLs.
    """
    laws = state['laws']
    updated_laws = []

    for law in laws:
        # Use the logic-based resolver (simulating the 'click' logic)
        if law['selector_id']:
            pdf_url = await resolve_law_pdf_url(state['url'], law['name'], law['selector_id'])
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
    db = client[f"jurisconsultor"] # Or get from env
    collection = db["scraping_sources"]

    count_new = 0
    count_updated = 0

    for law in laws:
        if law['status'] == 'resolved' and law['pdf_url']:
            # Check if exists
            existing = collection.find_one({"name": law['name']})

            doc = {
                "name": law['name'],
                "url": law['original_url'],
                "pdf_direct_url": law['pdf_url'],
                "scraper_type": "ordenjuridico_special", # Mark it so existing scraper handles it
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
                doc["status"] = "pending" # Ready for the downloader to pick up
                doc["local_filename"] = f"{law['name'].replace(' ', '_')}.pdf" # Simple filename gen
                collection.insert_one(doc)
                count_new += 1

    msg = f"DB Update: {count_new} new laws, {count_updated} updated."
    logger.info(msg)
    return {"logs": [msg]}

# --- Graph Construction ---

def create_scraper_graph():
    workflow = StateGraph(ScraperState)

    workflow.add_node("scan", scan_page_node)
    workflow.add_node("resolve", resolve_pdfs_node)
    workflow.add_node("save", update_db_node)

    workflow.set_entry_point("scan")
    workflow.add_edge("scan", "resolve")
    workflow.add_edge("resolve", "save")
    workflow.add_edge("save", END)

    return workflow.compile()

async def run_scraper_agent():
    graph = create_scraper_graph()
    initial_state = ScraperState(
        url="https://www.ordenjuridico.gob.mx/leyes.php",
        laws=[],
        logs=[],
        current_step="start"
    )
    # Invoke
    result = await graph.ainvoke(initial_state)
    return result
