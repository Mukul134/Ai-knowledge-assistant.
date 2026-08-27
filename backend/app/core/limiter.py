from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize the global limiter using the client's remote address
# Using in-memory storage for lightweight, zero-dependency rate limiting
limiter = Limiter(key_func=get_remote_address)
