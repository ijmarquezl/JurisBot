import os
import json
import docx
from difflib import get_close_matches
from typing import Optional

class TemplateManager:
    """
    Manages loading and parsing local legal templates (docx).
    """

    def __init__(self, templates_dir: str = None):
        if not templates_dir:
            # Default to the known directory inside the project
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.templates_dir = os.path.join(base_dir, "ejemplos_legales")
        else:
            self.templates_dir = templates_dir
            
        self.index_path = os.path.join(self.templates_dir, "templates.json")
        self.templates_index = self._load_index()

    def _load_index(self) -> dict:
        """Loads the template index JSON file."""
        if os.path.exists(self.index_path):
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def extract_text(self, file_path: str) -> str:
        """Extracts text from a .docx file."""
        try:
            doc = docx.Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return "\n".join(full_text)
        except Exception as e:
            return f"[Error extracting text from {file_path}: {e}]"

    def find_template(self, requested_type: str) -> Optional[dict]:
        """
        Tries to match the requested type against the available templates using
        difflib for a fuzzy match.
        """
        if not self.templates_index:
            return None
        
        # Keys are formatted e.g., 'contrato_arrendamiento_condominio'
        # Let's see if there's an exact match
        query = requested_type.lower().replace(" ", "_")
        if query in self.templates_index:
            return self.templates_index[query]
        
        # If not exact, fuzzy match on keys and descriptions
        keys = list(self.templates_index.keys())
        descriptions = [v["description"].lower() for v in self.templates_index.values()]
        search_corpus = keys + descriptions
        
        matches = get_close_matches(query.replace("_", " "), search_corpus, n=1, cutoff=0.3)
        if matches:
            match = matches[0]
            # If the match is a key
            if match in self.templates_index:
                return self.templates_index[match]
            
            # If the match is a description, find the corresponding key
            for k, v in self.templates_index.items():
                if v["description"].lower() == match:
                    return v

        return None

    def get_template_text(self, requested_type: str) -> Optional[str]:
        """
        Finds the closest template and returns its text content.
        """
        template_info = self.find_template(requested_type)
        if not template_info:
            return None
            
        file_path = os.path.join(self.templates_dir, template_info["file_path"])
        if os.path.exists(file_path):
            return self.extract_text(file_path)
        return None
