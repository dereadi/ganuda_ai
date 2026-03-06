import time
from typing import Callable, Any

class RateLimitHandler:
    """
    Handles rate limiting for API requests.
    """

    def __init__(self, max_requests: int, window_size: int):
        """
        Initializes the RateLimitHandler with a maximum number of requests and a window size in seconds.

        :param max_requests: Maximum number of requests allowed within the window size.
        :param window_size: Time window in seconds during which the max_requests limit applies.
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = []
        self.last_reset_time = time.time()

    def _reset_window(self) -> None:
        """
        Resets the request window if the current time exceeds the window size.
        """
        current_time = time.time()
        if current_time - self.last_reset_time > self.window_size:
            self.requests = []
            self.last_reset_time = current_time

    def _is_rate_limited(self) -> bool:
        """
        Checks if the current request would exceed the rate limit.

        :return: True if the request would exceed the rate limit, False otherwise.
        """
        self._reset_window()
        return len(self.requests) >= self.max_requests

    def handle_request(self, func: Callable[[Any], Any], *args, **kwargs) -> Any:
        """
        Wraps the given function to enforce rate limiting.

        :param func: The function to be called.
        :param args: Positional arguments to pass to the function.
        :param kwargs: Keyword arguments to pass to the function.
        :return: The result of the function call, or None if rate limited.
        """
        if self._is_rate_limited():
            return None
        self.requests.append(time.time())
        return func(*args, **kwargs)