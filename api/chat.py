from langchain.schema import BaseMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from dotenv import load_dotenv

load_dotenv()

chat_client = ChatOpenAI(model='gpt-4o-mini')
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

def embed(text: str) -> list[float]:
    vector = embeddings.embed_query(text)
    return vector

def call_chat(messages: list[BaseMessage]) -> BaseMessage:
    return chat_client.invoke(messages)
