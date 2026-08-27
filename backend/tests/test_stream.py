import pytest
import json
from fastapi.testclient import TestClient
from app.main import app
from app.rag.citations import CitationParser
from app.services.chat_service import ChatService
from app.agent.orchestrator import AgentOrchestrator

client = TestClient(app)

def test_citation_parser_extraction():
    """Verify CitationParser correctly matches document and page tags using regex."""
    text = (
        "Here is some information [File: report.pdf | Page: 12]. "
        "And another detail here [File: data_sheet.pdf | Page: 3]. "
        "Malformed tags should be ignored [File: invalid.pdf | Page: abc]."
    )
    
    citations = CitationParser.extract_citations(text)
    assert len(citations) == 2
    assert citations[0]["file_name"] == "report.pdf"
    assert citations[0]["page_number"] == 12
    assert citations[1]["file_name"] == "data_sheet.pdf"
    assert citations[1]["page_number"] == 3

def test_stream_unauthorized():
    """Verify streaming endpoint blocks requests without credentials."""
    response = client.post("/api/chat/session/session-id/stream", json={"message": "hello"})
    assert response.status_code == 401

def test_stream_success(monkeypatch):
    """Verify streaming endpoint creates SSE channels and yields formatted data blocks."""
    headers = {"Authorization": "Bearer mock-user-token"}
    session_id = "session-uuid-12345"
    
    # 1. Mock DB session checking and messages persistence
    def mock_get_session(sid, user, token):
        return {"id": sid, "user_id": str(user.id)}
        
    mock_messages = []
    def mock_save_message(session_id, current_user, jwt_token, role, content, citations=None):
        msg = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "citations": citations or []
        }
        mock_messages.append(msg)
        return msg
        
    def mock_get_messages(session_id, current_user, jwt_token):
        return mock_messages

    monkeypatch.setattr(ChatService, "get_session", mock_get_session)
    monkeypatch.setattr(ChatService, "save_message", mock_save_message)
    monkeypatch.setattr(ChatService, "get_messages", mock_get_messages)

    # 2. Mock AgentOrchestrator loop to stream events
    async def mock_run_chat_loop(self, user_id, jwt_token, chat_history):
        yield {"type": "text", "content": "Self-attention is key "}
        yield {"type": "text", "content": "[File: attention.pdf | Page: 4]."}

    monkeypatch.setattr(AgentOrchestrator, "run_chat_loop", mock_run_chat_loop)

    # 3. Request streaming response from FastAPI
    response = client.post(
        f"/api/chat/session/{session_id}/stream",
        json={"message": "Tell me about self-attention."},
        headers=headers
    )
    
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # 4. Parse Server-Sent Events output lines
    events = []
    for line in response.iter_lines():
        if line.startswith("data: "):
            data_str = line[6:]
            # Skip empty done markers or keep them
            events.append(json.loads(data_str))

    assert len(events) == 3 # 2 text chunks + 1 done chunk
    assert events[0]["type"] == "text"
    assert events[0]["content"] == "Self-attention is key "
    assert events[1]["type"] == "text"
    assert events[1]["content"] == "[File: attention.pdf | Page: 4]."
    assert events[2]["type"] == "done"

    # Verify both User query and Assistant grounded answer (with parsed citations) saved to DB
    assert len(mock_messages) == 2
    assert mock_messages[0]["role"] == "user"
    assert mock_messages[0]["content"] == "Tell me about self-attention."
    
    assert mock_messages[1]["role"] == "assistant"
    assert "Self-attention is key" in mock_messages[1]["content"]
    assert len(mock_messages[1]["citations"]) == 1
    assert mock_messages[1]["citations"][0]["file_name"] == "attention.pdf"
    assert mock_messages[1]["citations"][0]["page_number"] == 4
