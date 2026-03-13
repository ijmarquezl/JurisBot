
import os
import json
import docx
import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

EXAMPLES_DIR = "/app/ejemplos_legales"

def search_legal_examples(query: str) -> str:
    """
    Searches the 'ejemplos_legales' directory for matching files based on the query.
    Returns a JSON list of matches with 'category', 'filename', and 'score'.
    """
    try:
        if not os.path.exists(EXAMPLES_DIR):
             return json.dumps({"error": f"Directory not found: {EXAMPLES_DIR}"})

        query_terms = query.lower().split()
        matches = []

        # Traverse directories
        logger.info(f"DEBUG: Walking {EXAMPLES_DIR}")
        for root, dirs, files in os.walk(EXAMPLES_DIR):
            category = os.path.basename(root)
            logger.info(f"DEBUG: Visiting {category} (Files: {len(files)})")
            
            for file in files:
                if not file.endswith(".docx"):
                    continue
                
                score = 0
                file_lower = file.lower()
                
                # Simple keyword matching scoring
                for term in query_terms:
                    if term in file_lower:
                        score += 5
                    if term in category.lower():
                        score += 2
                
                if score > 0:
                    logger.info(f"DEBUG: Match found {file} score {score}")
                    matches.append({
                        "category": category,
                        "filename": file,
                        "filepath": os.path.join(root, file), # Absolute path internal
                        "score": score
                    })
        
        # Sort by score desc
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top 5
        return json.dumps(matches[:5])

    except Exception as e:
        logger.error(f"Error searching examples: {e}")
        return json.dumps({"error": str(e)})

def read_legal_example(category: str, filename: str) -> str:
    """
    Reads the content of a specific legal example file.
    Args:
        category: The subdirectory name (e.g., 'Demandas', 'Contratos')
        filename: The name of the file
    """
    try:
        # Construct path safely
        # If category is Root, just join filename
        if category == "Root":
             file_path = os.path.join(EXAMPLES_DIR, filename)
        else:
             file_path = os.path.join(EXAMPLES_DIR, category, filename)
        
        if not os.path.exists(file_path):
             # Try recursive search if path construction failing? No, strict is better for tools.
             return json.dumps({"error": f"File not found: {file_path}"})

        doc = docx.Document(file_path)
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        
        return json.dumps({"content": full_text})
        
    except Exception as e:
        logger.error(f"Error reading example: {e}")
        return json.dumps({"error": str(e)})

def start_drafting(topic: str) -> str:
    """
    Placeholder function to signal drafting intent.
    The actual routing logic in the graph handles the switch to the Drafter Sub-graph.
    """
    return json.dumps({"status": "drafting_started", "topic": topic})

# Test if running directly
if __name__ == "__main__":
    print(search_legal_examples("amparo"))
