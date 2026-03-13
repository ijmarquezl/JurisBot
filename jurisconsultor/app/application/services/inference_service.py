import logging
import datetime
from typing import Optional, Any, Dict
from infrastructure.ai.guardrails import SecurityGuardrails

logger = logging.getLogger(__name__)

class InferenceService:
    """
    Centralized service for Secure LLM Inference.
    Enforces Guardrails and Audit Logging.
    """

    def __init__(self):
        self.guard = SecurityGuardrails()

    def validate_input(self, user_input: str) -> bool:
        """
        Validates user input against Guardrails.
        Returns True if safe, raises ValueError if unsafe.
        """
        if self.guard.detect_prompt_injection(user_input):
            self._log_audit(user_input, "BLOCKED", "Prompt Injection Detected")
            raise ValueError("Security Alert: Potential input manipulation detected. Request blocked.")
        
        return True

    def _log_audit(self, prompt: str, response: str, risk_analysis: str):
        """
        Logs the interaction to the AUDIT log.
        In production, this would go to a database or SIEM.
        """
        timestamp = datetime.datetime.utcnow().isoformat()
        log_entry = f"| {timestamp} | Inference | {risk_analysis} | {prompt[:50]}... -> {response[:20]}... |\n"
        
        try:
            # Appending to project root AUDIT.md (assuming path relative to where app runs or absolute)
            # Since we are in clean architecture, we should ideally use a port/adapter for this.
            # For now, we append to the file directly or log to stdout which is captured.
            logger.info(f"AUDIT LOG: {log_entry.strip()}")
            
            # TODO: Implement proper file appending logic if needed, or rely on structured logs.
            # for the sake of this level, logging to the logger is sufficient for Docker capture.
        except Exception as e:
            logger.error(f"Failed to write to audit log: {e}")

    def secure_invoke(self, model_callable, prompt: Any) -> Any:
        # Prompt can be str or List[BaseMessage]
        text_to_validate = prompt
        if isinstance(prompt, list):
            # rudimentary extraction of text from last message if it's a list
            # In production, we might validate the whole chain or specifically user messages
            try:
                text_to_validate = prompt[-1].content
            except Exception:
                text_to_validate = str(prompt)
        
        self.validate_input(str(text_to_validate))
        
        start_time = datetime.datetime.utcnow()
        try:
            response = model_callable(prompt)
            # Here we could add output validation if needed
            self._log_audit(str(text_to_validate), str(response), "Clean")
            return response
        except ValueError as ve:
            # Re-raise security exceptions
            raise ve
        except Exception as e:
            self._log_audit(str(text_to_validate), "ERROR", f"Execution Error: {str(e)}")
            raise e
