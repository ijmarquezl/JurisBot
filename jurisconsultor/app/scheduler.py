import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from web_downloader import run_scraper
from app.scraper_agent import run_scraper_agent
import asyncio

# Configure logging explicitly to ensure output is captured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logging.getLogger('apscheduler').setLevel(logging.INFO)
logger = logging.getLogger(__name__)

def scheduled_job():
    """The job that will be executed by the scheduler."""
    logger.info("--- Starting scheduled scraper job ---")
    try:
        # Run the discovery agent first
        # Since run_scraper_agent is async, we need to run it in an event loop
        logger.info("Running discovery agent...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_scraper_agent())
        loop.close()

        # Then run the downloader/processor
        logger.info("Running file downloader...")
        run_scraper()
        logger.info("--- Scheduled scraper job finished successfully ---")
    except Exception as e:
        logger.error(f"An error occurred during the scheduled scraper job: {e}", exc_info=True)

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # Schedule the job to run every day at midnight
    scheduler.add_job(scheduled_job, 'cron', hour=0, minute=0)
    
    logger.info("Scheduler started. Press Ctrl+C to exit.")
    
    # Run the job once immediately on startup
    logger.info("Running initial scraper job on startup...")
    scheduled_job()
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
