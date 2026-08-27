import pytest
from app.rag.chunker import TokenChunker
from app.rag.parser import PDFParser
from app.services.document_service import DocumentService

# =========================================================================
# Chunker Tests
# =========================================================================

def test_chunker_token_count():
    """Verify that token counting correctly invokes tiktoken encoding."""
    chunker = TokenChunker()
    text = "Hello, world! This is a simple token count test."
    # "Hello, world! This is a simple token count test." is roughly 11 tokens in cl100k_base
    token_count = chunker.count_tokens(text)
    assert token_count > 0
    assert isinstance(token_count, int)

def test_chunker_split_small_text():
    """Verify that text smaller than chunk_size is returned as a single chunk."""
    chunker = TokenChunker()
    text = "Short sentence."
    chunks = chunker.split_text_by_tokens(text, chunk_size=512, chunk_overlap=51)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunker_split_large_text():
    """Verify that large text is split with correct overlap sliding windows."""
    chunker = TokenChunker()
    # Create text with approx 100 words (which is ~120-150 tokens)
    word_base = "word " * 150
    
    # We choose small chunk settings to trigger multiple splits
    chunks = chunker.split_text_by_tokens(word_base, chunk_size=30, chunk_overlap=5)
    assert len(chunks) > 1
    
    # Check that chunks overlap (each chunk contains some matching words)
    # The start of the second chunk should contain words from the end of the first
    assert chunks[1].strip().startswith("word")

def test_chunker_page_output_mapping():
    """Verify that chunk_page returns dict structures with proper metadata fields."""
    chunker = TokenChunker()
    page_text = "This is some mock text on page 3 of our document."
    doc_id = "doc-uuid-1"
    user_id = "user-uuid-1"
    file_name = "test.pdf"
    
    chunks = chunker.chunk_page(
        page_text=page_text,
        page_number=3,
        file_name=file_name,
        document_id=doc_id,
        user_id=user_id,
        chunk_size=10, # small chunk size to trigger chunk indexes
        chunk_overlap=2
    )
    
    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert "id" in first_chunk
    assert first_chunk["document_id"] == doc_id
    assert first_chunk["user_id"] == user_id
    assert first_chunk["page_number"] == 3
    assert first_chunk["file_name"] == file_name
    assert "content" in first_chunk
    assert "metadata" in first_chunk
    assert first_chunk["metadata"]["chunk_index"] == 0
    assert "token_count" in first_chunk["metadata"]

# =========================================================================
# Parser Tests
# =========================================================================

def test_parser_empty_pdf_rejection():
    """Verify that empty pages lists or unreadable text raises ValueError."""
    # Passing raw empty bytes should raise standard read errors in pdfplumber
    with pytest.raises(ValueError) as excinfo:
        PDFParser.extract_text_by_page(b"")
    assert "Failed to parse PDF document" in str(excinfo.value)

def test_parser_mocked_success(monkeypatch):
    """
    Test PDF parsing success by mocking pdfplumber layout interfaces.
    Allows us to check extraction routing without compiling physical PDFs.
    """
    # Create mock structures representing pdfplumber objects
    class MockPage:
        def __init__(self, text):
            self.text = text
            
        def extract_text(self):
            return self.text
            
    class MockPDF:
        def __init__(self):
            self.pages = [
                MockPage("Text on page 1 of sample document."),
                MockPage("Text on page 2 representing table data.")
            ]
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    import pdfplumber
    # Patch pdfplumber.open to return our MockPDF instead of attempting to parse raw bytes
    monkeypatch.setattr(pdfplumber, "open", lambda *args, **kwargs: MockPDF())
    
    # Run extractor on dummy bytes
    extracted_pages = PDFParser.extract_text_by_page(b"mock-pdf-binary-payload")
    
    assert len(extracted_pages) == 2
    assert extracted_pages[0]["page_number"] == 1
    assert extracted_pages[0]["text"] == "Text on page 1 of sample document."
    assert extracted_pages[1]["page_number"] == 2
    assert extracted_pages[1]["text"] == "Text on page 2 representing table data."

def test_parser_scanned_rejection(monkeypatch):
    """Verify that PDFs with zero readable text (image-only scans) are rejected."""
    class MockScannedPage:
        def extract_text(self):
            return None # pdfplumber returns None if no text elements exist on page
            
    class MockScannedPDF:
        def __init__(self):
            self.pages = [MockScannedPage()]
            
        def __enter__(self):
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    import pdfplumber
    monkeypatch.setattr(pdfplumber, "open", lambda *args, **kwargs: MockScannedPDF())
    
    with pytest.raises(ValueError) as excinfo:
        PDFParser.extract_text_by_page(b"scanned-pdf-bytes")
    assert "No readable text was extracted" in str(excinfo.value)

# =========================================================================
# Integration / Ingestion Pipeline Tests
# =========================================================================

@pytest.mark.asyncio
async def test_openai_client_get_embeddings(monkeypatch):
    """Verify OpenAI client creates 1536-dimensional float embeddings."""
    from app.llm.openai_client import openai_helper
    
    mock_vector = [0.1] * 1536
    
    class MockData:
        def __init__(self, embedding):
            self.embedding = embedding
            
    class MockResponse:
        def __init__(self, data_list):
            self.data = data_list
            
    async def mock_embeddings_create(*args, **kwargs):
        return MockResponse([MockData(mock_vector)])
        
    monkeypatch.setattr(openai_helper.client.embeddings, "create", mock_embeddings_create)
    
    embeddings = await openai_helper.get_embeddings(["Sample text fragment"])
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 1536
    assert embeddings[0][0] == 0.1

