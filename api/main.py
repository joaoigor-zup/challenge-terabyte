import logging
import os
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func, text

from api.database import get_db, create_tables, SessionLocal, test_db_connection
from api.models import Conversation, Message
from api.chat_service import ChatService
from api.config import get_settings, Settings
from api.schemas import (
    ChatRequest, ChatResponse, ConversationSummary, ConversationDetail,
    HealthCheck, SearchRequest, SearchResponse, MessageHistory
)
from api.tools import FUNCTION_MAPPING
from api.utils import vector_to_compare

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)

logger = logging.getLogger(__name__)

# Inicializar configurações
settings = get_settings()

# Inicializar app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Verificar configurações essenciais
if not settings.openai_api_key:
    logger.error("OPENAI_API_KEY não configurada!")
    raise ValueError("OPENAI_API_KEY é obrigatória")

# Inicializar serviço de chat
chat_service = ChatService(settings.openai_api_key)

@app.on_event("startup")
async def startup_event():
    """Inicialização da aplicação."""
    logger.info("Iniciando aplicação...")
    
    # Testar conexão com banco
    if not test_db_connection():
        logger.error("Falha na conexão com banco de dados!")
        raise Exception("Não foi possível conectar ao banco de dados")
    
    # Criar tabelas
    try:
        create_tables()
        logger.info("Tabelas verificadas/criadas com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise
    
    logger.info("Aplicação iniciada com sucesso!")

@app.get("/", response_model=HealthCheck)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Testar conexão com banco
        db.execute(text("SELECT 1"))
        db_status = "connected"
        
        # Verificar tabelas
        tables_result = db.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        tables = [row[0] for row in tables_result]
        
        # Contar registros nas tabelas principais
        conversations_count = db.execute(text("SELECT COUNT(*) FROM conversations")).scalar()
        messages_count = db.execute(text("SELECT COUNT(*) FROM messages")).scalar()
        
        return HealthCheck(
            status="healthy",
            database=db_status,
            timestamp=datetime.utcnow(),
            available_tools=list(FUNCTION_MAPPING.keys()),
            tables=tables,
            conversations_count=conversations_count,
            messages_count=messages_count
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy", 
                "error": str(e),
                "database": "disconnected",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Endpoint principal do chat com RAG."""
    try:
        logger.info(f"Recebida mensagem: {request.message[:100]}...")
        
        response, conversation_id, tools_used, sources_used, total_tokens = chat_service.process_chat_message(
            session=db,
            user_message=request.message,
            conversation_id=request.conversation_id,
            use_history=request.use_history,
            max_history_messages=request.max_history_messages
        )
        
        # Obter ID da mensagem de resposta (último message da conversa)
        last_message = db.execute(
            select(Message).where(Message.conversation_id == conversation_id)
                          .order_by(desc(Message.created_at))
                          .limit(1)
        ).scalar_one_or_none()
        
        message_id = last_message.id if last_message else "unknown"
        
        logger.info(f"Chat processado com sucesso. Conversa: {conversation_id}")
        
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            message_id=message_id,
            tools_used=tools_used,
            sources_used=sources_used,
            total_tokens=total_tokens
        )
        
    except Exception as e:
        logger.error(f"Erro no chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

@app.get("/conversations", response_model=List[ConversationSummary])
def list_conversations(limit: int = 20, db: Session = Depends(get_db)):
    """Lista conversas com resumo."""
    try:
        # Query para buscar conversas com contagem de mensagens
        query = select(
            Conversation,
            func.count(Message.id).label('message_count')
        ).outerjoin(Message).group_by(Conversation.id).order_by(
            desc(Conversation.updated_at)
        ).limit(limit)
        
        results = db.execute(query).all()
        
        conversations = []
        for conversation, message_count in results:
            conversations.append(ConversationSummary(
                id=conversation.id,
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                message_count=message_count or 0
            ))
        
        return conversations
        
    except Exception as e:
        logger.error(f"Erro ao listar conversas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Obtém detalhes de uma conversa específica."""
    try:
        # Buscar conversa
        conversation = db.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversa não encontrada"
            )
        
        # Buscar mensagens
        messages_query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at)
        
        messages = db.execute(messages_query).scalars().all()
        
        message_history = [
            MessageHistory(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                tool_name=msg.tool_name,
                created_at=msg.created_at
            ) for msg in messages
        ]
        
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=message_history
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar conversa: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/search", response_model=SearchResponse)
def search_messages(request: SearchRequest, db: Session = Depends(get_db)):
    """Busca mensagens por similaridade semântica."""
    try:
        results = chat_service.search_similar_messages(
            session=db,
            query_text=request.query,
            limit=request.limit,
            max_distance=1.0 - request.similarity_threshold  # Converter threshold para distância
        )
        
        return SearchResponse(
            results=results,
            query=request.query,
            total_found=len(results)
        )
        
    except Exception as e:
        logger.error(f"Erro na busca: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Deleta uma conversa e todas suas mensagens."""
    try:
        # Verificar se conversa existe
        conversation = db.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversa não encontrada"
            )
        
        # Deletar mensagens primeiro
        messages = db.execute(
            select(Message).where(Message.conversation_id == conversation_id)
        ).scalars().all()
        
        for message in messages:
            db.delete(message)
        
        # Deletar conversa
        db.delete(conversation)
        db.commit()
        
        logger.info(f"Conversa {conversation_id} deletada com sucesso")
        return {"message": "Conversa deletada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar conversa: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Endpoints de teste/debug
@app.get("/test-connection")
def test_connection():
    """Testa conexão com banco de dados."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
            return {
                "message": "DB Connected", 
                "connection": str(session.connection().engine.url).replace(
                    session.connection().engine.url.password or "", "***"
                )
            }
    except Exception as e:
        return {"message": "DB Connection Failed", "error": str(e)}

@app.get("/test-distance")
def test_distance():
    """Testa busca por distância usando dados de exemplo."""
    try:
        with SessionLocal() as session:
            result = []
            
            # Buscar por mensagens similares ao vetor de exemplo
            from api.database import simple_distance_query
            
            for message, distance in simple_distance_query(session, vector_to_compare, limit=5):
                result.append({
                    "message": {
                        "id": message.id, 
                        "content": message.content,
                        "conversation_id": message.conversation_id,
                        "role": message.role
                    },
                    "distance": float(distance),
                    "similarity": round((1 - distance) * 100, 2)
                })
            
            return {"items": result, "total": len(result)}
    except Exception as e:
        logger.error(f"Erro no teste de distância: {e}")
        return {"items": [], "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )