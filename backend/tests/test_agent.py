import pytest
from app.agent.prompts import SYSTEM_INSTRUCTIONS, format_prompt_injection_wrapper
from app.agent.orchestrator import AgentOrchestrator
from app.mcp.client import MCPClientManager

def test_prompts_and_guardrails():
    """Verify system instructions load and XML wrappers format content segments."""
    assert len(SYSTEM_INSTRUCTIONS) > 0
    assert "PROMPT INJECTION SECURITY GUARDRAIL" in SYSTEM_INSTRUCTIONS
    
    wrapped = format_prompt_injection_wrapper("Malicious instructions ignore", 1)
    assert "<retrieved_content index=\"1\">" in wrapped
    assert "Malicious instructions ignore" in wrapped
    assert "</retrieved_content>" in wrapped

@pytest.mark.asyncio
async def test_agent_orchestrator_loop_success(monkeypatch):
    """
    Test the AgentOrchestrator conversation loop.
    Simulates:
    1. OpenAI requests a tool call to 'search_knowledge'.
    2. Orchestrator captures it, runs it via MCPClientManager, and feeds it back.
    3. OpenAI returns the final text token response.
    """
    # 1. Setup mock delta chunks for OpenAI stream simulation
    class MockFunction:
        def __init__(self, name, arguments):
            self.name = name
            self.arguments = arguments

    class MockToolCall:
        def __init__(self, index, id, name, arguments):
            self.index = index
            self.id = id
            self.function = MockFunction(name, arguments)

    class MockDelta:
        def __init__(self, content=None, tool_calls=None):
            self.content = content
            self.tool_calls = tool_calls

    class MockChoice:
        def __init__(self, delta):
            self.delta = delta

    class MockChunk:
        def __init__(self, delta_obj):
            self.choices = [MockChoice(delta_obj)]

    # Stream yields:
    # - A tool call chunk
    # - A final text chunk
    stream_1 = [
        MockChunk(MockDelta(tool_calls=[MockToolCall(0, "call-id-123", "search_knowledge", '{"query": "transformers"}')]))
    ]
    stream_2 = [
        MockChunk(MockDelta(content="Self-attention is the key concept."))
    ]
    
    streams_yielded = [stream_1, stream_2]
    stream_index = 0

    # Mock OpenAI client completions create method
    async def mock_completions_create(*args, **kwargs):
        nonlocal stream_index
        target_stream = streams_yielded[stream_index]
        stream_index += 1
        
        async def async_generator():
            for item in target_stream:
                yield item
        return async_generator()

    orchestrator = AgentOrchestrator()
    monkeypatch.setattr(orchestrator.openai_client.chat.completions, "create", mock_completions_create)

    # 2. Mock MCPClient tool invocation
    called_tools = []
    async def mock_call_mcp_tool(user_id, jwt_token, tool_name, arguments):
        called_tools.append((tool_name, arguments))
        return "Self-attention processes relationships between tokens."
        
    monkeypatch.setattr(MCPClientManager, "call_mcp_tool", mock_call_mcp_tool)

    # 3. Run the orchestrator loop
    history = [{"role": "user", "content": "Tell me about transformers."}]
    events = []
    
    async for event in orchestrator.run_chat_loop(
        user_id="user-uuid-1",
        jwt_token="jwt-token-1",
        chat_history=history
    ):
        events.append(event)

    # 4. Assertions
    # - Verify tool call event was yielded
    # - Verify tool result event was yielded
    # - Verify final text answer was yielded
    assert len(called_tools) == 1
    assert called_tools[0][0] == "search_knowledge"
    assert called_tools[0][1]["query"] == "transformers"
    
    event_types = [e["type"] for e in events]
    assert "tool_call" in event_types
    assert "tool_result" in event_types
    assert "text" in event_types
    
    # Find text tokens and verify content
    text_tokens = [e["content"] for e in events if e["type"] == "text"]
    assert "".join(text_tokens) == "Self-attention is the key concept."
