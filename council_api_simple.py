#!/usr/bin/env python3
"""
🔥 Cherokee Council API - Simple Standalone Version
A minimal API to interact with the Ollama models
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import httpx
import json
import asyncio
from datetime import datetime

app = FastAPI(title="Cherokee Council API", version="1.0.0")

# Council member mapping
COUNCIL_MEMBERS = {
    "coyote": "mistral:latest",
    "eagle": "llama3.2:latest", 
    "gecko": "phi3:mini",
    "spider": "llama3.1:8b",
    "turtle": "qwen2.5:7b",
    "raven": "gemma2:9b",
    "mountain": "llama3.1:70b"
}

class CouncilQuery(BaseModel):
    question: str
    members: Optional[List[str]] = ["coyote", "eagle", "gecko"]
    temperature: Optional[float] = 0.7

class CouncilResponse(BaseModel):
    question: str
    responses: Dict[str, str]
    consensus: Optional[str] = None
    timestamp: str

@app.get("/")
async def root():
    return {
        "message": "🔥 Cherokee Council API Running",
        "endpoints": {
            "/council": "Ask the council a question",
            "/models": "List available models",
            "/health": "Check system health"
        }
    }

@app.get("/models")
async def list_models():
    """List available Ollama models"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://ollama:11434/api/tags")
            models = response.json()
            return {
                "council_members": COUNCIL_MEMBERS,
                "available_models": [m["name"] for m in models.get("models", [])]
            }
    except Exception as e:
        return {"error": str(e), "council_members": COUNCIL_MEMBERS}

@app.post("/council", response_model=CouncilResponse)
async def ask_council(query: CouncilQuery):
    """Ask the council a question and get responses from each member"""
    responses = {}
    
    async def ask_member(member: str, model: str):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": model,
                    "prompt": query.question,
                    "temperature": query.temperature,
                    "stream": False
                }
                
                response = await client.post(
                    "http://ollama:11434/api/generate",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return member, result.get("response", "No response")
                else:
                    return member, f"Error: {response.status_code}"
        except Exception as e:
            return member, f"Error: {str(e)}"
    
    # Ask all council members in parallel
    tasks = []
    for member in query.members:
        if member in COUNCIL_MEMBERS:
            model = COUNCIL_MEMBERS[member]
            tasks.append(ask_member(member, model))
    
    # Wait for all responses
    results = await asyncio.gather(*tasks)
    
    # Compile responses
    for member, response in results:
        responses[member] = response
    
    # Simple consensus (most common theme)
    if len(responses) > 1:
        consensus = f"Council discussed with {len(responses)} members present"
    else:
        consensus = "Single member response"
    
    return CouncilResponse(
        question=query.question,
        responses=responses,
        consensus=consensus,
        timestamp=datetime.now().isoformat()
    )

@app.get("/health")
async def health_check():
    """Check if Ollama is responding"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://ollama:11434/api/tags")
            return {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "ollama": "connected",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "ollama": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)