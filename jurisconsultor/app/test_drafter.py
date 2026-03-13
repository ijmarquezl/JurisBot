
import sys
import os
import json
import logging

# Add /app to path so we can import app modules
sys.path.append("/app")

# Configure logging
logging.basicConfig(level=logging.INFO)

from infrastructure.ai.tools.drafter_tools import search_legal_examples, read_legal_example

def test_tools():
    print("--- Testing Search ---")
    query = "amparo"
    search_res = search_legal_examples(query)
    print(f"Search Result: {search_res}")
    
    results = json.loads(search_res)
    if not results or "error" in results:
        print("Search failed or returned error.")
        return

    first_match = results[0]
    print(f"First match: {first_match}")
    
    print("\n--- Testing Read ---")
    # Note: 'category' in the matched result might need to be passed correctly
    category = first_match['category']
    filename = first_match['filename']
    
    print(f"Reading category='{category}', filename='{filename}'")
    content_res = read_legal_example(category, filename)
    
    # Print first 200 chars only
    content_json = json.loads(content_res)
    if "error" in content_json:
        print(f"Read Error: {content_json['error']}")
    else:
        content = content_json.get("content", "")
        print(f"Read Success. Content length: {len(content)}")
        print(f"Preview: {content[:200]}")

if __name__ == "__main__":
    test_tools()
