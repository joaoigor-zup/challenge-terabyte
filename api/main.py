import logging

from ulid import ulid
from fastapi import FastAPI

from langchain.schema import SystemMessage, HumanMessage, AIMessage, BaseMessage

from api.database import SessionLocal
from api.repository import HistoryEntity, HistoryRepository
from api.utils import vector_to_compare

from api.models import ChatRequest
import api.chat
import api.chat_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app = FastAPI()


@app.get("/")
def entrypoint():
    with SessionLocal() as session:
        return {"message": "DB Connected", "connection": str(session.connection().engine.url.render_as_string(hide_password=True))}


@app.get("/test-distance")
def test_distance():
    with SessionLocal() as session:
        repository = HistoryRepository(session)
        result = []

        for memory, distance in repository.simple_distance_query(
                vector_to_compare
        ):
            result.append({"memory": {"id": memory.id, "content": memory.content }, "proximity": (1 - distance) * 100})
        return {"items": result}


@app.post("/v1/chat")
def chat(message: ChatRequest):
    user_message_vector = api.chat.embed(message.query)
    messages: list[BaseMessage] = []

    logging.info(f"Embedded Vector ${user_message_vector}")
    with SessionLocal() as session:
        repository = HistoryRepository(session)

        rag_history = repository.simple_distance_query(query_vector = user_message_vector, limit = 10)
        for rag, distance in rag_history:
            logging.info(f"Retrieved history: {rag.content} - distance {distance}")
            messages.append(SystemMessage(content=f"RELEVANT DATA: {rag.content}"))
        
        logging.info(f"RAG size: {len(messages)}")
        messages.append(HumanMessage(content=message.query))
        chat_response = api.chat.call_chat(messages)
        api_vector = api.chat.embed(chat_response.content)

        repository.create(content = message.query, vector = user_message_vector)
        repository.create(content = chat_response.content, vector = api_vector)

    return chat_response

@app.post("/v1/chat/tool")
def chat_tool(message: ChatRequest):
    return api.chat_tool.call_chat_tool([HumanMessage(content=message.query)])