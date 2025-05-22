import logging

from fastapi import FastAPI

from api.database import SessionLocal, simples_distance_query
from api.utils import vector_to_compare
from api.models import ChatRequest
from api.chat import chat


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
        result = []

        for memory, distance in simples_distance_query(
                session, vector_to_compare
        ):
            result.append({"memory": {"id": memory.id, "content": memory.content }, "proximity": (1 - distance) * 100})
        return {"items": result}


@app.post("/v1/chat")
def post_v1_chat(req: ChatRequest):
    message = req.message
    
    answer = chat(message)
        
    return answer
