from pydantic import BaseModel

class ChatRequest(BaseModel):
    mensagem: str
