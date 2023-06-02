import json
import os
import uuid
from datetime import datetime
from functools import cache
from typing import Any

import pydantic as pydantic
import requests
from dateutil import parser
from todoist_api_python.api import Project, TodoistAPI


class TodoistActionToolKit:
    def __init__(self, api_key: str) -> None:
        self.api = TodoistAPI(api_key)

    @property
    @cache
    def inbox_id(self) -> str:
        projects = self.api.get_projects()
        for project in projects:
            if project.name.lower() == "inbox":
                return project.id
        raise ValueError("No inbox found")

    @property
    def _todoist_project_id_to_project_name(self) -> dict[str, str]:
        todoist_projects = self.api.get_projects()
        return {project.id: project.name for project in todoist_projects}

    def get_all_projects(self) -> list[dict[str, Any]]:
        return [project for project in self._get_all_projects()]

    def _get_all_projects(self) -> list[dict[str, str]]:
        results = []
        for project in self.api.get_projects():
            results.append(self._format_project(project))

        return results

    def _format_project(self, project: Project) -> dict[str, str]:
        return {
            "name": project.name,
            "project_id": project.id,
            "is_inbox": project.is_inbox_project,
        }

    def get_all_tasks(self) -> list[dict[str, Any]]:
        return [
            task
            for task in self._get_all_tasks()
            if task["project_id"] != self.inbox_id
        ]

    def _get_all_tasks(self) -> list[dict[str, str]]:
        results = []
        for task in self.api.get_tasks():
            results.append(
                {
                    "name": task.content,
                    "task_id": task.id,
                    "project_id": task.project_id,
                    "created": create_human_friendly_date(task.created_at),
                    "project_name": self._todoist_project_id_to_project_name[
                        task.project_id
                    ],
                }
            )

        return results

    def get_inbox_tasks(self) -> list[dict[str, Any]]:
        return [
            task
            for task in self._get_all_tasks()
            if task["project_id"] == self.inbox_id
        ]

    def create_project(self, name: str) -> dict[str, Any]:
        for project in self.api.get_projects():
            if project.name.lower() == name.lower():
                raise ValueError(f"Project {name} already exists.")
        project = self.api.add_project(name)
        return self._format_project(project)

    def move_task(self, task_id: str, project_id: str) -> None:
        task = self._get_task(task_id)
        project = self._get_project(project_id)

        if task["project_id"] == project_id:
            raise ValueError(
                f"Task {task_id} is already in project {project_id}. No need to move it."
            )

        return _move_task_api_call(task_id, project_id)

    def _get_task(self, task_id) -> dict[str, str]:
        for task in self._get_all_tasks():
            if task["task_id"] == task_id:
                return task
        raise ValueError(f"Task {task_id} does not exist.")

    def _get_project(self, project_id) -> dict[str, str]:
        for project in self._get_all_projects():
            if project["project_id"] == project_id:
                return project
        raise ValueError(f"Project {project_id} does not exist.")


def create_human_friendly_date(date: str) -> str:
    input_datetime = parser.isoparse(date)
    now = datetime.utcnow().replace(tzinfo=input_datetime.tzinfo)
    diff = now - input_datetime

    if diff.total_seconds() > 24 * 3600:
        return f"{int(diff.total_seconds() / (24 * 3600))} days ago"
    elif diff.total_seconds() > 3600:
        return f"{int(diff.total_seconds() / 3600)} hours ago"
    elif diff.total_seconds() > 60:
        return f"{int(diff.total_seconds() / 60)} minutes ago"

    return "Just now"


def _move_task_api_call(task_id: str, project_id: str):
    body = {
        "commands": [
            {
                "type": "item_move",
                "args": {"id": task_id, "project_id": project_id},
                "uuid": uuid.uuid4().hex,
            },
        ],
    }
    response = requests.post(
        "https://api.todoist.com/sync/v9/sync",
        headers={"Authorization": f"Bearer {os.getenv('TODOIST_API_KEY')}"},
        json=body,
    )
    if response.status_code >= 400:
        raise ValueError(
            f"Error failed to move task {task_id} to project {project_id}. Error: {response.text}"
        )

    return response.json()
