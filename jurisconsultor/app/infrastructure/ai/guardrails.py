import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Basic list of known Prompt Injection patterns
INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"ignore all previous instructions",
    r"system override",
    r"delete all files",
    r"show me your instructions",
    r"reveal system prompt",
]

class SecurityGuardrails:
    """
    Implements security checks for Input (Prompt Injection) and Output (Data Leakage/Structure).
    """

    @staticmethod
    def detect_prompt_injection(text: str) -> bool:
        """
        Scans values for known prompt injection patterns.
        Returns True if a threat is detected, False otherwise.
        """
        if not text:
            return False
            
        text_lower = text.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning(f"Prompt Injection detected: Pattern '{pattern}' found in input.")
                return True
        return False

    @staticmethod
    def validate_structure(content: str, required_keys: List[str] = None) -> bool:
        """
        Validates if the output likely contains the required structure (e.g. JSON keys).
        This is a heuristic check.
        """
        if not required_keys:
            return True
            
        for key in required_keys:
            if key not in content:
                logger.warning(f"Output Validation Failed: Missing key '{key}'")
                return False
        return True
