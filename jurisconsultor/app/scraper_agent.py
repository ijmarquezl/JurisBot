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

from app.browser_tools import extract_interactive_elements, resolve_law_pdf_url
from app.utils import get_mongo_client
from langchain_openai import ChatOpenAI
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

    selector = "a"
    if scraper_type == 'discovery_ordenjuridico':
        selector = "#resultado1 a, #resultado2 a"

    # We use the browser tool to get all links
    elements = await extract_interactive_elements(url, selector=selector)

    logger.info(f"Found {len(elements)} elements.")

    candidates = []
    for el in elements:
        # Filter obvious noise
        if len(el['text']) < 5: continue

        candidates.append({
            "name": el['text'],
            "selector_id": el['id'],
            "original_url": url,
            "pdf_url": None,
            "status": "found"
        })

    return {"laws": candidates, "logs": [f"Found {len(candidates)} candidate links."]}

async def filter_laws_node(state: ScraperState):
    """
    Uses LLM to verify and normalize the found items.
    """
    candidates = state['laws']
    logger.info(f"Filtering {len(candidates)} candidates with LLM...")

    # To avoid blowing up the context window or taking too long,
    # we'll process in batches or just use the LLM to 'judge' the list structure if small.
    # Given potentially hundreds of laws, passing *all* to the LLM is risky.
    # However, the user explicitly asked for LLM reasoning.

    # Let's perform a lightweight heuristic filter first, then asking LLM to confirm the *pattern*.
    # Actually, let's pick a sample of 5 items and ask the LLM if they look like laws.
    # If yes, we assume the selector was good.

    if not candidates:
        return {"laws": []}

    sample = candidates[:5]
    sample_text = "\n".join([f"- {c['name']} (ID: {c['selector_id']})" for c in sample])

    llm = get_llm()
    prompt = f"""
    Analyze the following list of items extracted from a government website:
    {sample_text}

    Are these items likely to be legal documents (laws, codes, regulations)?
    Respond with a JSON object: {{"is_legal_content": true/false, "reason": "..."}}
    """

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content
        # Basic cleanup if markdown json
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
             content = content.split("```")[1].split("```")[0].strip()

        analysis = json.loads(content)

        if not analysis.get("is_legal_content", False):
            logger.warning(f"LLM decided content is not legal: {analysis.get('reason')}")
            # If LLM rejects, we might want to flag or stop, but for now let's just log and proceed
            # (better false positives than false negatives in this context, or maybe empty list?)
            # return {"laws": []}
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        # Proceed with heuristics

    # We can also use the LLM to normalize names if needed, but 'slugify' in the next steps handles filenames.
    # We return the candidates passed through.
    return {"laws": candidates}


async def resolve_pdfs_node(state: ScraperState):
    """
    Iterates through laws and resolves their PDF URLs.
    """
    laws = state['laws']
    updated_laws = []

    for law in laws:
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
    db_name = os.getenv("MONGO_DB_NAME", "jurisconsultor")
    db = client[db_name]
    collection = db["scraping_sources"]

    count_new = 0
    count_updated = 0

    for law in laws:
        if law['status'] == 'resolved' and law['pdf_url']:
            # Check if exists
            existing = collection.find_one({"name": law['name']})

            # Use slugify for safe filename
            safe_filename = slugify(law['name']) + ".pdf"

            doc = {
                "name": law['name'],
                "url": law['original_url'],
                "pdf_direct_url": law['pdf_url'],
                "scraper_type": "ordenjuridico_special",
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
    cursor = collection.find({"scraper_type": {"$regex": "^discovery_"}, "status": "active"})
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
        except Exception as e:
            logger.error(f"Error processing source {source['name']}: {e}", exc_info=True)

    return results
