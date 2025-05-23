import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
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
        return conversation
    
    def save_message(self, session: Session, conversation_id: str, role: str, content: str, 
                    tool_name: Optional[str] = None, tool_call_id: Optional[str] = None) -> Message:
        """Salva uma mensagem no banco de dados com embedding."""
        embedding = self.get_embedding(content) if content.strip() else []
        
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
        return message
    
    def get_conversation_history(self, session: Session, conversation_id: str, limit: int = 10) -> List[MessageHistory]:
        """Recupera o histórico de uma conversa."""
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).limit(limit)
        
        messages = session.execute(query).scalars().all()
        
        return [
            MessageHistory(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                tool_name=msg.tool_name,
                created_at=msg.created_at
            ) for msg in reversed(messages)  # Ordem cronológica
        ]
    
    def search_similar_messages(self, session: Session, query_text: str, 
                               limit: int = 5, max_distance: float = 0.3) -> List[SearchResult]:
        """Busca mensagens similares usando embeddings."""
        query_embedding = self.get_embedding(query_text)
        if not query_embedding:
            return []
        
        try:
            results = []
            for message, distance in simple_distance_query(session, query_embedding, limit, max_distance):
                similarity = (1 - distance) * 100  # Converte distância em similaridade percentual
                results.append(SearchResult(
                    message_id=message.id,
                    content=message.content,
                    similarity=round(similarity, 2),
                    created_at=message.created_at,
                    conversation_id=message.conversation_id
                ))
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
                    "tool_call_id": msg.tool_name  # Simplificado para este exemplo
                })
        return formatted
    
    def process_chat_message(self, session: Session, user_message: str, 
                           conversation_id: Optional[str] = None, 
                           use_history: bool = True, 
                           max_history_messages: int = 10) -> Tuple[str, str, List[str], List[str], Optional[int]]:
        """
        Processa uma mensagem de chat completa.
        
        Returns:
            Tuple com (resposta, conversation_id, tools_used, sources_used, total_tokens)
        """
        # Criar ou recuperar conversa
        conversation = self.create_or_get_conversation(session, conversation_id)
        
        # Salvar mensagem do usuário
        user_msg = self.save_message(session, conversation.id, "user", user_message)
        
        # Buscar contexto relevante do histórico
        sources_used = []
        context_messages = []
        
        if use_history:
            # Buscar mensagens similares de outras conversas
            similar_messages = self.search_similar_messages(session, user_message, limit=3)
            if similar_messages:
                context_info = "Informações relevantes do histórico:\n"
                for result in similar_messages:
                    context_info += f"- {result.content[:200]}... (similaridade: {result.similarity}%)\n"
                    sources_used.append(f"Mensagem {result.message_id[:8]} ({result.similarity}%)")
                
                context_messages.append({
                    "role": "system",
                    "content": f"Use as seguintes informações do histórico quando relevantes:\n{context_info}"
                })
            
            # Buscar histórico da conversa atual
            history = self.get_conversation_history(session, conversation.id, max_history_messages)
            if history:
                # Remove a última mensagem (que é a que acabamos de adicionar)
                history = history[:-1] if history else []
                context_messages.extend(self.format_messages_for_openai(history))
        
        # Preparar mensagens para OpenAI
        messages = [
            {
                "role": "system",
                "content": """Você é um assistente útil e inteligente. Você tem acesso a várias ferramentas que podem ajudar a responder perguntas do usuário.

Quando informações do histórico forem fornecidas, cite-as naturalmente em sua resposta quando relevantes. 

Use as ferramentas disponíveis quando apropriado:
- calculator: Para cálculos matemáticos
- get_current_datetime: Para obter data/hora atual
- text_analyzer: Para analisar textos
- search_knowledge_base: Para buscar informações técnicas

Seja conversacional, útil e preciso nas suas respostas."""
            }
        ]
        
        messages.extend(context_messages)
        messages.append({
            "role": "user", 
            "content": user_message
        })
        
        # Chamada para OpenAI com tools
        tools_used = []
        total_tokens = 0
        
        try:
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
            if assistant_message.tool_calls:
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
                        "role": "assistant",
                        "content": assistant_message.content or "",
                        "tool_calls": [{
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_args)
                            }
                        }]
                    })
                    
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
                
                final_content = final_response.choices[0].message.content
            else:
                final_content = assistant_message.content
            
            # Salvar resposta do assistente
            assistant_msg = self.save_message(session, conversation.id, "assistant", final_content or "")
            
            # Atualizar timestamp da conversa
            conversation.updated_at = datetime.utcnow()
            session.commit()
            
            return final_content or "", conversation.id, tools_used, sources_used, total_tokens
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            error_response = f"Desculpe, ocorreu um erro ao processar sua mensagem: {str(e)}"
            self.save_message(session, conversation.id, "assistant", error_response)
            return error_response, conversation.id, [], [], None