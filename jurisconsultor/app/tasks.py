from celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="process_legal_consultation_task")
def process_legal_consultation_task(consulta: str, tenant_id: str):
    """
    Celery task to kick off the legal consultation workflow.
    """
    logger.info(f"Starting consultation task for tenant {tenant_id}")
    # We will invoke the formal workflow here
    # from workflows.legal_workflow import process_legal_consultation
    # return process_legal_consultation(consulta, tenant_id)
    return {"status": "processing", "tenant_id": tenant_id}
