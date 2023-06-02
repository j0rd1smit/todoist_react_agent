import pydantic

from todoist_react_agent.chat_bot import ChatBot
from todoist_react_agent.logger import logger

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
