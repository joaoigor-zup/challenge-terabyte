import json

# Formato oficial da OpenAI
tools = [
    {
        "type": "function",
        "function": {
            "name": "calc_tool",
            "description": "Realiza uma operação matemática",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Expressão matemática como '2 + 2'"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]

def execute_tool(name: str, args: dict) -> str:
    if name == "calc_tool":
        try:
            return str(eval(args["expression"]))
        except Exception as e:
            return f"Erro ao executar a expressão: {e}"
    return "Tool não reconhecida"


# Fallback manual, detecta chamadas como: "calc_tool(3 + 2)"
def detect_tool_call(response_text: str) -> dict | None:
    if "calc_tool(" in response_text:
        start = response_text.find("calc_tool(")
        end = response_text.find(")", start)
        args = response_text[start + 10:end]
        return {"name": "calc_tool", "arguments": {"expression": args.strip()}}
    return None
