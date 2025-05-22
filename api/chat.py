from fastapi import APIRouter
from api.database import SessionLocal, Memory, simples_distance_query
from api.utils_open_ai import embed_text
from api.tools import tools, execute_tool, detect_tool_call
from api.schemas import ChatRequest
from openai import OpenAI
import os

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/chat")
async def chat_endpoint(body: ChatRequest):
    user_msg = body.mensagem
    query_vector = embed_text(user_msg)

    with SessionLocal() as session:
        historico_raw = simples_distance_query(session, query_vector)
        historico = [(m.content, d) for m, d in historico_raw]

    messages = []
    for content, _ in historico:
        if content.strip().lower().startswith("assistente:"):
            messages.append({"role": "assistant", "content": content})
        else:
            messages.append({"role": "user", "content": content})


    messages.append({"role": "user", "content": user_msg})

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.6
    )
    resposta = completion.choices[0].message.content

    tool_call = detect_tool_call(resposta)
    if tool_call:
        tool_result = execute_tool(tool_call["name"], tool_call["arguments"])
        messages.append({"role": "assistant", "content": resposta})
        messages.append({"role": "user", "content": f"Tool result: {tool_result}"})
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.6
        )
        resposta = completion.choices[0].message.content

    resp_vector = embed_text(resposta)

    with SessionLocal() as session:
        session.add(Memory(content=user_msg, vector=query_vector))
        session.add(Memory(content=f"Assistente: {resposta}", vector=resp_vector))
        session.commit()

    if resposta.strip().lower().startswith("assistente:"):
        resposta = resposta[len("Assistente:"):].strip()

    return {"resposta": resposta}

@router.post("/chat-use-tools")
async def chat_endpoint(body: ChatRequest):
    user_msg = body.mensagem
    query_vector = embed_text(user_msg)

    with SessionLocal() as session:
        historico_raw = simples_distance_query(session, query_vector)
        historico = [(m.content, d) for m, d in historico_raw]

    messages = []
    for content, _ in historico:
        if content.strip().lower().startswith("assistente:"):
            messages.append({"role": "assistant", "content": content})
        else:
            messages.append({"role": "user", "content": content})

    messages.append({"role": "user", "content": user_msg})

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = completion.choices[0].message

    # Execução somente via tool_call oficial da OpenAI
    resposta = message.content
    if hasattr(message, "tool_calls") and message.tool_calls:
        tool_call = message.tool_calls[0]
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        result = execute_tool(name, args)

        messages.append({"role": "assistant", "content": f"[Tool chamada: {name}]"})
        messages.append({"role": "user", "content": f"Resultado da ferramenta: {result}"})

        final_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        resposta = final_response.choices[0].message.content

    resp_vector = embed_text(resposta)

    with SessionLocal() as session:
        session.add(Memory(content=user_msg, vector=query_vector))
        session.add(Memory(content=f"Assistente: {resposta}", vector=resp_vector))
        session.commit()

    if resposta.strip().lower().startswith("assistente:"):
        resposta = resposta[len("Assistente:"):].strip()

    return {"resposta": resposta}