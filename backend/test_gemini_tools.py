import os
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
    
    # Test 1: With tools, tool_choice and streaming
    try:
        print("Testing Chat completions with tools, tool_choice='auto' and stream=True...")
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": "What is in my resume?"}],
            tools=tools,
            tool_choice="auto",
            stream=True
        )
        for chunk in response:
            pass
        print("Success 1!")
    except Exception as e:
        print("Test 1 Failed:", str(e))

    # Test 2: With tools only and streaming (no tool_choice)
    try:
        print("\nTesting Chat completions with tools only and stream=True...")
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[{"role": "user", "content": "What is in my resume?"}],
            tools=tools,
            stream=True
        )
        for chunk in response:
            pass
        print("Success 2!")
    except Exception as e:
        print("Test 2 Failed:", str(e))

    # Test 3: With tool calls and tool messages in history
    try:
        print("\nTesting Chat completions with tool role in messages history...")
        history = [
            {"role": "user", "content": "What is in my resume?"},
            {
                "role": "assistant",
                "content": None,
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
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=history,
            tools=tools,
            stream=True
        )
        for chunk in response:
            pass
        print("Success 3!")
    except Exception as e:
        print("Test 3 Failed:", str(e))

if __name__ == "__main__":
    main()
