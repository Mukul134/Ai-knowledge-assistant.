import os
import sys
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment configurations
load_dotenv()

from mcp.server.mcpserver import MCPServer
from supabase import create_client, Client
from supabase.client import ClientOptions
from openai import OpenAI

# Initialize MCPServer server
mcp = MCPServer("knowledge-mcp-server")

def get_user_supabase_client() -> Client:
    """
    Instantiate a user-authenticated Supabase client using environment variables.
    Enforces Row-Level Security (RLS) constraints.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    user_jwt = os.getenv("USER_JWT")
    
    if not supabase_url or not supabase_anon_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be configured in environment.")
    if not user_jwt:
        raise ValueError("USER_JWT environment variable is missing. Authentication context is required.")
        
    options = ClientOptions(
        headers={
            "Authorization": f"Bearer {user_jwt}"
        }
    )
    return create_client(supabase_url, supabase_anon_key, options=options)

def get_openai_client() -> OpenAI:
    """Instantiate a standard OpenAI client for generating query embeddings."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY must be configured in environment.")
    return OpenAI(api_key=api_key)

@mcp.tool()
async def search_knowledge(
    query: str, 
    document_id: Optional[str] = None, 
    top_k: int = 5
) -> str:
    """
    Perform a semantic search across your uploaded documents. 
    Use this when the user asks questions requiring private file knowledge.
    """
    print(f"MCP Tool execution: search_knowledge", file=sys.stderr)
    try:
        supabase_user = get_user_supabase_client()
        user_id = os.getenv("USER_ID")
        if not user_id:
            raise ValueError("USER_ID environment variable is missing.")
            
        # 1. Generate Query Embedding
        openai_client = get_openai_client()
        embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        
        response = openai_client.embeddings.create(
            input=[query],
            model=embedding_model
        )
        query_vector = response.data[0].embedding
        
        # 2. Call pgvector Similarity Search RPC
        match_threshold = 0.3  # standard text-embedding-3-small threshold
        rpc_params = {
            "query_embedding": query_vector,
            "match_threshold": match_threshold,
            "match_count": top_k,
            "filter_user_id": user_id,
            "filter_document_id": document_id if document_id else None
        }
        
        db_response = supabase_user.rpc("match_document_chunks", rpc_params).execute()
        chunks = db_response.data or []
        
        if not chunks:
            return "No relevant information was found in your documents."
            
        # 3. Format results as Markdown
        formatted_results = []
        for idx, chunk in enumerate(chunks):
            formatted_results.append(
                f"### Result {idx + 1} | Source: {chunk['file_name']} (Page {chunk['page_number']})\n"
                f"Document ID: {chunk['document_id']}\n"
                f"Similarity Score: {chunk['similarity']:.4f}\n"
                f"Content:\n{chunk['content']}\n"
            )
        
        return "\n---\n".join(formatted_results)
        
    except Exception as e:
        print(f"Error executing search_knowledge: {str(e)}", file=sys.stderr)
        return f"Error executing tool search_knowledge: {str(e)}"

@mcp.tool()
async def get_document_page(
    document_id: str, 
    page_number: int
) -> str:
    """
    Retrieve verbatim text content of a specific page from a document. 
    Use this when you need page context around a citation.
    """
    print(f"MCP Tool execution: get_document_page", file=sys.stderr)
    try:
        supabase_user = get_user_supabase_client()
        user_id = os.getenv("USER_ID")
        if not user_id:
            raise ValueError("USER_ID environment variable is missing.")
            
        # Fetch chunks corresponding to target page
        db_response = supabase_user.table("document_chunks") \
            .select("content") \
            .eq("document_id", document_id) \
            .eq("page_number", page_number) \
            .order("created_at") \
            .execute()
            
        chunks = db_response.data or []
        if not chunks:
            return f"No content found for document {document_id} on page {page_number}."
            
        full_text = "\n".join([c["content"] for c in chunks])
        return f"--- Document {document_id} Page {page_number} ---\n\n{full_text}"
        
    except Exception as e:
        print(f"Error executing get_document_page: {str(e)}", file=sys.stderr)
        return f"Error executing tool get_document_page: {str(e)}"

@mcp.tool()
async def list_documents() -> str:
    """
    List metadata (file names, UUIDs, status, page count) for all your uploaded documents.
    """
    print(f"MCP Tool execution: list_documents", file=sys.stderr)
    try:
        supabase_user = get_user_supabase_client()
        user_id = os.getenv("USER_ID")
        if not user_id:
            raise ValueError("USER_ID environment variable is missing.")
            
        db_response = supabase_user.table("documents") \
            .select("id, file_name, file_size, page_count, status, created_at") \
            .order("created_at", descending=True) \
            .execute()
            
        docs = db_response.data or []
        if not docs:
            return "No documents have been uploaded yet."
            
        formatted_docs = []
        for doc in docs:
            size_mb = doc['file_size'] / (1024 * 1024)
            formatted_docs.append(
                f"- **{doc['file_name']}**\n"
                f"  UUID: `{doc['id']}`\n"
                f"  Status: {doc['status']}\n"
                f"  Pages: {doc.get('page_count') or 'Unknown'}\n"
                f"  Size: {size_mb:.2f} MB\n"
                f"  Uploaded At: {doc['created_at']}"
            )
            
        return "\n".join(formatted_docs)
        
    except Exception as e:
        print(f"Error executing list_documents: {str(e)}", file=sys.stderr)
        return f"Error executing tool list_documents: {str(e)}"

if __name__ == "__main__":
    # FastMCP uses .run() method to start the stdio server automatically
    mcp.run()