@pytest.mark.asyncio
async def test_process_document_background_success(monkeypatch):
    """Verify the entire background ingestion workflow parses, chunks, embeds, and uploads."""
    # 1. Setup mock returns
    mock_pdf_pages = [
        {"page_number": 1, "text": "This is page one text content."},
        {"page_number": 2, "text": "This is page two text content."}
    ]
    mock_embeddings = [[0.15] * 1536, [0.25] * 1536]
    
    # 2. Patch core utilities
    monkeypatch.setattr(PDFParser, "extract_text_by_page", lambda *args: mock_pdf_pages)
    
    from app.llm.openai_client import openai_helper
    async def mock_get_embeddings(texts):
        return mock_embeddings
    monkeypatch.setattr(openai_helper, "get_embeddings", mock_get_embeddings)
    
    # 3. Mock Supabase database and storage client operations
    db_updates = []
    db_inserts = []
    
    class MockBuilder:
        def __init__(self, table_name):
            self.table_name = table_name
            
        def update(self, data):
            db_updates.append((self.table_name, data))
            return self
            
        def insert(self, data):
            db_inserts.append((self.table_name, data))
            return self
            
        def eq(self, column, value):
            return self
            
        def execute(self):
            return self
            
    class MockStorageBucket:
        def download(self, path):
            return b"mock-pdf-bytes"
            
    class MockStorage:
        def from_(self, bucket_name):
            assert bucket_name == "documents"
            return MockStorageBucket()
            
    class MockSupabaseClient:
        def __init__(self):
            self.storage = MockStorage()
            
        def table(self, table_name):
            return MockBuilder(table_name)
            
    import app.services.document_service as doc_serv_mod
    monkeypatch.setattr(doc_serv_mod, "get_supabase_client", lambda: MockSupabaseClient())
    
    # 4. Execute background process
    await DocumentService.process_document_background(
        document_id="doc-uuid-987",
        storage_path="user-uuid-1/doc-uuid-987.pdf",
        file_name="invoice.pdf",
        user_id="user-uuid-1"
    )
    
    # 5. Verify the background workflow calls database status updates correctly
    # - First update to 'processing'
    # - Second update to 'completed' with page_count
    assert len(db_updates) == 2
    assert db_updates[0] == ("documents", {"status": "processing"})
    assert db_updates[1][0] == "documents"
    assert db_updates[1][1]["status"] == "completed"
    assert db_updates[1][1]["page_count"] == 2
    
    # Verify vector records were bulk-inserted
    assert len(db_inserts) == 1
    assert db_inserts[0][0] == "document_chunks"
    inserted_chunks = db_inserts[0][1]
    assert len(inserted_chunks) == 2 # 1 chunk per page
    assert inserted_chunks[0]["page_number"] == 1
    assert inserted_chunks[0]["embedding"] == [0.15] * 1536
    assert inserted_chunks[1]["page_number"] == 2
    assert inserted_chunks[1]["embedding"] == [0.25] * 1536

@pytest.mark.asyncio
async def test_document_retriever_success(monkeypatch):
    """Verify retriever generates embeddings and calls Supabase vector RPC with correct filters."""
    from app.rag.retriever import DocumentRetriever
    from app.llm.openai_client import openai_helper
    
    mock_query_vector = [0.05] * 1536
    mock_retrieved_chunks = [
        {
            "id": "chunk-1",
            "document_id": "doc-uuid-abc",
            "content": "Grounded chunk text content.",
            "file_name": "context.pdf",
            "page_number": 4,
            "similarity": 0.82
        }
    ]
    
    # 1. Mock OpenAI Embedding call
    async def mock_get_embeddings(texts):
        assert texts == ["transformer design query"]
        return [mock_query_vector]
        
    monkeypatch.setattr(openai_helper, "get_embeddings", mock_get_embeddings)
    
    # 2. Mock Supabase user client RPC call
    rpc_calls = []
    class MockRPCBuilder:
        def __init__(self, function_name, params):
            self.function_name = function_name
            self.params = params
            rpc_calls.append((function_name, params))
            
        def execute(self):
            class Response:
                data = mock_retrieved_chunks
            return Response()
            
    class MockUserSupabase:
        def rpc(self, function_name, params):
            return MockRPCBuilder(function_name, params)
            
    mock_user_client = MockUserSupabase()
    
    # 3. Execute retrieval
    results = await DocumentRetriever.retrieve_relevant_chunks(
        query="transformer design query",
        user_id="user-uuid-xyz",
        supabase_user_client=mock_user_client,
        document_id="doc-uuid-abc",
        top_k=3,
        similarity_threshold=0.5
    )
    
    # 4. Assertions
    assert len(results) == 1
    assert results[0]["id"] == "chunk-1"
    assert results[0]["page_number"] == 4
    
    # Verify RPC arguments were constructed and mapped correctly
    assert len(rpc_calls) == 1
    rpc_name, rpc_params = rpc_calls[0]
    assert rpc_name == "match_document_chunks"
    assert rpc_params["query_embedding"] == mock_query_vector
    assert rpc_params["match_threshold"] == 0.5
    assert rpc_params["match_count"] == 3
    assert rpc_params["filter_user_id"] == "user-uuid-xyz"
    assert rpc_params["filter_document_id"] == "doc-uuid-abc"


