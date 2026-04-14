# /ganuda/services/security/consultation_ring.py

from typing import Dict, Any, Optional
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ModelEndpoint(BaseModel):
    name: str
    url: str
    headers: Optional[Dict[str, str]] = None

class ConsultationRequest(BaseModel):
    model: str
    input: Dict[str, Any]

# In-memory storage for model endpoints
model_endpoints: Dict[str, ModelEndpoint] = {}

@app.post("/add_model/")
def add_model(model: ModelEndpoint):
    """
    Adds a new model endpoint to the consultation ring.
    """
    model_endpoints[model.name] = model
    return {"message": f"Model {model.name} added successfully"}

@app.post("/consult/")
def consult(request: ConsultationRequest):
    """
    Sends a consultation request to the specified model.
    """
    model = model_endpoints.get(request.model)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {request.model} not found")

    try:
        response = requests.post(model.url, json=request.input, headers=model.headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

# Example usage
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)