import os
import openai

from api.database import SessionLocal, simples_distance_query, save_history
from api.embed import embed_text
from api.tool import capitalize, lowercase, randomText


openai.api_key = os.getenv("OPENAI_API_KEY")

TOOL_FUNCTIONS = {
    "capitalize": capitalize,
    "lowercase": lowercase,
    "randomText": randomText,
}

def chat(message: str) -> str:    
    message_vector = embed_text(message)
    
    with SessionLocal() as session:
        # HISTORY 
        history = simples_distance_query(session, message_vector)
        
        chat_history = []
        relevant_history = [memory.content for memory, _ in history]
        relevant_history_str = "\n".join(relevant_history)

        chat_history.append({"role": "user", "content": f"""
            {message}
            
            ## relevant history
            {relevant_history_str}
"""
        })

        # First Call
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat_history,
            tools=[
                {"type": "function", "function": {"name": "capitalize", "description": "Capitalizes a string"}},
                {"type": "function", "function": {"name": "lowercase", "description": "Lowercases a string"}},
                {"type": "function", "function": {"name": "randomText", "description": "Generates a random Text with option length as argument, must be integer or empty"}},
            ]
        )
        message_data = response['choices'][0]['message']
        answer = message_data.get('content', '')

        # Check for tool calls
        if "tool_calls" in message_data:
            for tool_call in message_data["tool_calls"]:
                tool_name = tool_call["function"]["name"]
                tool_args = tool_call["function"].get("arguments", "")
                # Call the correct function
                tool_func = TOOL_FUNCTIONS.get(tool_name)
                if tool_func:
                    # If your tool expects arguments, parse them as needed
                    if tool_args:
                        # If arguments are JSON, parse them
                        import json
                        try:
                            args = json.loads(tool_args)
                            tool_output = tool_func(**args)
                        except Exception:
                            tool_output = tool_func(tool_args)
                    else:
                        tool_output = tool_func()
                    chat_history.append({
                        "role": "function",
                        "name": tool_name,
                        "content": tool_output
                    })
            # Call chat completion again with tool outputs
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=chat_history
            )
            answer = response['choices'][0]['message']['content']

        answer_vector = embed_text(answer)
    
        save_history(session, message, message_vector, answer, answer_vector)
        
        return answer