import json
import os
from typing import Literal, Union

import openai
import pydantic
import tqdm
from dotenv import load_dotenv

from todoist_react_agent.chat_bot import ChatBot
from todoist_react_agent.models import (
    CreateNewProjectAction,
    GetAllInboxTasksAction,
    GetAllProjectsAction,
    GetAllTasksAction,
    GiveFinalAnswerAction,
    MoveTaskAction,
    ReactResponse,
)
from todoist_react_agent.repair_agent import parse_base_model_with_retries
from todoist_react_agent.todoist_action_toolkit import TodoistActionToolKit


def main() -> None:
    todoist = TodoistActionToolKit(os.getenv("TODOIST_API_KEY"))

    # question = "Are there any duplicate tasks?"
    # question = "Find similiar task in the inbox and move them to the same project. If no good fit exists, create a new project. Ensure the inbox is empty at the end."
    # question = "Based on the tasks in the inbox, create a new project."
    # question = "For all tasks in the inbox, move them to the most relevant project. Create a new project if no good fit exists. Ensure the inbox is empty at the end."
    # question = "Please surest a project name that groups all the tasks in the inbox. Then create that project and move all the tasks in the inbox to that project"
    # question = "Get all the tasks in the inbox. Try to group them into projects. If no project exists, create a new project. Ensure the inbox is empty at the end by moving all the tasks to the projects."
    # question = "Get all tasks in the inbox and try to identify related tasks. Move them to the same project. If no suitable project exist create a new one. Then move all tasks to their project"
    # question = "Get all tasks in the inbox and try to identify related tasks. Please give a suitable project name for these grouping of tasks."
    question = "Get all tasks in the inbox and try to identify related tasks. Think of a suitable project name for these grouping of tasks. If not such project exists create a project. Then move all tasks to their project and ensure the inbox is empty afterwards!"

    system_message = create_system_prompt(ReactResponse, question)
    chatbot = ChatBot(system_message=system_message)

    inputs = json.dumps({"objective": question})
    for _ in tqdm.trange(10):
        raw_response = chatbot(inputs, role="user")
        try:
            response = parse_base_model_with_retries(raw_response, ReactResponse)

            chatbot.set_message_content(-1, json.dumps(response.dict()))

            match response.action:
                case GiveFinalAnswerAction():
                    break
                case GetAllInboxTasksAction():
                    observation = todoist.get_inbox_tasks()
                case GetAllTasksAction():
                    observation = todoist.get_all_tasks()
                case GetAllProjectsAction():
                    observation = todoist.get_all_projects()
                case MoveTaskAction(task_id=task_id, project_id=project_id):
                    todoist.move_task(task_id, project_id)
                    observation = {
                        "Observation": f"Task with id {task_id} moved to project with id {project_id}."
                    }
                case CreateNewProjectAction(project_name=project_name):
                    observation = todoist.create_project(project_name)
                case _:
                    raise ValueError(f"Unknown action {response.action}")
        except ValueError as e:
            print(e)
            observation = {
                "Observation": f"You response caused the following error: {e}. Please try again and avoid this error."
            }
            chatbot.set_message_content(-1, json.dumps(observation))

        inputs = json.dumps({"observation": observation})
        print(inputs)

    print(chatbot.export_conversation())


def create_system_prompt(react_model: pydantic.BaseModel, question: str) -> str:
    return f"""
You are a getting things done (GTD) agent.
It is your job to accomplish the following task: {question}
You have access to multiple tools to accomplish this task.
See the action in the json schema for the available tools.
If you have insufficient information to answer the question, you can use the tools to get more information.
All your answers must be in json format and follow the following schema json schema:
{react_model.schema()}

If your json response asks me to preform an action, I will preform that action.
I will then response with the result of that action.

Let's begin to answer the question: {question}
Do not write anything else than json!
"""


if __name__ == "__main__":
    load_dotenv()
    openai.api_type = "azure"
    openai.api_version = "2023-03-15-preview"
    openai.api_base = os.environ["OPENAI_API_BASE"]
    openai.api_key = os.environ["OPENAI_API_KEY"]

    main()
