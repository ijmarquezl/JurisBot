import requests
import json
import os
import re
import docx
from datetime import datetime

# This module defines the tools the AI agent can use.
# Each function in this module corresponds to a tool.
# The function's docstring is crucial as it will be used by the LLM to understand what the tool does.

_auth_token = None
API_BASE_URL = "http://127.0.0.1:8000"
TEMPLATE_DIR = "../formatos/"
GENERATED_DOCS_PATH = "../documentos_generados/"

def set_auth_token(token: str):
    """Sets the authentication token for the API calls."""
    global _auth_token
    _auth_token = token

def _get_headers():
    """Helper function to get authentication headers."""
    if not _auth_token:
        raise Exception("Authentication token not set.")
    return {
        "Authorization": f"Bearer {_auth_token}",
        "Content-Type": "application/json",
    }

def get_template_placeholders(template_name: str) -> str:
    """
    Reads a .docx template file and extracts all placeholders in the format {{placeholder}}.
    Use this tool to find out what information is needed to fill a document template.
    The user must provide the full template name, for example: 'FORMATO DE DEMANDA CIVIL EN GENERAL.docx'.

    Args:
        template_name (str): The name of the template file (e.g., "my_template.docx").

    Returns:
        str: A JSON string containing a list of unique placeholders found in the document.
    """
    try:
        template_path = os.path.join(TEMPLATE_DIR, template_name)
        if not os.path.exists(template_path):
            return json.dumps({"error": f"Template '{template_name}' not found in '{TEMPLATE_DIR}'."})

        doc = docx.Document(template_path)
        placeholders = set()
        placeholder_regex = re.compile(r"{{(.*?)}}")

        for para in doc.paragraphs:
            for match in placeholder_regex.finditer(para.text):
                placeholders.add(match.group(1).strip())

        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        for match in placeholder_regex.finditer(para.text):
                            placeholders.add(match.group(1).strip())
        
        if not placeholders:
             return json.dumps({"error": f"No placeholders like '{{field}}' found in the template '{template_name}'."})

        return json.dumps(list(placeholders))
    except Exception as e:
        return json.dumps({"error": f"Failed to read template and extract placeholders. {e}"})

def fill_template_and_save_document(template_name: str, project_id: str, document_name: str, context: dict) -> str:
    """
    Fills a .docx template with the provided context and saves it as a new document.
    This is the final step in the document generation workflow.

    Args:
        template_name (str): The name of the template file (e.g., "FORMATO DE DEMANDA CIVIL EN GENERAL.docx").
        project_id (str): The ID of the project this document belongs to.
        document_name (str): The desired name for the new document (without extension).
        context (dict): A dictionary where keys are the placeholder names and values are the text to insert.

    Returns:
        str: A JSON string with the path to the newly created document or an error message.
    """
    # Guard to prevent premature execution
    if not document_name or not project_id or not context:
        return json.dumps({"error": "This tool was called too early. You must collect all information from the user (placeholders, document_name, project_id) BEFORE calling this tool."})

    try:
        template_path = os.path.join(TEMPLATE_DIR, template_name)
        if not os.path.exists(template_path):
            return json.dumps({"error": f"Template '{template_name}' not found."})

        doc = docx.Document(template_path)

        # Replace placeholders in paragraphs
        for para in doc.paragraphs:
            for key, value in context.items():
                search_text = f"{{{{{key}}}}}"
                if search_text in para.text:
                    para.text = para.text.replace(search_text, str(value))

        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        for key, value in context.items():
                            search_text = f"{{{{{key}}}}}"
                            if search_text in para.text:
                                para.text = para.text.replace(search_text, str(value))

        # Save the new document
        new_file_name = f"{document_name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.docx"
        new_file_path = os.path.join(GENERATED_DOCS_PATH, new_file_name)
        doc.save(new_file_path)

        # Register the new document in the database via API call
        register_payload = {
            "file_name": document_name,
            "project_id": project_id,
            "file_path": new_file_path
        }
        response = requests.post(f"{API_BASE_URL}/documents/register", headers=_get_headers(), json=register_payload)
        response.raise_for_status()
        
        return json.dumps({"success": True, "file_path": new_file_path, "details": response.json()})

    except Exception as e:
        return json.dumps({"error": f"Failed to fill and save document. {e}"})

def list_projects() -> str:
    """
    Lists all the projects the user is a member of.
    Use this tool when the user asks to see their projects.
    
    Returns:
        str: A JSON string representing the list of projects, including their names and IDs.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/projects/", headers=_get_headers())
        response.raise_for_status()
        projects = response.json()
        return json.dumps(projects)
    except Exception as e:
        return json.dumps({"error": f"Failed to list projects. {e}"})

def create_project(name: str, description: str = None) -> str:
    """
    Creates a new project with a given name and an optional description.
    Use this tool when the user explicitly asks to create a new project.
    
    Args:
        name (str): The name of the new project. This is a required parameter.
        description (str, optional): An optional description for the project.
        
    Returns:
        str: A JSON string representing the newly created project.
    """
    try:
        payload = {"name": name, "description": description}
        response = requests.post(f"{API_BASE_URL}/projects/", headers=_get_headers(), json=payload)
        response.raise_for_status()
        project_data = response.json()
        return json.dumps(project_data)
    except Exception as e:
        return json.dumps({"error": f"Failed to create project. {e}"})

def create_task(project_id: str, title: str, description: str = None) -> str:
    """
    Creates a new task in a specific project using its ID.
    To use this tool, you must know the ID of the project. You can get the project ID by using the 'list_projects' tool first.
    
    Args:
        project_id (str): The ID of the project where the task will be created.
        title (str): The title of the new task.
        description (str, optional): An optional description for the task.
        
    Returns:
        str: A JSON string representing the newly created task.
    """
    try:
        payload = {"title": title, "description": description}
        task_response = requests.post(f"{API_BASE_URL}/tasks/projects/{project_id}", headers=_get_headers(), json=payload)
        task_response.raise_for_status()
        task_data = task_response.json()
        return json.dumps(task_data)
    except Exception as e:
        return json.dumps({"error": f"Failed to create task. {e}"})


def list_tasks(project_id: str) -> str:
    """
    Lists all tasks for a specific project using its ID.
    To use this tool, you must know the ID of the project. You can get the project ID by using the 'list_projects' tool first.
    
    Args:
        project_id (str): The ID of the project to list tasks from.
        
    Returns:
        str: A JSON string representing the list of tasks.
    """
    try:
        task_response = requests.get(f"{API_BASE_URL}/tasks/projects/{project_id}", headers=_get_headers())
        task_response.raise_for_status()
        tasks_data = task_response.json()
        return json.dumps(tasks_data)
    except Exception as e:
        return json.dumps({"error": f"Failed to list tasks. {e}"})


def list_documents() -> str:
    """

    Lists all generated documents the user has access to.
    Use this tool when the user asks to see their documents.
    
    Returns:
        str: A JSON string representing the list of documents.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/documents/", headers=_get_headers())
        response.raise_for_status()
        documents = response.json()
        return json.dumps(documents)
    except Exception as e:
        return json.dumps({"error": f"Failed to list documents. {e}"})