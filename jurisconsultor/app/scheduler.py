import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from web_downloader import run_scraper

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
        run_scraper()
        logger.info("--- Scheduled scraper job finished successfully ---")
    except Exception as e:
        logger.error(f"An error occurred during the scheduled scraper job: {e}", exc_info=True)

if __name__ == "__main__":
    scheduler = BlockingScheduler()
    # Schedule the job to run every 24 hours
    scheduler.add_job(scheduled_job, 'interval', hours=24)
    
    logger.info("Scheduler started. Press Ctrl+C to exit.")
    
    # Run the job once immediately on startup
    logger.info("Running initial scraper job on startup...")
    scheduled_job()
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
