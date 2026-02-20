import requests
import json

LLM_GATEWAY = "http://192.168.132.223:8080/v1/chat/completions"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

def analyze_email_with_llm(email_data: dict) -> dict:
    """
    Analyze an email and return a dictionary containing priority, sentiment, action type, and summary.

    :param email_data: A dictionary containing email details with keys 'subject', 'from_address', and 'body_text'.
    :return: A dictionary with keys 'priority', 'sentiment', 'action_type', and 'summary'.
    """
    prompt = f"""Analyze this email and respond with JSON only:
Subject: {email_data.get("subject", "")}
From: {email_data.get("from_address", "")}
Body: {email_data.get("body_text", "")[:500]}

Return JSON: {{"priority": 1-5, "sentiment": "positive|neutral|negative", "action_type": "reply_needed|fyi|none", "summary": "brief summary"}}"""
    
    response = requests.post(
        LLM_GATEWAY, 
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model": "qwen2.5-coder-32b", "messages": [{"role": "user", "content": prompt}], "max_tokens": 200},
        timeout=30
    )
    
    result = response.json()["choices"][0]["message"]["content"]
    return json.loads(result)