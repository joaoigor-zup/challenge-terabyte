from langchain_core.tools import tool
from openai import OpenAI
import openai

client = OpenAI()

@tool
def gerar_imagem(prompt: str) -> str:
    """Gera uma imagem a partir de um prompt textual usando DALL·E. Retorna uma url da imagem"""
    response = client.images.generate(
        prompt=prompt,
        n=1,
        size="512x512"
    )
    print(response)
    return response.data[0].url

@tool
def somar(a: int, b: int) -> int:
    """Soma dois números inteiros."""
    return a + b