from typing import Dict, Any

from orgo.project import ProjectManager
from orgo.api.client import ApiClient

def delete_computer(project_id: str) -> Dict[str, Any]:
    """
    Custom function to delete a computer/project instance.

    Args:
        project_id (str): ID of the project to delete

    Returns:
        Dict[str, Any]: Response from the delete operation

    Raises:
        Exception: If API request fails
    """
    try:
        client = ApiClient()
        print(f"Deleting computer/project: {project_id}")
        result = client._request("POST", f"projects/{project_id}/delete")
        ProjectManager.clear_project_cache()
        print(f"Successfully deleted computer: {project_id}")
        return result

    except Exception as e:
        print(f"Error deleting computer {project_id}: {str(e)}")
        raise
