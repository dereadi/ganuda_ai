from flask import Blueprint, request, jsonify
import httpx
import os

vlm_bp = Blueprint('vlm', __name__, url_prefix='/api/vlm')

GATEWAY = os.getenv('LLM_GATEWAY_URL', 'http://localhost:8080')
API_KEY = os.getenv('LLM_API_KEY', 'ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5')

@vlm_bp.route('/health', methods=['GET'])
def health() -> dict:
    """
    Check the health of the VLM service.
    
    Returns:
        dict: JSON response from the VLM service or an error message.
    """
    try:
        response = httpx.get(f"{GATEWAY}/v1/vlm/health", timeout=5.0)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

@vlm_bp.route('/describe', methods=['POST'])
def describe() -> dict:
    """
    Send a description request to the VLM service.
    
    Returns:
        dict: JSON response from the VLM service.
    """
    data = request.json or {}
    response = httpx.post(
        f"{GATEWAY}/v1/vlm/describe",
        json=data,
        headers={"X-API-Key": API_KEY},
        timeout=120.0
    )
    return jsonify(response.json())

@vlm_bp.route('/analyze', methods=['POST'])
def analyze() -> dict:
    """
    Send an analysis request to the VLM service.
    
    Returns:
        dict: JSON response from the VLM service.
    """
    data = request.json or {}
    response = httpx.post(
        f"{GATEWAY}/v1/vlm/analyze",
        json=data,
        headers={"X-API-Key": API_KEY},
        timeout=120.0
    )
    return jsonify(response.json())

@vlm_bp.route('/ask', methods=['POST'])
def ask() -> dict:
    """
    Send a question to the VLM service.
    
    Returns:
        dict: JSON response from the VLM service.
    """
    data = request.json or {}
    response = httpx.post(
        f"{GATEWAY}/v1/vlm/ask",
        json=data,
        headers={"X-API-Key": API_KEY},
        timeout=120.0
    )
    return jsonify(response.json())