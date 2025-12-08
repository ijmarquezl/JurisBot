from fastapi import APIRouter, HTTPException, BackgroundTasks
from scraper_agent import run_scraper_agent
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/scrape-laws")
async def trigger_scraper(background_tasks: BackgroundTasks):
    """
    Triggers the background scraping agent to find and update laws.
    """
    background_tasks.add_task(run_scraper_task)
    return {"message": "Scraper agent triggered in background."}

async def run_scraper_task():
    try:
        logger.info("Starting scheduled/manual scraper agent...")
        results = await run_scraper_agent()
        for idx, result in enumerate(results):
            logger.info(f"Scraper agent finished for source index {idx}. Logs: {result.get('logs')}")
    except Exception as e:
        logger.error(f"Scraper agent failed: {e}", exc_info=True)
