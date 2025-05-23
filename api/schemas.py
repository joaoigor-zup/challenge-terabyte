from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    role: str = Field(..., description="Papel da mensagem: 'user', 'assistant', ou 'tool'")
    content: str = Field(..., description="Conteúdo da mensagem")
    tool_name: Optional[str] = Field(None, description="Nome da tool se aplicável")
    tool_call_id: Optional[str] = Field(None, description="ID da chamada da tool se aplicável")

class ChatRequest(BaseModel):
    message: str = Field(..., description="Mensagem do usuário")
    conversation_id: Optional[str] = Field(None, description="ID da conversa (opcional, será criado se não fornecido)")
    use_history: bool = Field(True, description="Se deve usar o histórico da conversa")
    max_history_messages: int = Field(10, description="Máximo de mensagens do histórico para considerar")

class ConversationSummary(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int

class ChatResponse(BaseModel):
    response: str = Field(..., description="Resposta do assistente")
    conversation_id: str = Field(..., description="ID da conversa")
    message_id: str = Field(..., description="ID da mensagem de resposta")
    tools_used: List[str] = Field(default_factory=list, description="Lista de tools utilizadas")
    sources_used: List[str] = Field(default_factory=list, description="Fontes do histórico utilizadas")
    total_tokens: Optional[int] = Field(None, description="Total de tokens utilizados")

class MessageHistory(BaseModel):
    id: str
    role: str
    content: str
    tool_name: Optional[str]
    created_at: datetime

class ConversationDetail(BaseModel):
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageHistory]

class HealthCheck(BaseModel):
    status: str
    database: str
    timestamp: datetime
    available_tools: List[str]

class SearchRequest(BaseModel):
    query: str = Field(..., description="Termo de busca")
    limit: int = Field(5, description="Número máximo de resultados")
    similarity_threshold: float = Field(0.7, description="Limiar de similaridade para busca")

class SearchResult(BaseModel):
    message_id: str
    content: str
    similarity: float
    created_at: datetime
    conversation_id: str

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_found: int