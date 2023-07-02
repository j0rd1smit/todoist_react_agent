# ToDoist LLM Agent
This is a proof of concept for an agent that can interact with the ToDoist API and perform actions on the user's behalf.

## Demo

### Accessing your inbox

![acces inbox](assets/acces-inbox.gif)

### Cleaning your inbox
![task management](assets/task_management.gif)

## How it works
This repo use the [react](https://www.promptingguide.ai/techniques/react) framework to allow the agent to reason and act.
This framework forces the agent to responde in the following way:
```
THOUGHT: Here it writes down its reasoning about the task at hand and the observations it has made.
ACTION: Here it writes down the action it wants to perform and optionally the inputs for the action.
OBSERVATION: Here the agent recieves the result of the action it has a preformed.
... This cycle repeats until the agent has completed its task.
FINAL ANSWER: Here the agent writes down the final answer to the question it was asked.
```

### Which actions are available
In this implementation the agent has access to the following actions:
- Get all inbox tasks.
- Get all projects.
- Move task.
- Create new project.

You can find the action definitions in the [models.py](src/models.py) file and the API calls in the [todoist_action_toolkit.py](src/todoist_action_toolkit.py) file.

### How do you force the agent to adhere to the react framework
To force the agent to adhere to the react framework, we give the agent a system prompt that only allows it response using a specific json format.
The idea behind this is as follows:
1. LLMs are very efficient in reading code.
2. JSON schemas (and code in general) are more specific than natural language.
3. JSON is easier to parse and validate than natural language, especially if you use Pydantic.

The system prompt is as follows:
```text
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
```

The schema definition is created using Pydatic. The entire schema can be fond in the [models.py](src/models.py) file. The most important part is the following:
```python
...
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
...
```

### How do you handle agent not adhering to expected format.
LLMs can be very apologetic. 
For example, the agent might first write perfect JSON but followed sorry for not adhering to the JSON format before. 
Or it might not adhere to the expected JSON format in a 100 different ways,
This is a problem since you can no longer parse the JSON.
How do you handle this?
Like always the answer is more AI.
If pydanctic fails to parse the JSON, we give the parsing exception and json schema to another LLM and tell it to fix the JSON:
```python
SYSTEM_PROMPT = f"""
Your task is to fix the FAULTY_INPUT such that it can be parsed into the JSON_SCHEMA.
Use the ERROR_MSG to create a FIXED_INPUT. 
The FIXED_INPUT should be in the same format as the FAULTY_INPUT.
You are only allowed to respond in json format. 
    """.strip()


def parse_base_model_with_retries(
    raw_response: str, base_model: pydantic.BaseModel, retries: int = 3
) -> pydantic.BaseModel:
    chatbot = ChatBot(system_message=SYSTEM_PROMPT, messages=[])

    updated_input_str = raw_response

    for _ in range(retries):
        try:
            return base_model.parse_raw(updated_input_str)
        except Exception as exception:
            updated_input_str = chatbot(
                _format_fix_prompt(updated_input_str, base_model, exception),
                role="assistant",
            )
            logger.warn(
                f"Could not parse input.\nOriginal: {raw_response}\nTry to update the input to: {updated_input_str}"
            )

    raise ValueError(
        f"Failed to repair with retries.\nOriginal input: {raw_response}\nTry to update the input to: {updated_input_str}"
    )


def _format_fix_prompt(
    updated_input_str: str,
    base_model: pydantic.BaseModel,
    exception: Exception,
) -> str:
    return f"""
JSON_SCHEMA:
{base_model.schema()}

FAULTY_INPUT:
{updated_input_str}

ERROR_MSG:
{exception}
FIXED_INPUT:""".strip()
```

The full implementation can be found in the [repair_agent.py](src/repair_agent.py) file.


## How do you handle an agent that makes mistakes?
The agent is not perfect. It will make mistakes. For example, using tasks IDs that do not exist.
How do you handle this?
You raise an exception, and you give the exception message to agent and tell it to fix the problem:
```python
...
try:
    ...
except Exception as e:
    observation = f"You response caused the following error: {e}. Please try again and avoid this error."
...
```


## Running the application yourself
### Setup API keys
The application expects an `.env` file in the root directory with the following keys:
```text
OPENAI_API_BASE=
OPENAI_API_KEY=
TODOIST_API_KEY=
```

The `OPENAI_API_BASE` is the API key to base URL to you Azure OpenAI service. The `OPENAI_API_KEY` is the API key to the Azure OpenAI service. The `TODOIST_API_KEY` is the API key to the ToDoist service. I recommend to use a ToDoist account that is not your main account, since this project is still only a POC. If you decided to use it on your main account I take no responsibility for the concequences


### Install dependencies
All the dependencies are managed by [Poetry](https://python-poetry.org/). To install the dependencies, run the following command:
```bash
poetry install
```

### Run the application
To run the application, run the following command:
```bash
poetry run streamlit run main_streamlit.py
```