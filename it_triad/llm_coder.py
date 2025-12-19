"""
LLM Code Generator using Ollama API

This module provides code generation capabilities for IT Jr agents
using locally hosted LLMs via Ollama.
"""

import requests
import json
import logging
import re
from typing import Optional, Dict, Any, List

# Configuration
OLLAMA_HOST = "http://localhost:11434"
CODE_MODEL = "qwen2.5-coder:14b"
CHAT_MODEL = "llama3.1:8b"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class LLMCoder:
    """Code generator using Ollama API."""
    
    def __init__(self, model: str = None, host: str = None):
        self.model = model or CODE_MODEL
        self.host = host or OLLAMA_HOST
        self.api_url = f"{self.host}/api/generate"
        logger.info(f"LLMCoder initialized with model={self.model}, host={self.host}")
        
    def _call_ollama(self, prompt: str, temperature: float = 0.7, 
                     max_tokens: int = 4096) -> Optional[str]:
        """Call Ollama API and return response."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            logger.info(f"Calling Ollama with model {self.model}...")
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out after 120 seconds")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            return None
    
    def generate_code(self, prompt: str, language: str = "python",
                      temperature: float = 0.3, max_tokens: int = 4096) -> Optional[str]:
        """Generate code from a natural language prompt."""
        system_prompt = f"""You are an expert {language} developer. Generate clean, well-documented code.
Only output the code, no explanations. Use proper indentation and follow best practices.

Task: {prompt}

{language.upper()} CODE:"""
        
        response = self._call_ollama(system_prompt, temperature, max_tokens)
        if response:
            return self._extract_code(response, language)
        return None
    
    def _extract_code(self, response: str, language: str) -> str:
        """Extract code from response, handling markdown code blocks."""
        # Try to extract from markdown code block
        pattern = rf"```(?:{language})?\s*(.*?)```"
        matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
        if matches:
            return matches[0].strip()
        # No code block, return cleaned response
        return response.strip()
    
    def generate_function(self, name: str, description: str,
                          params: str = "", return_type: str = "") -> Optional[str]:
        """Generate a single function."""
        prompt = f"Create a Python function named `{name}` that {description}"
        if params:
            prompt += f". Parameters: {params}"
        if return_type:
            prompt += f". Returns: {return_type}"
        return self.generate_code(prompt)


class LLMTester:
    """Test generator using Ollama API."""
    
    def __init__(self, model: str = None, host: str = None):
        self.model = model or CODE_MODEL
        self.host = host or OLLAMA_HOST
        self.api_url = f"{self.host}/api/generate"
        
    def generate_tests(self, code: str, requirements: str = "") -> Optional[str]:
        """Generate pytest test cases for the given code."""
        prompt = f"""Generate comprehensive pytest test cases for this Python code:

```python
{code}
```

Requirements: {requirements if requirements else "Test all functions and edge cases."}

Output only the test code with proper pytest imports."""

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 2048}
            }
            response = requests.post(self.api_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            return None


class LLMReviewer:
    """Code reviewer using Ollama API."""
    
    def __init__(self, model: str = None, host: str = None):
        self.model = model or CHAT_MODEL
        self.host = host or OLLAMA_HOST
        self.api_url = f"{self.host}/api/generate"
        
    def review_security(self, code: str) -> Optional[str]:
        """Review code for security issues."""
        prompt = f"""Review this Python code for security vulnerabilities:

```python
{code}
```

Check for: SQL injection, XSS, command injection, hardcoded secrets, 
insecure file operations, and OWASP top 10 vulnerabilities.

Output a structured report with findings and severity levels."""

        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 1024}
            }
            response = requests.post(self.api_url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except Exception as e:
            logger.error(f"Security review failed: {e}")
            return None

    def approve_for_production(self, code: str, test_results: str = "") -> Dict[str, Any]:
        """Final approval gate for production deployment."""
        security_review = self.review_security(code)
        
        # Simple heuristic approval
        approved = True
        issues = []
        
        if security_review:
            lower_review = security_review.lower()
            if any(word in lower_review for word in ["critical", "high severity", "vulnerability found"]):
                approved = False
                issues.append("Security issues detected")
        
        return {
            "approved": approved,
            "security_review": security_review,
            "issues": issues
        }


if __name__ == "__main__":
    print("Testing LLM Code Generator...")
    print("=" * 50)
    
    # Test basic code generation
    coder = LLMCoder()
    result = coder.generate_function(
        name="add_numbers",
        description="Add two numbers together",
        params="a: int, b: int",
        return_type="int"
    )
    
    if result:
        print("SUCCESS! Generated code:")
        print(result)
    else:
        print("FAILED - Check Ollama connection at http://localhost:11434")
