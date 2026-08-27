# Knowledge MCP Server

A Model Context Protocol (MCP) server that exposes standardized search and listing tools for the user's private knowledge base (Supabase Postgres database).

## Features
- Implements Anthropic's Model Context Protocol (v1)
- Exposes tools to search document segments (`search_knowledge`), list documents (`list_documents`), and read pages (`get_document_page`)
- Designed to run over stdio (standard input/output) as a subprocess, or standalone via SSE

## Configuration
The server expects database environment keys to connect to Supabase:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_ANON_KEY` mapping to authenticated queries)

## Verification
You can verify the MCP server is working by executing it directly with python. Because it uses stdio, it will wait for JSON-RPC messages on standard input.
```bash
python mcp_server.py
```
To test its JSON-RPC capabilities interactively, you can use the MCP CLI inspector tools.
