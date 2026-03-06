from typing import Dict, Any, Optional
import logging
from ganuda.backend.federation_extension.models import FederationRequest, FederationResponse
from ganuda.backend.federation_extension.utils import validate_federation_request, process_federation_data

logger = logging.getLogger(__name__)

class ExtensionHandler:
    """
    Handles the logic for the federation extension.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the ExtensionHandler with the provided configuration.

        :param config: Configuration dictionary containing necessary settings.
        """
        self.config = config

    def handle_request(self, request: FederationRequest) -> FederationResponse:
        """
        Processes the incoming federation request and returns a response.

        :param request: The FederationRequest object containing the request data.
        :return: A FederationResponse object containing the processed data.
        """
        # Validate the incoming request
        if not validate_federation_request(request):
            logger.error("Invalid federation request")
            return FederationResponse(success=False, message="Invalid request")

        # Process the federation data
        try:
            processed_data = process_federation_data(request.data)
            return FederationResponse(success=True, message="Request processed successfully", data=processed_data)
        except Exception as e:
            logger.exception(f"Error processing federation request: {e}")
            return FederationResponse(success=False, message=f"Error processing request: {e}")

# Example usage
if __name__ == "__main__":
    config = {
        "key1": "value1",
        "key2": "value2"
    }
    handler = ExtensionHandler(config)
    request = FederationRequest(data={"example_key": "example_value"})
    response = handler.handle_request(request)
    print(response)