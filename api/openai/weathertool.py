from langchain_core.tools import tool
from pydantic import BaseModel, Field
import json

# Schema para os argumentos da nossa tool de previsão do tempo
class GetWeatherInput(BaseModel):
    city: str = Field(description="A cidade para a qual obter a previsão do tempo.")

@tool(args_schema=GetWeatherInput, description="Essa tool deve ser utilizada para retornar o clima atual de uma determinada cidade.") # O decorador @tool ajuda a descrever a função para o LLM
def get_current_weather(city: str) -> str:
    """Obtém a previsão do tempo atual para uma cidade especificada."""
    print(f"--- Chamando Tool: get_current_weather para a cidade: {city} ---")
    # Em um cenário real, você chamaria uma API de previsão do tempo aqui.
    # Para este exemplo, vamos simular:
    if "são paulo" in city.lower():
        return "A cidade de São Paulo possui as seguintes condições no momento: temperatura 22°C e tempo ensolarado"
    elif "rio de janeiro" in city.lower():
        return "A cidade do Rio de Janeiro possui as seguintes condições no momento: temperatura 28°C e tempo Parcialmente Nublado"
    else:
        return "Informações da cidade indisponível"