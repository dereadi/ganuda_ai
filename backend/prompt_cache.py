import os
import json
from typing import Optional, Dict, Any

class PromptCache:
    """
    A class to handle caching of prompts and their responses.
    """

    def __init__(self, cache_dir: str = 'cache'):
        """
        Initialize the cache with a directory to store the cache files.

        :param cache_dir: Directory to store the cache files.
        """
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_file_path(self, prompt: str) -> str:
        """
        Generate a file path for the given prompt.

        :param prompt: The prompt to generate a file path for.
        :return: The file path for the cache file.
        """
        # Hash the prompt to create a unique filename
        import hashlib
        hash_object = hashlib.sha256(prompt.encode())
        hex_dig = hash_object.hexdigest()
        return os.path.join(self.cache_dir, f"{hex_dig}.json")

    def get(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the cached response for a given prompt.

        :param prompt: The prompt to retrieve the cached response for.
        :return: The cached response if it exists, otherwise None.
        """
        cache_file_path = self._get_cache_file_path(prompt)
        if os.path.exists(cache_file_path):
            with open(cache_file_path, 'r') as file:
                return json.load(file)
        return None

    def set(self, prompt: str, response: Dict[str, Any]) -> None:
        """
        Store the response for a given prompt in the cache.

        :param prompt: The prompt to store the response for.
        :param response: The response to store.
        """
        cache_file_path = self._get_cache_file_path(prompt)
        with open(cache_file_path, 'w') as file:
            json.dump(response, file, indent=4)

    def clear(self) -> None:
        """
        Clear all cached responses.
        """
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")