import os
import requests
from typing import Dict, Any, Optional

class CloudflareWAFAgent:
    """
    Cloudflare WAF Agent to manage rate limiting.
    """

    def __init__(self, api_key: str, email: str, zone_id: str):
        self.api_key = api_key
        self.email = email
        self.zone_id = zone_id
        self.base_url = "https://api.cloudflare.com/client/v4"

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the Cloudflare API.

        :param method: HTTP method (GET, POST, PUT, DELETE)
        :param endpoint: API endpoint
        :param data: Data to send with the request (optional)
        :return: Response from the API
        """
        headers = {
            "X-Auth-Email": self.email,
            "X-Auth-Key": self.api_key,
            "Content-Type": "application/json"
        }
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()

    def create_rate_limit(self, name: str, threshold: int, period: int, action: str, match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a rate limit rule.

        :param name: Name of the rate limit rule
        :param threshold: Number of requests allowed within the period
        :param period: Time period in seconds
        :param action: Action to take when the rate limit is exceeded (e.g., "ban", "challenge")
        :param match: Conditions for the rate limit rule
        :return: Response from the API
        """
        data = {
            "description": name,
            "threshold": threshold,
            "period": period,
            "action": {
                "mode": action,
                "timeout": 60  # Default timeout of 60 seconds
            },
            "match": match
        }
        return self._make_request("POST", f"zones/{self.zone_id}/rate_limits", data)

    def list_rate_limits(self) -> Dict[str, Any]:
        """
        List all rate limit rules.

        :return: Response from the API
        """
        return self._make_request("GET", f"zones/{self.zone_id}/rate_limits")

    def delete_rate_limit(self, rate_limit_id: str) -> Dict[str, Any]:
        """
        Delete a rate limit rule.

        :param rate_limit_id: ID of the rate limit rule to delete
        :return: Response from the API
        """
        return self._make_request("DELETE", f"zones/{self.zone_id}/rate_limits/{rate_limit_id}")

if __name__ == "__main__":
    # Example usage
    api_key = os.getenv("CLOUDFLARE_API_KEY")
    email = os.getenv("CLOUDFLARE_EMAIL")
    zone_id = os.getenv("CLOUDFLARE_ZONE_ID")

    agent = CloudflareWAFAgent(api_key, email, zone_id)

    # Create a rate limit rule
    match_conditions = {
        "request": {
            "url": {
                "value": "example.com/*",
                "operator": "matches"
            }
        }
    }
    response = agent.create_rate_limit(
        name="Example Rate Limit",
        threshold=100,
        period=60,
        action="ban",
        match=match_conditions
    )
    print(response)

    # List all rate limits
    rate_limits = agent.list_rate_limits()
    print(rate_limits)

    # Delete a rate limit rule
    rate_limit_id = "your_rate_limit_id_here"
    response = agent.delete_rate_limit(rate_limit_id)
    print(response)