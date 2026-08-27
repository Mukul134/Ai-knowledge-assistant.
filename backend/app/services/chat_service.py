from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.database.supabase import get_supabase_user_client
from app.core.security import CurrentUser

class ChatService:
    @staticmethod
    def create_session(
        current_user: CurrentUser, 
        jwt_token: str, 
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new chat session for the authenticated user.
        Enforces user isolation via user-session client writes.
        """
        user_supabase = get_supabase_user_client(jwt_token)
        
        session_data = {
            "user_id": str(current_user.id)
        }
        if title:
            session_data["title"] = title
            
        try:
            response = user_supabase.table("chat_sessions").insert(session_data).execute()
            if not response.data:
                raise Exception("No data returned from session insert")
            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create chat session: {str(e)}"
            )

    @staticmethod
    def list_sessions(current_user: CurrentUser, jwt_token: str) -> List[Dict[str, Any]]:
        """
        List all chat sessions belonging to the authenticated user.
        """
        user_supabase = get_supabase_user_client(jwt_token)
        try:
            response = user_supabase.table("chat_sessions") \
                .select("*") \
                .order("updated_at", descending=True) \
                .execute()
            return response.data or []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list chat sessions: {str(e)}"
            )

    @staticmethod
    def get_session(
        session_id: str, 
        current_user: CurrentUser, 
        jwt_token: str
    ) -> Dict[str, Any]:
        """
        Retrieve details of a specific chat session.
        Enforces RLS.
        """
        user_supabase = get_supabase_user_client(jwt_token)
        try:
            response = user_supabase.table("chat_sessions") \
                .select("*") \
                .eq("id", session_id) \
                .execute()
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found or access denied."
                )
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch chat session: {str(e)}"
            )

    @staticmethod
    def rename_session(
        session_id: str, 
        current_user: CurrentUser, 
        jwt_token: str, 
        title: str
    ) -> Dict[str, Any]:
        """
        Rename an existing chat session.
        """
        user_supabase = get_supabase_user_client(jwt_token)
        
        # Verify ownership first (handled implicitly by RLS update)
        try:
            response = user_supabase.table("chat_sessions") \
                .update({"title": title}) \
                .eq("id", session_id) \
                .execute()
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found or update denied."
                )
            return response.data[0]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to rename session: {str(e)}"
            )

    @staticmethod
    def delete_session(
        session_id: str, 
        current_user: CurrentUser, 
        jwt_token: str
    ) -> Dict[str, Any]:
        """
        Delete a chat session and all cascading message logs.
        """
        user_supabase = get_supabase_user_client(jwt_token)
        try:
            # RLS handles access verification, cascading foreign keys delete messages
            response = user_supabase.table("chat_sessions") \
                .delete() \
                .eq("id", session_id) \
                .execute()
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found or deletion denied."
                )
            return {"message": "Chat session and logs deleted successfully.", "id": session_id}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete session: {str(e)}"
            )

    @staticmethod
    def get_messages(
        session_id: str, 
        current_user: CurrentUser, 
        jwt_token: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all message lines inside a session, ordered chronologically.
        """
        user_supabase = get_supabase_user_client(jwt_token)
        
        # Ensure the session belongs to user (implicit check: query message constraints)
        try:
            response = user_supabase.table("messages") \
                .select("*") \
                .eq("session_id", session_id) \
                .order("created_at", descending=False) \
                .execute()
            return response.data or []
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch conversation history: {str(e)}"
            )

    @staticmethod
    def save_message(
        session_id: str,
        current_user: CurrentUser,
        jwt_token: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Save a single message entry (either user, assistant, or tool) into the database.
        Enforces ownership validations via RLS context checks.
        """
        user_supabase = get_supabase_user_client(jwt_token)
        
        message_data = {
            "session_id": session_id,
            "user_id": str(current_user.id),
            "role": role,
            "content": content,
            "citations": citations or []
        }
        
        try:
            response = user_supabase.table("messages").insert(message_data).execute()
            if not response.data:
                raise Exception("No data returned from message save")
            return response.data[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save message log: {str(e)}"
            )
