from pydantic import BaseModel

# Example request body
class ChatRequest(BaseModel):
    message: str