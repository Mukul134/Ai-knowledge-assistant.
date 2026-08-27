from supabase import create_client, Client
from supabase.client import ClientOptions
from app.core.config import settings

def get_supabase_client() -> Client:
    """
    Get a Supabase client authenticated with the service role key.
    This client has superuser/admin privileges and bypasses RLS.
    Use this for background tasks, initial ingestion writing, and admin chores.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured in environment.")
    
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
    )

def get_supabase_user_client(jwt_token: str) -> Client:
    """
    Get a Supabase client authenticated with a user's JWT access token.
    This client acts in the security context of the user and respects RLS.
    Use this for any user-facing API operations (chat, session retrieval, document lists).
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be configured in environment.")
    
    # Inject user's bearer token into the request headers for Row Level Security verification
    options = ClientOptions(
        headers={
            "Authorization": f"Bearer {jwt_token}"
        }
    )
    
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_ANON_KEY,
        options=options
    )
