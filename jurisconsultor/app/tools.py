import requests
import json

# This module defines the tools the AI agent can use.
# Each function in this module corresponds to a tool.
# The function's docstring is crucial as it will be used by the LLM to understand what the tool does.

_auth_token = None
API_BASE_URL = "http://127.0.0.1:8000"

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