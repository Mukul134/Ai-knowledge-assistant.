import os
import time
from openai import OpenAI

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_knowledge",
                "description": "Search document",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    history = [
        {"role": "user", "content": "What is in my resume?"},
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "search_knowledge",
                        "arguments": "{\"query\":\"resume\"}"
                    }
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": "call_123",
            "name": "search_knowledge",
            "content": "Resume contains details about Mukul Verma."
        },
        {"role": "user", "content": "What is my name?"}
    ]

    print("Waiting 10 seconds to ensure rate limit window cooldown...")
    time.sleep(10)
    
    try:
        print("Testing Chat completions with history...")
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=history,
            tools=tools,
            stream=True
        )
        for chunk in response:
            pass
        print("Success!")
    except Exception as e:
        print("Failed:", str(e))

if __name__ == "__main__":
    main()
