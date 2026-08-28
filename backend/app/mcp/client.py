import os
import sys
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from app.core.config import settings

class MCPClientManager:
    @staticmethod
    def _get_server_parameters(user_id: str, jwt_token: str) -> StdioServerParameters:
        """
        Build subprocess parameters to run the MCP server.
        Uses sys.executable to run inside the same virtual environment context.
        """
        # Inject standard database credentials and user-session token parameters into the env
        env = {
            **os.environ,
            "SUPABASE_URL": settings.SUPABASE_URL,
            "SUPABASE_ANON_KEY": settings.SUPABASE_ANON_KEY,
            "OPENAI_API_KEY": settings.OPENAI_API_KEY,
            "OPENAI_BASE_URL": settings.OPENAI_BASE_URL,
            "OPENAI_EMBEDDING_MODEL": settings.OPENAI_EMBEDDING_MODEL,
            "USER_ID": user_id,
            "USER_JWT": jwt_token,
        }

        # Resolve path to the mcp server script
        server_script = os.path.abspath(settings.MCP_SERVER_PATH)

        return StdioServerParameters(
            command=sys.executable,
            args=[server_script],
            env=env
        )

    @classmethod
    async def call_mcp_tool(
        cls, 
        user_id: str, 
        jwt_token: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> str:
        """
        Spawns the MCP server subprocess, connects JSON-RPC streams,
        executes the target tool, and returns the result string.
        """
        params = cls._get_server_parameters(user_id, jwt_token)
        
        try:
            # Establish stdio pipe streams to subprocess
            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # Execute protocol handshake
                    await session.initialize()
                    
                    # Execute JSON-RPC tool call request
                    response = await session.call_tool(tool_name, arguments)
                    
                    # MCP tool call results typically contain TextContent lists
                    if response.content and len(response.content) > 0:
                        return response.content[0].text
                    
                    return "No output returned from tool."
                    
        except Exception as e:
            # Catch subprocess spawn errors or connection timeouts
            raise RuntimeError(f"MCP Client failed to execute tool '{tool_name}': {str(e)}")
