#!/usr/bin/env python3
"""
Script de debug e verificação do sistema.
Uso: python scripts/debug.py
"""

import sys
import os
import subprocess
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_docker_services():
    """Verifica status dos serviços Docker."""
    print("🐳 Verificando serviços Docker...")
    
    try:
        # Verificar se docker-compose está rodando
        result = subprocess.run(
            ["docker-compose", "-f", "docker/docker-compose.yaml", "ps"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode == 0:
            print("✅ Docker Compose está rodando")
            print("Serviços ativos:")
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Pular header
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ Docker Compose não está rodando")
            print("Execute: cd docker && docker-compose up -d")
            return False
            
    except FileNotFoundError:
        print("❌ Docker Compose não encontrado")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar Docker: {e}")
        return False
    
    return True

def check_database_connection():
    """Verifica conexão com PostgreSQL."""
    print("\n🗄️  Verificando conexão com banco de dados...")
    
    try:
        from api.database import SessionLocal, test_db_connection
        
        if test_db_connection():
            print("✅ Conexão com PostgreSQL OK")
            
            # Verificar tabelas
            with SessionLocal() as session:
                from sqlalchemy import text
                
                # Verificar extensão pgvector
                result = session.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
                if result.first():
                    print("✅ Extensão pgvector instalada")
                else:
                    print("⚠️  Extensão pgvector não encontrada")
                
                # Contar registros
                conversations = session.execute(text("SELECT COUNT(*) FROM conversations")).scalar()
                messages = session.execute(text("SELECT COUNT(*) FROM messages")).scalar()
                messages_with_embeddings = session.execute(text(
                    "SELECT COUNT(*) FROM messages WHERE embedding IS NOT NULL"
                )).scalar()
                
                print(f"📊 Estatísticas do banco:")
                print(f"   - Conversas: {conversations}")
                print(f"   - Mensagens: {messages}")
                print(f"   - Mensagens com embeddings: {messages_with_embeddings}")
                
                return True
                
    except Exception as e:
        print(f"❌ Erro na conexão com banco: {e}")
        return False

def check_api_status():
    """Verifica se a API está respondendo."""
    print("\n🌐 Verificando API FastAPI...")
    
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ API está online")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Database: {data.get('database')}")
            print(f"   - Tools disponíveis: {len(data.get('available_tools', []))}")
            return True
        else:
            print(f"❌ API retornou status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ API não está acessível em http://localhost:8000")
        print("   Execute: docker-compose up -d ou uvicorn api.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar API: {e}")
        return False

def check_openai_config():
    """Verifica configuração da OpenAI."""
    print("\n🤖 Verificando configuração OpenAI...")
    
    try:
        from api.config import get_settings
        settings = get_settings()
        
        if settings.openai_api_key:
            # Mascarar a chave para não mostrar completa
            masked_key = settings.openai_api_key[:8] + "..." + settings.openai_api_key[-4:]
            print(f"✅ OPENAI_API_KEY configurada: {masked_key}")
            print(f"   - Modelo de chat: {settings.openai_model}")
            print(f"   - Modelo de embedding: {settings.openai_embedding_model}")
            
            # Testar a chave fazendo uma requisição simples
            from api.chat_service import ChatService
            chat_service = ChatService(settings.openai_api_key)
            
            # Tentar gerar um embedding simples
            test_embedding = chat_service.get_embedding("teste")
            if test_embedding:
                print(f"✅ Chave OpenAI válida (embedding gerado: {len(test_embedding)} dimensões)")
                return True
            else:
                print("❌ Falha ao gerar embedding - chave inválida?")
                return False
        else:
            print("❌ OPENAI_API_KEY não configurada")
            print("   Configure no arquivo .env: OPENAI_API_KEY=sua_chave_aqui")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar OpenAI: {e}")
        return False

def check_rag_functionality():
    """Verifica se o RAG está funcionando."""
    print("\n🧠 Verificando funcionalidade RAG...")
    
    try:
        from api.database import SessionLocal
        from api.chat_service import ChatService
        from api.config import get_settings
        
        settings = get_settings()
        if not settings.openai_api_key:
            print("❌ Não é possível testar RAG sem OPENAI_API_KEY")
            return False
        
        chat_service = ChatService(settings.openai_api_key)
        
        with SessionLocal() as session:
            # Verificar se há mensagens com embeddings
            from sqlalchemy import text
            count = session.execute(text(
                "SELECT COUNT(*) FROM messages WHERE embedding IS NOT NULL"
            )).scalar()
            
            if count == 0:
                print("⚠️  Nenhuma mensagem com embedding encontrada")
                print("   Execute: python scripts/init_db.py")
                return False
            
            print(f"✅ Encontradas {count} mensagens com embeddings")
            
            # Testar busca por similaridade
            results = chat_service.search_similar_messages(
                session, 
                "Python programming", 
                limit=3
            )
            
            if results:
                print(f"✅ Busca por similaridade funcionando ({len(results)} resultados)")
                for result in results[:2]:  # Mostrar primeiros 2
                    print(f"   - Similaridade: {result.similarity}% | {result.content[:50]}...")
                return True
            else:
                print("❌ Busca por similaridade não retornou resultados")
                return False
                
    except Exception as e:
        print(f"❌ Erro ao verificar RAG: {e}")
        return False

def check_environment_variables():
    """Verifica variáveis de ambiente importantes."""
    print("\n⚙️  Verificando variáveis de ambiente...")
    
    required_vars = [
        "OPENAI_API_KEY",
        "DATABASE_URL"
    ]
    
    optional_vars = [
        "OPENAI_MODEL",
        "OPENAI_EMBEDDING_MODEL",
        "MAX_HISTORY_MESSAGES",
        "SIMILARITY_THRESHOLD"
    ]
    
    all_good = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if "key" in var.lower() or "password" in var.lower():
                print(f"✅ {var}: {value[:8]}...{value[-4:]}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: não configurada")
            all_good = False
    
    print("\nVariáveis opcionais:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: usando padrão")
    
    return all_good

def run_quick_api_test():
    """Executa um teste rápido da API."""
    print("\n🚀 Executando teste rápido da API...")
    
    try:
        # Teste básico de chat
        response = requests.post("http://localhost:8000/chat", json={
            "message": "Olá! Este é um teste rápido.",
            "use_history": True
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Teste de chat bem-sucedido")
            print(f"   - Conversa ID: {data.get('conversation_id', 'N/A')[:8]}...")
            print(f"   - Tools usadas: {data.get('tools_used', [])}")
            print(f"   - Fontes RAG: {len(data.get('sources_used', []))}")
            print(f"   - Tokens: {data.get('total_tokens', 0)}")
            return True
        else:
            print(f"❌ Teste de chat falhou: {response.status_code}")
            print(f"   Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste de API: {e}")
        return False

def main():
    """Função principal de debug."""
    print("🔧 SISTEMA DE DEBUG - TERABYTE CHALLENGE")
    print("=" * 50)
    print(f"Data/Hora: {datetime.now()}")
    print()
    
    checks = [
        ("Docker Services", check_docker_services),
        ("Database Connection", check_database_connection),
        ("API Status", check_api_status),
        ("OpenAI Configuration", check_openai_config),
        ("Environment Variables", check_environment_variables),
        ("RAG Functionality", check_rag_functionality),
        ("Quick API Test", run_quick_api_test)
    ]
    
    results = {}
    
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ Erro inesperado em {name}: {e}")
            results[name] = False
    
    # Resumo final
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS CHECKS:")
    
    passed = 0
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Score: {passed}/{len(checks)} checks passaram")
    
    if passed == len(checks):
        print("🎉 SISTEMA TOTALMENTE FUNCIONAL!")
        print("\nPróximos passos:")
        print("- Acesse http://localhost:8000/docs para testar")
        print("- Execute python scripts/test_rag.py para testes completos")
    else:
        print("⚠️  SISTEMA COM PROBLEMAS")
        print("\nVerifique os itens que falharam acima e:")
        print("- Revise o arquivo .env")
        print("- Execute docker-compose up -d")
        print("- Execute python scripts/init_db.py")
    
    return passed == len(checks)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)