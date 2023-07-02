import os

from dotenv import load_dotenv
from todoist_api_python.api import Project, TodoistAPI

from todoist_react_agent.todoist_action_toolkit import _move_task_api_call


def main() -> None:
    """Simple script that move all tasks to inbox and delete all projects except inbox"""

    load_dotenv()
    todoist = TodoistAPI(os.getenv("TODOIST_API_KEY"))

    inbox_project = get_inbox_project(todoist)

    for task in todoist.get_tasks():
        _move_task_api_call(task.id, inbox_project.id)

    for project in todoist.get_projects():
        if project.name.lower() != "inbox":
            todoist.delete_project(project.id)


def get_inbox_project(todoist) -> Project:
    projects = todoist.get_projects()
    for project in projects:
        if project.name.lower() == "inbox":
            return project
    raise ValueError("No inbox found")


if __name__ == "__main__":
    main()
