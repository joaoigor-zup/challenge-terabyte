import getpass
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

from click import prompt
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from api.openai.weathertool import get_current_weather

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
vector_store = PGVector(
    embeddings=embeddings,
    collection_name="history",
    connection="postgresql+psycopg://postgres:postgres@localhost:6000/postgres",
)

tools_list = [get_current_weather]

def chat_execute(userPrompt: str):
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

    messages_for_llm = []
    for history in vector_store.similarity_search(userPrompt):
        messages_for_llm.append(history)

    logging.info(f"history: {str(messages_for_llm)}")

    vector = embeddings.embed_query(userPrompt)
    #logging.info(f"Vector: {str(vector)}")
    save_user_prompt_with_precomputed_vector_add_embeddings(
        user_prompt_text=userPrompt,
        user_prompt_vector=vector,
        user_id="user",
        session_id="chat_session"
    )

    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    model_with_tools = model.bind_tools(tools_list)


    system_template = "Considere esse histórico de mensagens {history}"
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_template), ("user", "{text}")]
    )

    prompt = prompt_template.invoke({"history": messages_for_llm,"text": userPrompt})

    response = model_with_tools.invoke(prompt)

    if not hasattr(response, 'tool_calls') or not response.tool_calls:
        print(response.content)
        return response.content
    for tool_call in response.tool_calls:
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        tool_call_id = tool_call['id']  # Importante para associar o resultado à chamada

        print(f"LLM quer chamar a tool: {tool_name} com argumentos: {tool_args} (ID: {tool_call_id})")

        # Encontrar e executar a tool
        selected_tool = next((t for t in tools_list if t.name == tool_name), None)
        if selected_tool:
            try:
                tool_output = selected_tool.invoke(tool_args)  # Passa o dicionário de args
                print(f"Saída da Tool '{tool_name}': {tool_output}")
            except Exception as e:
                print(f"Erro ao executar a tool {tool_name}: {e}")
                tool_output = f"Erro ao executar a tool: {e}"
        else:
            print(f"Tool '{tool_name}' não encontrada!")
            tool_output = f"Tool '{tool_name}' não encontrada."

        # Adicionar o resultado da tool à conversa
        print(ToolMessage(content=str(tool_output), tool_call_id=tool_call_id))
        return tool_output



def save_user_prompt_with_precomputed_vector_add_embeddings(
            user_prompt_text: str,
            user_prompt_vector: List[float],
            user_id: str = None,
            session_id: str = None,
            additional_metadata: Dict[str, Any] = None
    ):
        """
        Salva o prompt do usuário (texto e seu embedding pré-calculado) no PGVector
        usando o método add_embeddings.

        Args:
            user_prompt_text (str): O texto do prompt do usuário.
            user_prompt_vector (List[float]): O embedding pré-calculado do prompt.
            user_id (str, optional): Um identificador para o usuário.
            session_id (str, optional): Um identificador para a sessão de chat.
            additional_metadata (dict, optional): Metadados adicionais.
        """
        if not user_prompt_text or not user_prompt_vector:
            print("Texto do prompt ou vetor estão vazios, não será salvo.")
            return None

        # Prepare os argumentos para add_embeddings
        # Eles esperam listas, mesmo que você esteja adicionando um único item.
        texts_to_add: List[str] = [user_prompt_text]
        embeddings_to_add: List[List[float]] = [user_prompt_vector]  # Lista de listas de floats

        metadata_item: Dict[str, Any] = {}
        if user_id:
            metadata_item["user_id"] = user_id
        if session_id:
            metadata_item["session_id"] = session_id
        if additional_metadata:
            metadata_item.update(additional_metadata)

        metadata_item["type"] = "user_prompt"
        metadata_item["timestamp"] = datetime.utcnow().isoformat()

        metadatas_to_add: List[Dict[str, Any]] = [metadata_item]

        try:
            print(f"Tentando salvar (via add_embeddings) o prompt: '{user_prompt_text}' com metadados: {metadata_item}")
            # Opcional: você pode fornecer seus próprios IDs se quiser controlá-los
            # ids_to_add: List[str] = [str(uuid.uuid4())]
            # added_doc_ids = vector_store.add_embeddings(
            #     texts=texts_to_add,
            #     embeddings=embeddings_to_add,
            #     metadatas=metadatas_to_add,
            #     ids=ids_to_add
            # )
            added_doc_ids = vector_store.add_embeddings(
                texts=texts_to_add,
                embeddings=embeddings_to_add,
                metadatas=metadatas_to_add
            )
            print(f"Prompt do usuário salvo no PGVector com IDs: {added_doc_ids}")
            return added_doc_ids
        except Exception as e:
            print(f"Erro ao salvar o prompt do usuário no PGVector usando add_embeddings: {e}")
            return None



