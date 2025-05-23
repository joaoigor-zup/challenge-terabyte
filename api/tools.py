import json
import math
from datetime import datetime
from typing import Dict, Any, List

def calculator(expression: str) -> str:
    """
    Calcula expressões matemáticas simples.
    
    Args:
        expression: Expressão matemática como string (ex: "2 + 3 * 4")
    
    Returns:
        Resultado do cálculo
    """
    try:
        # Lista de operações permitidas para segurança
        allowed_chars = set('0123456789+-*/().^ ')
        if not all(c in allowed_chars for c in expression.replace('**', '^')):
            return "Erro: Expressão contém caracteres não permitidos"
        
        # Substitui ^ por ** para potenciação
        safe_expression = expression.replace('^', '**')
        
        # Avalia a expressão de forma segura
        result = eval(safe_expression, {"__builtins__": {}, "abs": abs, "round": round, "pow": pow, "sqrt": math.sqrt})
        return f"Resultado: {result}"
    except Exception as e:
        return f"Erro no cálculo: {str(e)}"

def get_current_datetime() -> str:
    """
    Retorna a data e hora atual no formato brasileiro.
    
    Returns:
        Data e hora atual formatada
    """
    now = datetime.now()
    return f"Data e hora atual: {now.strftime('%d/%m/%Y às %H:%M:%S')}"

def text_analyzer(text: str) -> str:
    """
    Analisa um texto fornecendo estatísticas básicas.
    
    Args:
        text: Texto a ser analisado
    
    Returns:
        Estatísticas do texto
    """
    if not text:
        return "Erro: Texto vazio fornecido"
    
    word_count = len(text.split())
    char_count = len(text)
    char_count_no_spaces = len(text.replace(' ', ''))
    sentence_count = text.count('.') + text.count('!') + text.count('?')
    paragraph_count = text.count('\n\n') + 1
    
    return f"""Análise do texto:
- Caracteres: {char_count}
- Caracteres (sem espaços): {char_count_no_spaces}
- Palavras: {word_count}
- Frases: {sentence_count}
- Parágrafos: {paragraph_count}"""

def search_knowledge_base(query: str) -> str:
    """
    Simula uma busca em base de conhecimento. 
    Em um sistema real, faria busca em uma base de dados real.
    
    Args:
        query: Termo de busca
    
    Returns:
        Informações relacionadas ao termo
    """
    # Base de conhecimento simulada
    knowledge_base = {
        "python": "Python é uma linguagem de programação interpretada, orientada a objetos e de alto nível.",
        "fastapi": "FastAPI é um framework web moderno e rápido para construir APIs com Python 3.7+ baseado em type hints.",
        "postgresql": "PostgreSQL é um sistema de gerenciamento de banco de dados objeto-relacional de código aberto.",
        "vector": "Vetores são estruturas de dados usadas em machine learning para representar embeddings e fazer buscas por similaridade.",
        "openai": "OpenAI é uma empresa de pesquisa em IA que desenvolve modelos de linguagem como GPT e ChatGPT.",
        "terabyte": "Terabyte é uma unidade de medida de armazenamento digital equivalente a 1.024 gigabytes."
    }
    
    query_lower = query.lower()
    
    # Busca exata
    if query_lower in knowledge_base:
        return f"Informação encontrada sobre '{query}': {knowledge_base[query_lower]}"
    
    # Busca parcial
    for key, value in knowledge_base.items():
        if query_lower in key or key in query_lower:
            return f"Informação relacionada a '{query}': {value}"
    
    return f"Nenhuma informação específica encontrada sobre '{query}' na base de conhecimento."

# Definição das tools para o OpenAI Function Calling
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Calcula expressões matemáticas simples como soma, subtração, multiplicação, divisão e potenciação",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Expressão matemática para calcular (ex: '2 + 3 * 4', '10 ^ 2')"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Obtém a data e hora atual",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "text_analyzer",
            "description": "Analisa um texto fornecendo estatísticas como contagem de palavras, caracteres, frases, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Texto a ser analisado"
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Busca informações em uma base de conhecimento sobre tecnologia e programação",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termo ou conceito a ser pesquisado"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

# Mapeamento das funções
FUNCTION_MAPPING = {
    "calculator": calculator,
    "get_current_datetime": get_current_datetime,
    "text_analyzer": text_analyzer,
    "search_knowledge_base": search_knowledge_base
}

def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Executa uma tool específica com os argumentos fornecidos.
    
    Args:
        tool_name: Nome da tool a ser executada
        arguments: Argumentos da tool
    
    Returns:
        Resultado da execução da tool
    """
    if tool_name not in FUNCTION_MAPPING:
        return f"Erro: Tool '{tool_name}' não encontrada"
    
    try:
        function = FUNCTION_MAPPING[tool_name]
        if arguments:
            return function(**arguments)
        else:
            return function()
    except Exception as e:
        return f"Erro ao executar tool '{tool_name}': {str(e)}"