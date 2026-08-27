import pytest
from app.database.supabase import get_supabase_client, get_supabase_user_client
from app.core.config import settings

def test_supabase_client_creation_missing_keys(monkeypatch):
    """Test that client helper raises ValueError when credentials are empty."""
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
    
    with pytest.raises(ValueError) as excinfo:
        get_supabase_client()
    assert "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY" in str(excinfo.value)

def test_supabase_user_client_creation_missing_keys(monkeypatch):
    """Test that user client helper raises ValueError when anon key is empty."""
    monkeypatch.setattr(settings, "SUPABASE_URL", "")
    monkeypatch.setattr(settings, "SUPABASE_ANON_KEY", "")
    
    with pytest.raises(ValueError) as excinfo:
        get_supabase_user_client("mock-token")
    assert "SUPABASE_URL and SUPABASE_ANON_KEY" in str(excinfo.value)

def test_supabase_client_instantiation_valid_config(monkeypatch):
    """
    Test client instantiators with simulated config values.
    Since we aren't executing network requests, we mock the create_client call.
    """
    mock_url = "https://mock.supabase.co"
    mock_key = "mock-role-key"
    mock_anon = "mock-anon-key"
    
    monkeypatch.setattr(settings, "SUPABASE_URL", mock_url)
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", mock_key)
    monkeypatch.setattr(settings, "SUPABASE_ANON_KEY", mock_anon)
    
    # Verify client creation runs settings validation
    # (Since we are using valid URLs, create_client will execute, but might fail on actual HTTP unless mocked)
    # We can mock create_client to verify parameters passed to it
    import app.database.supabase as db_mod
    
    calls = []
    def mock_create_client(supabase_url, supabase_key, options=None):
        calls.append((supabase_url, supabase_key, options))
        return "mocked-client"
        
    monkeypatch.setattr(db_mod, "create_client", mock_create_client)
    
    admin_client = get_supabase_client()
    assert admin_client == "mocked-client"
    assert calls[0][0] == mock_url
    assert calls[0][1] == mock_key
    
    user_client = get_supabase_user_client("my-jwt-token")
    assert user_client == "mocked-client"
    assert calls[1][0] == mock_url
    assert calls[1][1] == mock_anon
    assert calls[1][2].headers["Authorization"] == "Bearer my-jwt-token"
