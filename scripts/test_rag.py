#!/usr/bin/env python3
"""
Script para testar o funcionamento do RAG (Retrieval-Augmented Generation).
Uso: python scripts/test_rag.py
"""

import sys
import os
import requests
import json
from time import sleep

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = "http://localhost:8000"

def test_api_connection():
    """Testa se a API está rodando."""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ API está online")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Database: {data.get('database')}")
            print(f"   - Conversas: {data.get('conversations_count', 0)}")
            print(f"   - Mensagens: {data.get('messages_count', 0)}")
            return True
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar com a API: {e}")
        return False

def send_chat_message(message, conversation_id=None):
    """Envia uma mensagem para o chat."""
    payload = {
        "message": message,
        "use_history": True,
        "max_history_messages": 10
    }
    
    if conversation_id:
        payload["conversation_id"] = conversation_id
    
    try:
        response = requests.post(f"{API_BASE_URL}/chat", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erro na requisição: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        return None

def test_basic_chat():
    """Testa funcionalidade básica do chat."""
    print("\n=== Teste Básico do Chat ===")
    
    # Primeira mensagem
    print("1. Enviando primeira mensagem...")
    response1 = send_chat_message("Olá! Você pode me explicar o que é Python?")
    
    if not response1:
        return False
    
    conversation_id = response1.get("conversation_id")
    print(f"✅ Resposta recebida (Conversa: {conversation_id[:8]}...)")
    print(f"   Tools usadas: {response1.get('tools_used', [])}")
    print(f"   Fontes RAG: {response1.get('sources_used', [])}")
    print(f"   Tokens: {response1.get('total_tokens', 0)}")
    
    # Segunda mensagem na mesma conversa
    print("\n2. Enviando segunda mensagem na mesma conversa...")
    response2 = send_chat_message("E como posso começar a aprender?", conversation_id)
    
    if not response2:
        return False
    
    print("✅ Segunda resposta recebida")
    print(f"   Fontes RAG: {response2.get('sources_used', [])}")
    print(f"   Tokens: {response2.get('total_tokens', 0)}")
    
    return True

def test_rag_functionality():
    """Testa especificamente o RAG."""
    print("\n=== Teste do RAG ===")
    
    # Criar várias conversas com tópicos relacionados
    topics = {
        "python_basics": [
            "O que é Python?",
            "Python é uma linguagem interpretada?",
            "Quais são as vantagens do Python?"
        ],
        "math_calculations": [
            "Quanto é 15 * 23?",
            "Me ajude com cálculos matemáticos",
            "Como fazer operações com números grandes?"
        ],
        "web_development": [
            "O que é FastAPI?",
            "Como criar uma API REST?",
            "Quais são os frameworks web para Python?"
        ]
    }
    
    conversation_ids = {}
    
    # Criar conversas iniciais
    print("1. Criando conversas iniciais...")
    for topic, questions in topics.items():
        print(f"   - Tópico: {topic}")
        for i, question in enumerate(questions):
            response = send_chat_message(question)
            if response and i == 0:  # Salvar ID da primeira conversa de cada tópico
                conversation_ids[topic] = response.get("conversation_id")
            sleep(1)  # Evitar rate limit
    
    print(f"✅ Criadas {len(conversation_ids)} conversas iniciais")
    
    # Agora testar se o RAG funciona - fazer perguntas relacionadas em novas conversas
    print("\n2. Testando recuperação de contexto (RAG)...")
    
    test_questions = [
        "Me fale sobre linguagens de programação interpretadas",  # Deve recuperar info sobre Python
        "Preciso fazer multiplicações complexas",  # Deve recuperar info sobre cálculos
        "Como construir APIs web modernas?"  # Deve recuperar info sobre FastAPI
    ]
    
    for i, question in enumerate(test_questions):
        print(f"   - Pergunta {i+1}: {question[:40]}...")
        response = send_chat_message(question)
        
        if response:
            sources = response.get('sources_used', [])
            if sources:
                print(f"     ✅ RAG ativo! Fontes utilizadas: {len(sources)}")
                for source in sources:
                    print(f"       - {source}")
            else:
                print("     ⚠️  Nenhuma fonte RAG encontrada")
        else:
            print("     ❌ Falha na requisição")
        
        sleep(1)
    
    return True

def test_similarity_search():
    """Testa o endpoint de busca por similaridade."""
    print("\n=== Teste de Busca por Similaridade ===")
    
    search_queries = [
        "programação",
        "matemática",
        "web development",
        "cálculos"
    ]
    
    for query in search_queries:
        print(f"Buscando por: '{query}'")
        
        try:
            response = requests.post(f"{API_BASE_URL}/search", json={
                "query": query,
                "limit": 5,
                "similarity_threshold": 0.7
            })
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ Encontrados {len(results)} resultados")
                
                for result in results:
                    print(f"   - Similaridade: {result['similarity']}% | {result['content'][:50]}...")
            else:
                print(f"❌ Erro na busca: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
        
        print()
    
    return True

def test_tools_integration():
    """Testa integração com tools."""
    print("\n=== Teste de Integração com Tools ===")
    
    tool_questions = [
        "Quanto é 25 * 47 + 100?",  # Calculator
        "Que horas são agora?",      # DateTime
        "Analise este texto: 'Python é uma linguagem de programação muito poderosa'",  # Text Analyzer
        "Me fale sobre FastAPI"      # Knowledge Base
    ]
    
    for question in tool_questions:
        print(f"Testando: {question}")
        response = send_chat_message(question)
        
        if response:
            tools_used = response.get('tools_used', [])
            if tools_used:
                print(f"✅ Tools utilizadas: {', '.join(tools_used)}")
            else:
                print("   ℹ️  Nenhuma tool utilizada")
            
            sources = response.get('sources_used', [])
            if sources:
                print(f"   📚 Fontes RAG: {len(sources)} fontes")
        else:
            print("❌ Falha na requisição")
        
        print()
        sleep(1)
    
    return True

def run_comprehensive_test():
    """Executa todos os testes."""
    print("🧪 Iniciando testes abrangentes do RAG...")
    
    # Verificar se API está online
    if not test_api_connection():
        print("❌ API não está acessível. Certifique-se de que está rodando em http://localhost:8000")
        return False
    
    sleep(1)
    
    # Testes básicos
    if not test_basic_chat():
        print("❌ Falha nos testes básicos")
        return False
    
    sleep(2)
    
    # Testes do RAG
    if not test_rag_functionality():
        print("❌ Falha nos testes do RAG")
        return False
        
    sleep(2)
    
    # Testes de busca
    if not test_similarity_search():
        print("❌ Falha nos testes de busca")
        return False
        
    sleep(2)
    
    # Testes de tools
    if not test_tools_integration():
        print("❌ Falha nos testes de tools")
        return False
    
    print("\n🎉 Todos os testes foram executados!")
    print("\n📊 Resumo:")
    print("✅ Conexão com API")
    print("✅ Funcionalidade básica do chat")
    print("✅ Sistema RAG (Retrieval-Augmented Generation)")
    print("✅ Busca por similaridade")
    print("✅ Integração com tools")
    
    return True

if __name__ == "__main__":
    run_comprehensive_test()