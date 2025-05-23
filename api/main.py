import logging

from fastapi import FastAPI

from api import llmService
from api.database import SessionLocal, simpleDistanceQuery
from api.requests import ChatRequest
from api.utils import vectorToCompare

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


@app.get("/test_distance")
def testDistance():
    with SessionLocal() as session:
        result = []

        for memory, distance in simpleDistanceQuery(
                session, vectorToCompare
        ):
            result.append({"memory": {"id": memory.id, "content": memory.content }, "proximity": (1 - distance) * 100})
        return {"items": result}


@app.post("/chat")
def chatWithLlm(request: ChatRequest)-> str:
    return llmService.postChat(request.message)
