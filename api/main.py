import logging

from fastapi import FastAPI
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from api.database import SessionLocal, simples_distance_query
from api.models.chatrequest import ChatRequest
from api.utils import vector_to_compare
from api.openai.openaiservice import chat_execute

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

app = FastAPI()


@app.get("/")
def entrypoint():
    with SessionLocal() as session:
        return {"message": "DB Connected",
                "connection": str(session.connection().engine.url.render_as_string(hide_password=True))}


@app.get("/test-distance")
def test_distance():
    with SessionLocal() as session:
        result = []

        for memory, distance in simples_distance_query(
                session, vector_to_compare
        ):
            result.append({"memory": {"id": memory.id, "content": memory.content}, "proximity": (1 - distance) * 100})
        return {"items": result}


@app.post("/marceloreiszup/chat")
def chat(message: ChatRequest):

    ## aqui quero salvar a string da mensagem do usuario no banco vector

    return chat_execute(message.query)

