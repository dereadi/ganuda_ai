# /ganuda/backend/security/consultation_ring.py

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from .models import ModelEndpoint, CapybaraModel
from .security import validate_api_key

router = APIRouter()

class ConsultationRequest(BaseModel):
    input_data: str
    model: Optional[str] = "capybara"

class ConsultationResponse(BaseModel):
    output_data: str
    model_used: str

@router.post("/consult", response_model=ConsultationResponse)
async def consult(request: ConsultationRequest):
    """
    Endpoint to consult a model for a given input.
    """
    api_key = request.headers.get("X-API-Key")
    if not validate_api_key(api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

    model_name = request.model.lower()
    if model_name == "capybara":
        model = CapybaraModel()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported model: {model_name}")

    try:
        output_data = model.process_input(request.input_data)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return ConsultationResponse(output_data=output_data, model_used=model_name)

# Example usage of the CapybaraModel
class CapybaraModel(ModelEndpoint):
    def process_input(self, input_data: str) -> str:
        """
        Process the input data using the Capybara model.
        """
        # Placeholder for actual model processing logic
        return f"Capybara processed: {input_data}"