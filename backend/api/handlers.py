from flask import request, jsonify
from functools import wraps
from ganuda.backend.cache import cache
from typing import Callable, Any

def cached(timeout: int = 50) -> Callable:
    """
    Decorator to add caching to API handlers.
    
    :param timeout: Cache timeout in seconds
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            cache_key = f"{request.path}-{request.method}"
            if (cached_response := cache.get(cache_key)) is not None:
                return cached_response
            response = f(*args, **kwargs)
            cache.set(cache_key, response, timeout=timeout)
            return response
        return wrapped
    return decorator

# Example usage
@cached(timeout=60)
def get_data() -> dict:
    """
    Example API handler that fetches data.
    """
    # Simulate data fetching
    data = {"key": "value"}
    return jsonify(data)