from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import torch

app = FastAPI()

# Load MedGemma model
model_path = "/ganuda/models/medgemma-1.5"
try:
    nlp_pipeline = pipeline("ner", model=model_path)
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

class TextAnalysisRequest(BaseModel):
    text: str

class TextAnalysisResponse(BaseModel):
    conditions: list
    dates: list
    providers: list
    treatments: list

@app.post("/analyze", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    try:
        # Perform NER on the input text
        results = nlp_pipeline(request.text)
        
        # Extract entities
        conditions = [entity['word'] for entity in results if entity['entity'] == 'CONDITION']
        dates = [entity['word'] for entity in results if entity['entity'] == 'DATE']
        providers = [entity['word'] for entity in results if entity['entity'] == 'PROVIDER']
        treatments = [entity['word'] for entity in results if entity['entity'] == 'TREATMENT']
        
        return TextAnalysisResponse(conditions=conditions, dates=dates, providers=providers, treatments=treatments)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during text analysis: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}