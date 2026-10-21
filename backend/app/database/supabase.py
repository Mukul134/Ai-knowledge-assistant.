"""Backward-compatible import path for the Neon database adapter."""
from app.database.neon import DatabaseClient as Client
from app.database.neon import get_neon_client, get_neon_user_client


def get_supabase_client() -> Client:
    return get_neon_client()


def get_supabase_user_client(_jwt_token: str) -> Client:
    return get_neon_user_client(_jwt_token)
