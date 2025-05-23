#!/usr/bin/env python3
"""
Script para inicializar e testar o banco de dados.
Uso: python scripts/init_db.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import SessionLocal, create_tables, test_db_connection
from api.models import Message, Conversation
from api.chat_service import ChatService
from api.config import get_settings
from ulid import ulid
from datetime import datetime

def init_database():
    """Inicializa o banco de dados e adiciona dados de teste."""
    print("=== Inicialização do Banco de Dados ===")
    
    # Testar conexão
    print("1. Testando conexão com banco...")
    if not test_db_connection():
        print("❌ Falha na conexão com banco de dados!")
        return False
    print("✅ Conexão com banco OK")
    
    # Criar tabelas
    print("2. Criando/verificando tabelas...")
    try:
        create_tables()
        print("✅ Tabelas criadas/verificadas com sucesso")
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        return False
    
    # Verificar se já existem dados
    with SessionLocal() as session:
        existing_messages = session.query(Message).count()
        existing_conversations = session.query(Conversation).count()
        
        print(f"3. Estado atual do banco:")
        print(f"   - Conversas: {existing_conversations}")
        print(f"   - Mensagens: {existing_messages}")
        
        if existing_messages > 0:
            print("ℹ️  Banco já possui dados. Pulando inicialização.")
            return True
    
    # Adicionar dados de exemplo
    print("4. Adicionando dados de exemplo...")
    try:
        settings = get_settings()
        if not settings.openai_api_key:
            print("⚠️  OPENAI_API_KEY não configurada. Adicionando dados sem embeddings...")
            add_sample_data_without_embeddings()
        else:
            print("📡 Gerando embeddings com OpenAI...")
            add_sample_data_with_embeddings(settings.openai_api_key)
            
        print("✅ Dados de exemplo adicionados com sucesso")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao adicionar dados: {e}")
        return False

def add_sample_data_without_embeddings():
    """Adiciona dados de exemplo sem embeddings."""
    with SessionLocal() as session:
        # Criar conversas de exemplo
        conv1_id = str(ulid())
        conv2_id = str(ulid())
        
        conversations = [
            Conversation(
                id=conv1_id,
                title="Conversa sobre Python",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Conversation(
                id=conv2_id,
                title="Matemática e Cálculos",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        ]
        
        for conv in conversations:
            session.add(conv)
        
        # Mensagens de exemplo
        messages = [
            # Conversa 1 - Python
            Message(
                id=str(ulid()),
                conversation_id=conv1_id,
                role="user",
                content="O que é Python?",
                embedding=None,
                created_at=datetime.utcnow()
            ),
            Message(
                id=str(ulid()),
                conversation_id=conv1_id,
                role="assistant",
                content="Python é uma linguagem de programação interpretada, orientada a objetos e de alto nível, conhecida por sua sintaxe clara e legível.",
                embedding=None,
                created_at=datetime.utcnow()
            ),
            # Conversa 2 - Matemática
            Message(
                id=str(ulid()),
                conversation_id=conv2_id,
                role="user",
                content="Quanto é 15 * 23?",
                embedding=None,
                created_at=datetime.utcnow()
            ),
            Message(
                id=str(ulid()),
                conversation_id=conv2_id,
                role="assistant",
                content="15 * 23 = 345",
                embedding=None,
                created_at=datetime.utcnow()
            ),
            # Mais exemplos para RAG
            Message(
                id=str(ulid()),
                conversation_id=conv1_id,
                role="user",
                content="Como usar FastAPI com Python?",
                embedding=None,
                created_at=datetime.utcnow()
            ),
            Message(
                id=str(ulid()),
                conversation_id=conv1_id,
                role="assistant",
                content="FastAPI é um framework web moderno para Python. Para usar, instale com 'pip install fastapi uvicorn' e crie uma aplicação básica importando FastAPI.",
                embedding=None,
                created_at=datetime.utcnow()
            )
        ]
        
        for msg in messages:
            session.add(msg)
        
        session.commit()
        print(f"   - Adicionadas {len(conversations)} conversas")
        print(f"   - Adicionadas {len(messages)} mensagens")

def add_sample_data_with_embeddings(openai_api_key: str):
    """Adiciona dados de exemplo COM embeddings usando ChatService."""
    chat_service = ChatService(openai_api_key)
    
    with SessionLocal() as session:
        # Simular algumas conversas usando o chat service
        sample_questions = [
            "O que é Python e para que serve?",
            "Como fazer cálculos matemáticos?",
            "Explique o que é FastAPI",
            "Quanto é 25 + 17?",
            "Como funciona machine learning?",
            "O que são embeddings?"
        ]
        
        for i, question in enumerate(sample_questions):
            try:
                print(f"   - Processando pergunta {i+1}/{len(sample_questions)}: {question[:30]}...")
                
                # Usar o chat service para processar a mensagem
                # Isso vai gerar embeddings automaticamente
                response, conv_id, tools_used, sources_used, tokens = chat_service.process_chat_message(
                    session=session,
                    user_message=question,
                    conversation_id=None,  # Nova conversa para cada pergunta
                    use_history=True
                )
                
                if tools_used:
                    print(f"     ✨ Tools usadas: {', '.join(tools_used)}")
                
            except Exception as e:
                print(f"     ⚠️  Erro ao processar '{question}': {e}")
                continue
        
        # Verificar quantos dados foram criados
        conversations_count = session.query(Conversation).count()
        messages_count = session.query(Message).count()
        messages_with_embeddings = session.query(Message).filter(Message.embedding.isnot(None)).count()
        
        print(f"   - Total de conversas: {conversations_count}")
        print(f"   - Total de mensagens: {messages_count}")
        print(f"   - Mensagens com embeddings: {messages_with_embeddings}")

def verify_database():
    """Verifica o estado do banco após inicialização."""
    print("\n=== Verificação do Banco ===")
    
    with SessionLocal() as session:
        try:
            # Estatísticas básicas
            conversations = session.query(Conversation).count()
            messages = session.query(Message).count()
            messages_with_embeddings = session.query(Message).filter(Message.embedding.isnot(None)).count()
            
            print(f"✅ Conversas: {conversations}")
            print(f"✅ Mensagens: {messages}")
            print(f"✅ Mensagens com embeddings: {messages_with_embeddings}")
            
            # Testar uma consulta de similarity (se há embeddings)
            if messages_with_embeddings > 0:
                print("🔍 Testando busca por similaridade...")
                # Pegar o primeiro embedding disponível
                first_message_with_embedding = session.query(Message).filter(
                    Message.embedding.isnot(None)
                ).first()
                
                if first_message_with_embedding:
                    from api.database import simple_distance_query
                    similar_messages = list(simple_distance_query(
                        session, 
                        first_message_with_embedding.embedding, 
                        limit=3
                    ))
                    print(f"   - Encontradas {len(similar_messages)} mensagens similares")
            
            print("✅ Verificação concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Iniciando configuração do banco de dados...")
    
    success = init_database()
    if success:
        verify_database()
        print("\n🎉 Banco de dados configurado e pronto para uso!")
        print("\nPróximos passos:")
        print("1. Inicie a API: uvicorn api.main:app --reload")
        print("2. Acesse: http://localhost:8000/docs")
        print("3. Teste o endpoint /chat")
    else:
        print("\n❌ Falha na configuração do banco de dados.")
        print("Verifique as configurações e tente novamente.")
        sys.exit(1)