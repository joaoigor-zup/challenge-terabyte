#!/usr/bin/env python3
"""
Script para inicializar dados de exemplo no banco de dados.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import SessionLocal, create_tables
from api.models import Message
from api.utils import vector_to_compare
from ulid import ulid

def init_sample_data():
    """Inicializa dados de exemplo no banco."""
    print("Criando tabelas...")
    create_tables()
    
    print("Adicionando dados de exemplo...")
    
    with SessionLocal() as session:
        # Verificar se já existem dados
        existing = session.query(Message).first()
        if existing:
            print("Dados já existem, pulando inicialização.")
            return
        
        # Adicionar algumas mensagens de exemplo
        sample_messages = [
            {
                "id": str(ulid()),
                "conversation_id": "example_conversation",
                "role": "user",
                "content": "o rato roeu a roupa do rei de roma",
                "embedding": vector_to_compare
            },
            {
                "id": str(ulid()),
                "conversation_id": "example_conversation",
                "role": "assistant",
                "content": "Esse é um famoso trava-línguas em português! A frase 'o rato roeu a roupa do rei de roma' é conhecida pela repetição dos sons 'r' e 'o', tornando-a difícil de pronunciar rapidamente.",
                "embedding": None  # Será gerado automaticamente se usar o chat_service
            },
            {
                "id": str(ulid()),
                "conversation_id": "tech_conversation",
                "role": "user",
                "content": "Qual é a diferença entre Python e JavaScript?",
                "embedding": None
            },
            {
                "id": str(ulid()),
                "conversation_id": "tech_conversation",
                "role": "assistant",
                "content": "Python é uma linguagem interpretada, orientada a objetos, geralmente usada para desenvolvimento backend, ciência de dados e automação. JavaScript é uma linguagem principalmente usada para desenvolvimento web, tanto frontend quanto backend (Node.js).",
                "embedding": None
            }
        ]
        
        for msg_data in sample_messages:
            message = Message(**msg_data)
            session.add(message)
        
        session.commit()
        print(f"Adicionadas {len(sample_messages)} mensagens de exemplo.")

if __name__ == "__main__":
    init_sample_data()
    print("Inicialização concluída!")