import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.chat_service import ChatService

client = TestClient(app)

def test_chat_endpoints_unauthorized():
    """Verify requesting chat operations without authentication returns 401 Unauthorized."""
    # List sessions unauthorized
    response = client.get("/api/chat/session")
    assert response.status_code == 401
    
    # Create session unauthorized
    response = client.post("/api/chat/session", json={"title": "Test"})
    assert response.status_code == 401

def test_create_chat_session_success(monkeypatch):
    """Verify creating a session returns details and registers it successfully."""
    headers = {"Authorization": "Bearer mock-user-token"}
    mock_session = {
        "id": "session-uuid-12345",
        "user_id": "de305d54-75b4-431b-adb2-eb6b9e546013",
        "title": "New Conversation",
        "created_at": "2026-08-28T00:00:00Z",
        "updated_at": "2026-08-28T00:00:00Z"
    }
    
    def mock_create_session(current_user, jwt_token, title):
        return mock_session
        
    monkeypatch.setattr(ChatService, "create_session", mock_create_session)
    
    response = client.post("/api/chat/session", json={"title": "New Conversation"}, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "session-uuid-12345"
    assert data["title"] == "New Conversation"

def test_list_chat_sessions_success(monkeypatch):
    """Verify list_chat_sessions returns all sessions belonging to the user."""
    headers = {"Authorization": "Bearer mock-user-token"}
    mock_list = [
        {
            "id": "session-uuid-12345",
            "title": "Active Chat Thread",
            "updated_at": "2026-08-28T00:00:00Z"
        }
    ]
    
    def mock_list_sessions(current_user, jwt_token):
        return mock_list
        
    monkeypatch.setattr(ChatService, "list_sessions", mock_list_sessions)
    
    response = client.get("/api/chat/session", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "session-uuid-12345"
    assert data[0]["title"] == "Active Chat Thread"

def test_rename_chat_session_success(monkeypatch):
    """Verify renaming a session returns updated details."""
    headers = {"Authorization": "Bearer mock-user-token"}
    
    def mock_rename_session(session_id, current_user, jwt_token, title):
        return {
            "id": session_id,
            "title": title,
            "updated_at": "2026-08-28T00:01:00Z"
        }
        
    monkeypatch.setattr(ChatService, "rename_session", mock_rename_session)
    
    response = client.put("/api/chat/session/session-uuid-12345", json={"title": "Updated Title"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "session-uuid-12345"
    assert data["title"] == "Updated Title"

def test_delete_chat_session_success(monkeypatch):
    """Verify deleting a chat session returns successful status."""
    headers = {"Authorization": "Bearer mock-user-token"}
    
    def mock_delete_session(session_id, current_user, jwt_token):
        return {"message": "Deleted successfully", "id": session_id}
        
    monkeypatch.setattr(ChatService, "delete_session", mock_delete_session)
    
    response = client.delete("/api/chat/session/session-uuid-12345", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "session-uuid-12345"
    assert "Deleted successfully" in data["message"]

def test_get_session_messages_history_success(monkeypatch):
    """Verify message logs inside a session return chronologically."""
    headers = {"Authorization": "Bearer mock-user-token"}
    mock_messages = [
        {
            "id": "msg-1",
            "session_id": "session-uuid-12345",
            "role": "user",
            "content": "Hello assistant.",
            "citations": [],
            "created_at": "2026-08-28T00:00:01Z"
        },
        {
            "id": "msg-2",
            "session_id": "session-uuid-12345",
            "role": "assistant",
            "content": "Hello user, how can I help?",
            "citations": [],
            "created_at": "2026-08-28T00:00:02Z"
        }
    ]
    
    def mock_get_messages(session_id, current_user, jwt_token):
        return mock_messages
        
    monkeypatch.setattr(ChatService, "get_messages", mock_get_messages)
    
    response = client.get("/api/chat/session/session-uuid-12345/messages", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["role"] == "user"
    assert data[1]["role"] == "assistant"
