from logging import getLogger

import datetime
import ollama as llm
from sqlalchemy.orm import Session
from ulid import ulid

from api.database import Memory, SessionLocal, simpleDistanceQuery

import json
import os

DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "mistral")
logger = getLogger(__name__)

FIXED_SYSTEM_PROMPT = {"role": "system", "content": "You are a helpful LLM assistant. Reply with short sentenses. Call the provided tools if needed"}

def getCurrentDateAndTime() -> datetime.datetime:
    """
    Gets the current date and time

    Returns:
        datetime: The current date and time
    """
    now = datetime.datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

getCurrentDateAndTimeTool = {
    "type": "function",
    "function": {
        "name": "getCurrentDateAndTime",
        "description": "Gets the current date and time",
        "parameters": {
        },
    },
}

availableFunctions = {
    'getCurrentDateAndTime': getCurrentDateAndTime,
}

def _saveMemory(message: dict, embed: list[float]):
    with SessionLocal() as session:
        memory = Memory(id=ulid(), content=json.dumps(message), vector=embed)
        session.add(memory)
        session.commit()


def _embed(message: dict) -> list[float]:
    return llm.embed(model=DEFAULT_MODEL, input=message["content"]).embeddings[0]

def _getRelevantMessages(embed: list[float]) -> list[dict]:
    with SessionLocal() as session:
        messagesWithPercentages = simpleDistanceQuery(session, embed, limit=10, max_distance=0.7)

        return [json.loads(x[0].content) for x in messagesWithPercentages.all()]

def _callLlm(messages: list[dict]):
    while True:
        response = llm.chat(DEFAULT_MODEL, messages, tools=[getCurrentDateAndTimeTool])
        if response.message.tool_calls:
            for tool in response.message.tool_calls:
                if function_to_call := availableFunctions.get(tool.function.name):
                    logger.info("Calling tool")
                    result = function_to_call(**tool.function.arguments)
                    messages.append({"role": "tool", "content": result})
            else:
                print("Function", tool.function.name, "not found")
        else:
            return response

def postChat(message: str):
    messages = [FIXED_SYSTEM_PROMPT]
    userJson = {"role": "user", "content": message}
    userEmbed = _embed(userJson)
    messages.extend(_getRelevantMessages(userEmbed))
    messages.append(userJson)

    logger.info(f"Sending messages to LLM: {messages}")
    response = _callLlm(messages)
    logger.info(f"Received from LLM: {response}")

    llmEmbed = _embed(response.message)
    logger.info("LLM embeddings created")
    _saveMemory(userJson, userEmbed)
    _saveMemory({"role": "assistant", "content": response.message.content}, llmEmbed)
    return response.message.content
