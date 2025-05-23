import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func, text
from openai import OpenAI
from ulid import ulid

from api.models import Conversation, Message
from api.database import simple_distance_query
from api.tools import AVAILABLE_TOOLS, execute_tool
from api.schemas import ChatMessage, MessageHistory, SearchResult

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-3-large"
        self.chat_model = "gpt-4o-mini"  # Modelo mais econômico
        
    def get_embedding(self, text: str) -> List[float]:
        """Gera embedding para um texto usando OpenAI."""
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return []
    
    def create_or_get_conversation(self, session: Session, conversation_id: Optional[str] = None) -> Conversation:
        """Cria uma nova conversa ou retorna uma existente."""
        try:
            if conversation_id:
                conversation = session.get(Conversation, conversation_id)
                if conversation:
                    return conversation
            
            # Cria nova conversa
            conversation = Conversation(
                id=str(ulid()),
                title=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
            logger.info(f"Nova conversa criada: {conversation.id}")
            return conversation
        except Exception as e:
            logger.error(f"Erro ao criar/obter conversa: {e}")
            session.rollback()
            raise
    
    def save_message(self, session: Session, conversation_id: str, role: str, content: str, 
                    tool_name: Optional[str] = None, tool_call_id: Optional[str] = None) -> Message:
        """Salva uma mensagem no banco de dados com embedding."""
        try:
            # Gerar embedding apenas se o conteúdo não estiver vazio
            embedding = None
            if content and content.strip():
                embedding = self.get_embedding(content)
            
            message = Message(
                id=str(ulid()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                embedding=embedding if embedding else None,
                tool_name=tool_name,
                tool_call_id=tool_call_id,
                created_at=datetime.utcnow()
            )
            
            session.add(message)
            session.commit()
            session.refresh(message)
            logger.info(f"Mensagem salva: {message.id} - {role}")
            return message
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem: {e}")
            session.rollback()
            raise
    
    def get_conversation_history(self, session: Session, conversation_id: str, limit: int = 10) -> List[MessageHistory]:
        """Recupera o histórico de uma conversa."""
        try:
            query = select(Message).where(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).limit(limit)
            
            messages = session.execute(query).scalars().all()
            
            return [
                MessageHistory(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    tool_name=msg.tool_name,
                    created_at=msg.created_at
                ) for msg in messages
            ]
        except Exception as e:
            logger.error(f"Erro ao recuperar histórico: {e}")
            return []
    
    def search_similar_messages(self, session: Session, query_text: str, 
                               conversation_id: Optional[str] = None,
                               limit: int = 5, max_distance: float = 0.7) -> List[SearchResult]:
        """Busca mensagens similares usando embeddings para implementar RAG."""
        try:
            query_embedding = self.get_embedding(query_text)
            if not query_embedding:
                return []
            
            results = []
            
            # Busca por similaridade usando pgvector
            distance = Message.embedding.cosine_distance(query_embedding).label("distance")
            
            query = select(Message, distance).where(
                Message.embedding.isnot(None)
            ).where(
                distance < max_distance
            )
            
            # Se temos uma conversa específica, incluir mensagens dela também
            if conversation_id:
                # Buscar tanto mensagens similares globalmente quanto da conversa atual
                query = query.where(
                    Message.conversation_id != conversation_id  # Evitar duplicatas
                )
            
            query = query.order_by(distance.asc()).limit(limit)
            
            query_result = session.execute(query)
            
            for message, distance in query_result:
                similarity = (1 - distance) * 100  # Converte distância em similaridade percentual
                results.append(SearchResult(
                    message_id=message.id,
                    content=message.content,
                    similarity=round(similarity, 2),
                    created_at=message.created_at,
                    conversation_id=message.conversation_id
                ))
            
            logger.info(f"Encontradas {len(results)} mensagens similares")
            return results
        except Exception as e:
            logger.error(f"Erro na busca por similaridade: {e}")
            return []
    
    def format_messages_for_openai(self, messages: List[MessageHistory]) -> List[Dict[str, Any]]:
        """Formata mensagens para o formato esperado pela OpenAI."""
        formatted = []
        for msg in messages:
            if msg.role in ['user', 'assistant']:
                formatted.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif msg.role == 'tool' and msg.tool_name:
                formatted.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id or msg.tool_name
                })
        return formatted
    
    def build_rag_context(self, similar_messages: List[SearchResult], conversation_history: List[MessageHistory]) -> str:
        """Constrói o contexto RAG combinando mensagens similares e histórico."""
        context_parts = []
        
        if similar_messages:
            context_parts.append("=== CONTEXTO DE CONVERSAS ANTERIORES ===")
            for msg in similar_messages:
                context_parts.append(f"[Similaridade: {msg.similarity}%] {msg.content}")
        
        if conversation_history:
            context_parts.append("\n=== HISTÓRICO DA CONVERSA ATUAL ===")
            for msg in conversation_history[:-1]:  # Excluir a última mensagem (atual)
                context_parts.append(f"[{msg.role.upper()}]: {msg.content}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def process_chat_message(self, session: Session, user_message: str, 
                           conversation_id: Optional[str] = None, 
                           use_history: bool = True, 
                           max_history_messages: int = 10) -> Tuple[str, str, List[str], List[str], Optional[int]]:
        """
        Processa uma mensagem de chat completa com RAG.
        
        Returns:
            Tuple com (resposta, conversation_id, tools_used, sources_used, total_tokens)
        """
        try:
            # Criar ou recuperar conversa
            conversation = self.create_or_get_conversation(session, conversation_id)
            
            # Salvar mensagem do usuário
            user_msg = self.save_message(session, conversation.id, "user", user_message)
            
            # Buscar contexto relevante do histórico (RAG)
            sources_used = []
            rag_context = ""
            
            if use_history:
                # Buscar mensagens similares de todas as conversas para RAG
                similar_messages = self.search_similar_messages(
                    session, user_message, 
                    conversation_id=conversation.id,
                    limit=3
                )
                
                # Buscar histórico da conversa atual
                history = self.get_conversation_history(session, conversation.id, max_history_messages)
                
                # Construir contexto RAG
                rag_context = self.build_rag_context(similar_messages, history)
                
                # Registrar fontes utilizadas
                for result in similar_messages:
                    sources_used.append(f"Conversa {result.conversation_id[:8]} ({result.similarity}%)")
            
            # Preparar mensagens para OpenAI
            messages = [
                {
                    "role": "system",
                    "content": f"""Você é um assistente inteligente que aprende com conversas anteriores.

IMPORTANTE: Use o contexto fornecido para dar respostas mais precisas e relevantes. Quando apropriado, referencie informações anteriores naturalmente.

Você tem acesso a ferramentas úteis:
- calculator: Para cálculos matemáticos
- get_current_datetime: Para obter data/hora atual
- text_analyzer: Para analisar textos  
- search_knowledge_base: Para buscar informações técnicas

{f"CONTEXTO RELEVANTE:\\n{rag_context}" if rag_context else ""}"""
                },
                {
                    "role": "user", 
                    "content": user_message
                }
            ]
            
            # Chamada para OpenAI com tools
            tools_used = []
            total_tokens = 0
            
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                tools=AVAILABLE_TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000
            )
            
            total_tokens = response.usage.total_tokens if response.usage else 0
            assistant_message = response.choices[0].message
            
            # Processar tool calls se houver
            final_content = assistant_message.content or ""
            
            if assistant_message.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        } for tool_call in assistant_message.tool_calls
                    ]
                })
                
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Executar a tool
                    tool_result = execute_tool(tool_name, tool_args)
                    tools_used.append(tool_name)
                    
                    # Salvar chamada da tool
                    self.save_message(
                        session, conversation.id, "tool", 
                        f"Executou {tool_name}({tool_args}) -> {tool_result}",
                        tool_name=tool_name,
                        tool_call_id=tool_call.id
                    )
                    
                    # Adicionar resultado da tool às mensagens
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                
                # Segunda chamada para obter resposta final
                final_response = self.client.chat.completions.create(
                    model=self.chat_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )
                
                if final_response.usage:
                    total_tokens += final_response.usage.total_tokens
                
                final_content = final_response.choices[0].message.content or ""
            
            # Salvar resposta do assistente
            assistant_msg = self.save_message(session, conversation.id, "assistant", final_content)
            
            # Atualizar timestamp da conversa
            conversation.updated_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"Chat processado com sucesso. Tokens: {total_tokens}")
            return final_content, conversation.id, tools_used, sources_used, total_tokens
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            session.rollback()
            error_response = f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"
            try:
                self.save_message(session, conversation.id, "assistant", error_response)
            except:
                pass  # Se não conseguir salvar erro, apenas retornar
            return error_response, conversation.id if 'conversation' in locals() else "", [], [], None