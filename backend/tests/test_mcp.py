import pytest
import os
import sys

# Add mcp-server directory to python path to import the script directly
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "mcp-server"))

from mcp_server import mcp, list_documents, get_document_page, search_knowledge

@pytest.mark.asyncio
async def test_mcp_list_tools():
    """Verify that MCPServer registers the three expected tools and descriptions."""
    tools = await mcp.list_tools()
    assert len(tools) == 3
    tool_names = [t.name for t in tools]
    assert "search_knowledge" in tool_names
    assert "get_document_page" in tool_names
    assert "list_documents" in tool_names

@pytest.mark.asyncio
async def test_mcp_call_list_documents_success(monkeypatch):
    """Verify calling list_documents tool function returns formatted Markdown summaries."""
    monkeypatch.setenv("SUPABASE_URL", "https://mock-supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "mock-anon-key")
    monkeypatch.setenv("USER_JWT", "mock-jwt-token")
    monkeypatch.setenv("USER_ID", "user-uuid-123")
    
    mock_docs = [
        {
            "id": "doc-uuid-abc",
            "file_name": "resume.pdf",
            "file_size": 1024 * 1024,
            "page_count": 2,
            "status": "completed",
            "created_at": "2026-08-28T00:00:00Z"
        }
    ]
    
    class MockBuilder:
        def select(self, *args, **kwargs):
            return self
        def order(self, *args, **kwargs):
            return self
        def execute(self):
            class Response:
                data = mock_docs
            return Response()
            
    class MockSupabase:
        def table(self, table_name):
            assert table_name == "documents"
            return MockBuilder()
            
    # Mock create_client in mcp_server namespace
    import mcp_server
    monkeypatch.setattr(mcp_server, "create_client", lambda *args, **kwargs: MockSupabase())
    
    text_content = await list_documents()
    assert "resume.pdf" in text_content
    assert "1.00 MB" in text_content
    assert "completed" in text_content

@pytest.mark.asyncio
async def test_mcp_call_get_page_success(monkeypatch):
    """Verify calling get_document_page tool function aggregates and returns page chunk content."""
    monkeypatch.setenv("SUPABASE_URL", "https://mock-supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "mock-anon-key")
    monkeypatch.setenv("USER_JWT", "mock-jwt-token")
    monkeypatch.setenv("USER_ID", "user-uuid-123")
    
    mock_chunks = [
        {"content": "This is paragraph one on page 2."},
        {"content": "This is paragraph two on page 2."}
    ]
    
    class MockBuilder:
        def select(self, *args, **kwargs):
            return self
        def eq(self, column, value):
            return self
        def order(self, *args, **kwargs):
            return self
        def execute(self):
            class Response:
                data = mock_chunks
            return Response()
            
    class MockSupabase:
        def table(self, table_name):
            assert table_name == "document_chunks"
            return MockBuilder()
            
    import mcp_server
    monkeypatch.setattr(mcp_server, "create_client", lambda *args, **kwargs: MockSupabase())
    
    text_content = await get_document_page(
        document_id="doc-uuid-abc", 
        page_number=2
    )
    assert "This is paragraph one on page 2." in text_content
    assert "This is paragraph two on page 2." in text_content

@pytest.mark.asyncio
async def test_mcp_call_search_knowledge_success(monkeypatch):
    """Verify search_knowledge tool function generates embeddings and returns similarity matches."""
    monkeypatch.setenv("SUPABASE_URL", "https://mock-supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "mock-anon-key")
    monkeypatch.setenv("USER_JWT", "mock-jwt-token")
    monkeypatch.setenv("USER_ID", "user-uuid-123")
    monkeypatch.setenv("OPENAI_API_KEY", "mock-openai-key")
    
    # 1. Mock OpenAI embeddings creation
    class MockData:
        embedding = [0.01] * 1536
        
    class MockEmbedResponse:
        data = [MockData()]
        
    class MockOpenAI:
        class Embeddings:
            def create(self, *args, **kwargs):
                return MockEmbedResponse()
        embeddings = Embeddings()
        
    # 2. Mock Supabase vector RPC call
    mock_search_results = [
        {
            "id": "chunk-uuid-1",
            "document_id": "doc-uuid-abc",
            "file_name": "paper.pdf",
            "page_number": 5,
            "similarity": 0.8954,
            "content": "Matched vector database chunk text."
        }
    ]
    
    class MockRPCBuilder:
        def execute(self):
            class Response:
                data = mock_search_results
            return Response()

    class MockSupabase:
        def rpc(self, name, params):
            assert name == "match_document_chunks"
            assert params["filter_user_id"] == "user-uuid-123"
            return MockRPCBuilder()
            
    import mcp_server
    monkeypatch.setattr(mcp_server, "get_openai_client", lambda: MockOpenAI())
    monkeypatch.setattr(mcp_server, "create_client", lambda *args, **kwargs: MockSupabase())
    
    text_content = await search_knowledge(
        query="mock search text"
    )
    assert "paper.pdf" in text_content
    assert "Page 5" in text_content
    assert "Matched vector database" in text_content
