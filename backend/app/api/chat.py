import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from app.core.security import get_current_user, CurrentUser
from app.services.chat_service import ChatService
from app.agent.orchestrator import AgentOrchestrator
from app.rag.citations import CitationParser
from app.core.limiter import limiter

router = APIRouter()

# Schema definitions
class CreateSessionRequest(BaseModel):
    title: Optional[str] = None

class RenameSessionRequest(BaseModel):
    title: str

class ChatMessageRequest(BaseModel):
    message: str

def get_token_from_header(authorization: str = Header(...)) -> str:
    """Helper to retrieve JWT bearer token."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <JWT>'."
        )
    return authorization.split(" ")[1]

@router.post("/session", status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    request: CreateSessionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header)
):
    """Create a new chat conversation session."""
    return ChatService.create_session(current_user, token, request.title)

@router.get("/session", response_model=list[dict])
async def list_chat_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header)
):
    """List all chat sessions belonging to the user."""
    return ChatService.list_sessions(current_user, token)

@router.get("/session/{session_id}")
async def get_chat_session_details(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header)
):
    """Get metadata for a specific chat session."""
    return ChatService.get_session(session_id, current_user, token)

@router.put("/session/{session_id}")
async def rename_chat_session(
    session_id: str,
    request: RenameSessionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header)
):
    """Rename a chat session title."""
    return ChatService.rename_session(session_id, current_user, token, request.title)

@router.delete("/session/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header)
):
    """Delete a chat session and all cascading message records."""
    return ChatService.delete_session(session_id, current_user, token)

@router.get("/session/{session_id}/messages", response_model=list[dict])
async def get_session_message_history(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header)
):
    """Retrieve chronological message log history inside a session."""
    return ChatService.get_messages(session_id, current_user, token)

@router.post("/session/{session_id}/stream")
@limiter.limit("30/minute")
async def stream_chat_response(
    session_id: str,
    request: Request,
    body: ChatMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
    token: str = Depends(get_token_from_header)
):
    """
    Open Server-Sent Events (SSE) stream to run the AI agent loop in real-time,
    persisting query prompts and grounded answers (with citations) to PostgreSQL.
    """
    # 1. Verify session exists and belongs to the authenticated user
    ChatService.get_session(session_id, current_user, token)
    
    # 2. Save user prompt immediately to conversation log
    ChatService.save_message(
        session_id=session_id,
        current_user=current_user,
        jwt_token=token,
        role="user",
        content=body.message
    )

    async def event_generator():
        # Retrieve full history (including the newly saved user prompt)
        history = ChatService.get_messages(session_id, current_user, token)
        
        orchestrator = AgentOrchestrator()
        assistant_text = ""
        
        try:
            async for event in orchestrator.run_chat_loop(
                user_id=str(current_user.id),
                jwt_token=token,
                chat_history=history
            ):
                # Accumulate generated tokens for final DB saving
                if event["type"] == "text":
                    assistant_text += event["content"]
                    
                # Yield JSON payload structured for SSE streaming consumption
                yield {"data": json.dumps(event)}
                
            # 3. Generation complete. Extract citations from assistant's generated text
            citations = CitationParser.extract_citations(assistant_text)
            
            # 4. Persist the final assistant response to the message log
            ChatService.save_message(
                session_id=session_id,
                current_user=current_user,
                jwt_token=token,
                role="assistant",
                content=assistant_text,
                citations=citations
            )
            
            # Emit closing message
            yield {"data": json.dumps({"type": "done"})}
            
        except Exception as e:
            yield {"data": json.dumps({"type": "error", "content": f"Streaming worker error: {str(e)}"})}
            
    return EventSourceResponse(event_generator())
