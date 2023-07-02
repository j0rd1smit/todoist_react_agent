from typing import Literal, Union

import pydantic as pydantic


class GetAllTasksAction(pydantic.BaseModel):
    """Use this to get all open tasks that are not in the inbox."""

    type: Literal["get_all_tasks"]


class GetAllInboxTasksAction(pydantic.BaseModel):
    """Use this to get all open tasks that are in the inbox."""

    type: Literal["get_all_inbox_tasks"]


class GetAllProjectsAction(pydantic.BaseModel):
    """Use this when you want to get all the projects."""

    type: Literal["get_all_projects"]


class MoveTaskAction(pydantic.BaseModel):
    """Use this to move a task to a project."""

    type: Literal["move_task"]
    task_id: str = pydantic.Field(
        description="The task id obtained from the"
        + " get_all_tasks or get_all_inbox_tasks action.",
        regex=r"^[0-9]+$",
    )
    project_id: str = pydantic.Field(
        description="The project id obtained from the " + "get_all_projects action.",
        regex=r"^[0-9]+$",
    )


class GiveFinalAnswerAction(pydantic.BaseModel):
    """Use this to give the final answer. Only use it when your work is done."""

    type: Literal["give_final_answer"]
    answer: str = pydantic.Field(
        description="The final answer to the question. If you have writen you answer thought, please repeat it here.",
        min_length=3,
    )


class CreateNewProjectAction(pydantic.BaseModel):
    """Use this to create a new project."""

    type: Literal["create_new_project"]
    project_name: str = pydantic.Field(
        description="The name of the project. Project names description of multiple tasks. e.g., 'Do groceries', 'Implement feature X', etc.",
        min_length=3,
    )


class ReactResponse(pydantic.BaseModel):
    """The expected response from the agent."""

    thought: str = pydantic.Field(
        description="Here you write your plan to answer the question. You can also write here your interpretation of the observations and progress you have made so far."
    )
    action: Union[
        GetAllTasksAction,
        GetAllProjectsAction,
        CreateNewProjectAction,
        GetAllInboxTasksAction,
        MoveTaskAction,
        GiveFinalAnswerAction,
    ] = pydantic.Field(
        description="The next action you want to take. Make sure it is consistent with your thoughts."
    )
