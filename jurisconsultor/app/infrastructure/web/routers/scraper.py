from fastapi import APIRouter, HTTPException, BackgroundTasks
from infrastructure.ai.agents.scraper_agent import run_scraper_agent
from infrastructure.ai.web_downloader import run_scraper
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/scrape-laws")
async def trigger_scraper(background_tasks: BackgroundTasks):
    """
    Triggers the FULL scraping pipeline in background:
      1. Descubrimiento (scraper_agent): encuentra y siembra las leyes de las
         semillas discovery_* (incluye estrategias por estado: congresoags, congresobc).
      2. Ingesta (run_scraper): descarga los PDFs de todas las fuentes activas y
         los ingiere en el RAG.
    El superadmin puede seguir el avance en los logs del backoffice.
    """
    background_tasks.add_task(run_full_scraper_task)
    return {"message": "Pipeline de scraping iniciado en segundo plano (descubrimiento + ingesta)."}

async def run_full_scraper_task():
    try:
        # 1) Descubrimiento
        logger.info("Starting scraper agent (discovery)...")
        results = await run_scraper_agent()
        for idx, result in enumerate(results):
            logger.info(f"Scraper agent finished for source index {idx}. Logs: {result.get('logs')}")

        # 2) Ingesta RAG (descarga + procesamiento) de todas las fuentes activas
        logger.info("Starting RAG ingestion (run_scraper)...")
        run_scraper()
        logger.info("Full scraping pipeline finished.")
    except Exception as e:
        logger.error(f"Scraper pipeline failed: {e}", exc_info=True)
