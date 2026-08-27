import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.document_service import DocumentService

client = TestClient(app)

def test_upload_pdf_unauthorized():
    """Test that uploading a PDF without credentials fails with 401 Unauthorized."""
    file_data = {"file": ("test.pdf", b"%PDF-1.4 mock content", "application/pdf")}
    response = client.post("/api/documents/upload", files=file_data)
    assert response.status_code == 401

def test_upload_invalid_mime_type(monkeypatch):
    """Test that uploading a text file instead of a PDF fails with 400 Bad Request."""
    # Mock authentication to succeed
    headers = {"Authorization": "Bearer mock-user-token"}
    
    file_data = {"file": ("test.txt", b"plain text content", "text/plain")}
    response = client.post("/api/documents/upload", files=file_data, headers=headers)
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]

def test_upload_pdf_size_limit(monkeypatch):
    """Test that uploading a PDF exceeding the 10MB limit fails with 400 Bad Request."""
    headers = {"Authorization": "Bearer mock-user-token"}
    
    # 11MB file payload simulation
    large_payload = b"%PDF-1.4" + b"x" * (11 * 1024 * 1024)
    file_data = {"file": ("large.pdf", large_payload, "application/pdf")}
    
    response = client.post("/api/documents/upload", files=file_data, headers=headers)
    assert response.status_code == 400
    assert "exceeds maximum allowed size of 10MB" in response.json()["detail"]

def test_upload_pdf_success(monkeypatch):
    """Test successful PDF upload and database registration."""
    headers = {"Authorization": "Bearer mock-user-token"}
    file_data = {"file": ("sample.pdf", b"%PDF-1.4 pdf header validation info", "application/pdf")}
    
    mock_doc_record = {
        "id": "doc-uuid-12345",
        "user_id": "de305d54-75b4-431b-adb2-eb6b9e546013",
        "file_name": "sample.pdf",
        "file_path": "de305d54-75b4-431b-adb2-eb6b9e546013/doc-uuid-12345.pdf",
        "file_size": 36,
        "status": "uploaded"
    }
    
    # Mock the static upload_document call in DocumentService
    async def mock_upload_document(file, current_user, background_tasks):
        return mock_doc_record
        
    monkeypatch.setattr(DocumentService, "upload_document", mock_upload_document)
    
    response = client.post("/api/documents/upload", files=file_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "doc-uuid-12345"
    assert data["file_name"] == "sample.pdf"
    assert data["status"] == "uploaded"

def test_list_user_documents_success(monkeypatch):
    """Test fetching user uploaded documents list."""
    headers = {"Authorization": "Bearer mock-user-token"}
    
    mock_docs_list = [
        {
            "id": "doc-uuid-12345",
            "file_name": "sample.pdf",
            "status": "completed",
            "created_at": "2026-08-28T00:00:00Z"
        }
    ]
    
    def mock_list_documents(current_user, jwt_token):
        return mock_docs_list
        
    monkeypatch.setattr(DocumentService, "list_documents", mock_list_documents)
    
    response = client.get("/api/documents", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "doc-uuid-12345"
    assert data[0]["file_name"] == "sample.pdf"

def test_delete_user_document_success(monkeypatch):
    """Test successful document deletion."""
    headers = {"Authorization": "Bearer mock-user-token"}
    
    def mock_delete_document(document_id, current_user, jwt_token):
        return {"message": "Document deleted successfully", "id": document_id}
        
    monkeypatch.setattr(DocumentService, "delete_document", mock_delete_document)
    
    response = client.delete("/api/documents/doc-uuid-12345", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "doc-uuid-12345"
    assert "deleted successfully" in data["message"]
