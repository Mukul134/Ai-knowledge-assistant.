import json
from typing import AsyncGenerator, List, Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings
from app.agent.prompts import SYSTEM_INSTRUCTIONS, format_prompt_injection_wrapper
from app.mcp.client import MCPClientManager

class AgentOrchestrator:
    def __init__(self):
        """
        Initialize the AsyncOpenAI client.
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be configured in environment.")
        
        kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_BASE_URL
        self.openai_client = AsyncOpenAI(**kwargs)

    def _get_mcp_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Tool schema declarations matching the MCP server tools,
        formatted for the OpenAI Chat Completions API.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge",
                    "description": "Perform a semantic search across the user's uploaded documents. Use this when the user asks questions requiring private file knowledge.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Semantic query or question to search in the knowledge base."
                            },
                            "document_id": {
                                "type": "string",
                                "description": "Optional UUID of a specific document to restrict the search to."
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Maximum number of document chunks to return (default is 5).",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_document_page",
                    "description": "Retrieve verbatim text content of a specific page from a document. Use this when you need page context around a citation.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "document_id": {
                                "type": "string",
                                "description": "The unique UUID of the document."
                            },
                            "page_number": {
                                "type": "integer",
                                "description": "The page number to extract (1-indexed)."
                            }
                        },
                        "required": ["document_id", "page_number"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_documents",
                    "description": "List metadata (file names, UUIDs, status, page count) for all your uploaded documents.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

    async def run_chat_loop(
        self,
        user_id: str,
        jwt_token: str,
        chat_history: List[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Orchestrates the agent loop: builds prompt templates, sends queries to OpenAI,
        intercepts tool requests, executes them via the MCP client subprocess,
        feeds findings back, and yields text tokens and citation metadata to the stream.
        """
        # 1. Format the conversation logs
        messages = [{"role": "system", "content": SYSTEM_INSTRUCTIONS}]
        for msg in chat_history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        tools = self._get_mcp_tool_definitions()
        
        # We loop up to 5 times to handle recursive tool calls (e.g. list docs -> search -> print answer)
        MAX_LOOPS = 5
        
        for loop_idx in range(MAX_LOOPS):
            try:
                # Call OpenAI with streaming enabled
                response_stream = await self.openai_client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    stream=True
                )
            except Exception as e:
                yield {"type": "error", "content": f"OpenAI connection error: {str(e)}"}
                return

            current_tool_calls = {}
            has_tool_call = False
            
            async for chunk in response_stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue
                
                # Stream back generated text content
                if delta.content:
                    yield {"type": "text", "content": delta.content}
                    
                # Accumulate tool call fragments if the model wants to call a tool
                if delta.tool_calls:
                    has_tool_call = True
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in current_tool_calls:
                            current_tool_calls[idx] = {
                                "id": tc.id or "",
                                "name": tc.function.name or "",
                                "arguments": tc.function.arguments or ""
                            }
                        else:
                            if tc.id:
                                current_tool_calls[idx]["id"] += tc.id
                            if tc.function.name:
                                current_tool_calls[idx]["name"] += tc.function.name
                            if tc.function.arguments:
                                current_tool_calls[idx]["arguments"] += tc.function.arguments

            # If no tool calls were generated in this loop iteration, the generation is complete!
            if not has_tool_call:
                break

            # Process all tool calls requested by the model in this turn
            assistant_tool_calls_payload = []
            
            for idx, tool_data in current_tool_calls.items():
                tool_name = tool_data["name"]
                tool_id = tool_data["id"]
                args_str = tool_data["arguments"]
                
                try:
                    arguments = json.loads(args_str) if args_str else {}
                except json.JSONDecodeError:
                    arguments = {}

                yield {"type": "tool_call", "name": tool_name, "arguments": arguments}
                
                # Execute the tool via the MCP subprocess client manager
                try:
                    # Apply prompt injection protections when returning search content
                    if tool_name == "search_knowledge":
                        raw_result = await MCPClientManager.call_mcp_tool(user_id, jwt_token, tool_name, arguments)
                        # Isolate the returned string chunk inside XML containers
                        result_str = format_prompt_injection_wrapper(raw_result, idx)
                    else:
                        result_str = await MCPClientManager.call_mcp_tool(user_id, jwt_token, tool_name, arguments)
                except Exception as e:
                    result_str = f"Error executing tool '{tool_name}': {str(e)}"

                yield {"type": "tool_result", "name": tool_name, "content": result_str}
                
                # Record the assistant's decision and the tool's result to feed back to the LLM
                assistant_tool_calls_payload.append({
                    "id": tool_id,
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": args_str
                    }
                })
                
                # Add the tool outcome to the message history
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": result_str
                })

            # Prepend the assistant's call definitions to the history before feeding back
            # (Required by OpenAI API: a tool role message must always follow an assistant role message with tool_calls)
            messages.insert(-len(assistant_tool_calls_payload), {
                "role": "assistant",
                "tool_calls": assistant_tool_calls_payload
            })
            
            # Continue the loop to feed the tool outcomes back to OpenAI
