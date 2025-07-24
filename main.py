import argparse
import shutil
import sys
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


def main():
    from agents.research_orchestrator import ResearchOrchestrator
    from config import DEFAULT_NUM_PAPERS, DEFAULT_NUM_VMS, OUTPUT_DIR
    
    parser = argparse.ArgumentParser(description="Orgo-based Research Paper Summarization System")
    parser.add_argument("--topic", type=str, help="The research topic to search for (e.g., \"video diffusion models\")")
    parser.add_argument("--num_papers", type=int, default=DEFAULT_NUM_PAPERS,
                        help=f"Number of papers to summarize (default: {DEFAULT_NUM_PAPERS})")
    parser.add_argument("--num_vms", type=int, default=DEFAULT_NUM_VMS,
                        help=f"Number of parallel VMs/agents to use (default: {DEFAULT_NUM_VMS})")

    args = parser.parse_args()

    if args.num_papers > args.num_vms:
        print(f"Error: Number of papers ({args.num_papers}) cannot exceed number of VMs ({args.num_vms}).")
        return

    print(f"Starting research paper summarization for topic: '{args.topic}'")

    orchestrator = ResearchOrchestrator()
    output_file = orchestrator.run(args.topic, args.num_papers, args.num_vms)

    if output_file:
        print(f"\nProcess completed. Output saved to {output_file}")
    else:
        print("\nProcess completed with no output.")

if __name__ == "__main__":
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        print(f"Removing .orgo folder...")
        delete_computer("research_orchestrator")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)