# Jr Instruction: Add Claude API Backend to Graduated Harness

**Task**: Add Anthropic Claude as an available LLM backend for the harness tier handlers
**Priority**: 3
**Assigned Jr**: Software Engineer Jr.
**Story Points**: 5
**use_rlm**: false

## Context

The graduated harness (lib/harness/) currently routes to local vLLM (Qwen 72B on redfin) and
bmasass DeepSeek. The TierHandler protocol is model-agnostic — it only cares about
HarnessRequest in, TierResult out. Adding Claude as a backend makes the harness a
model-agnostic governance wrapper that can route to ANY inference provider.

DC-11 Macro Polymorphism: the SRE interface is conserved, the implementation (which LLM
answers) speciates freely.

Chief directive: "If I harnessed Claude in our cluster, teaming up with our hardware, this
would be even more black box. I could trust governance to be handled without my oversight."

Council vote: Unanimous YES with conditions (Coyote: misalignment monitor for external API,
Eagle Eye: graceful degradation on failure, Spider: latency-aware routing).

## Steps

### Step 1: Add provider field to EndpointConfig

File: `/ganuda/lib/harness/config.py`

```text
<<<<<<< SEARCH
@dataclass
class EndpointConfig:
    """Configuration for an LLM endpoint (OpenAI-compatible API)."""
    url: str = "http://localhost:8000/v1/chat/completions"
    model: str = "default"
    api_key: str = ""
    timeout_seconds: int = 30
    max_tokens: int = 2048
    temperature: float = 0.7

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EndpointConfig":
        return cls(
            url=d.get("url", "http://localhost:8000/v1/chat/completions"),
            model=d.get("model", "default"),
            api_key=d.get("api_key", ""),
            timeout_seconds=d.get("timeout_seconds", 30),
            max_tokens=d.get("max_tokens", 2048),
            temperature=d.get("temperature", 0.7),
        )
=======
@dataclass
class EndpointConfig:
    """Configuration for an LLM endpoint (OpenAI-compatible or Anthropic API)."""
    url: str = "http://localhost:8000/v1/chat/completions"
    model: str = "default"
    api_key: str = ""
    timeout_seconds: int = 30
    max_tokens: int = 2048
    temperature: float = 0.7
    provider: str = "openai"  # "openai" or "anthropic"

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "EndpointConfig":
        return cls(
            url=d.get("url", "http://localhost:8000/v1/chat/completions"),
            model=d.get("model", "default"),
            api_key=d.get("api_key", ""),
            timeout_seconds=d.get("timeout_seconds", 30),
            max_tokens=d.get("max_tokens", 2048),
            temperature=d.get("temperature", 0.7),
            provider=d.get("provider", "openai"),
        )
>>>>>>> REPLACE
```

### Step 2: Add Anthropic API support to Tier 1 Reflex

File: `/ganuda/lib/harness/tier1_reflex.py`

Route to Anthropic format when provider is "anthropic". Add after the `_call_endpoint` method:

```text
<<<<<<< SEARCH
    def _estimate_confidence(self, answer: str) -> float:
=======
    def _call_anthropic(
        self,
        endpoint: EndpointConfig,
        prompt: str,
    ) -> tuple:
        """Call Anthropic Claude API using messages format.

        Converts to Anthropic's message format, calls the API, and normalizes
        the response back to the same (answer_text, success_bool) tuple format.
        """
        import os
        api_key = endpoint.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            logger.error("Anthropic API key not configured")
            return ("", False)

        payload = {
            "model": endpoint.model,
            "max_tokens": endpoint.max_tokens,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        try:
            response = self._session.post(
                endpoint.url,
                json=payload,
                headers=headers,
                timeout=endpoint.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()

            # Extract text from Anthropic response format
            content_blocks = data.get("content", [])
            if content_blocks:
                answer = content_blocks[0].get("text", "")
                if answer:
                    return (answer.strip(), True)

            logger.warning("Empty response from Anthropic API")
            return ("", False)

        except requests.exceptions.Timeout:
            logger.warning(
                "Timeout calling Anthropic API (limit: %ds)",
                endpoint.timeout_seconds,
            )
            return ("", False)
        except requests.exceptions.ConnectionError:
            logger.warning("Connection error calling Anthropic API")
            return ("", False)
        except requests.exceptions.HTTPError as e:
            logger.warning("HTTP error from Anthropic API: %s", e)
            return ("", False)
        except Exception as e:
            logger.error("Unexpected error calling Anthropic API: %s", e)
            return ("", False)

    def _estimate_confidence(self, answer: str) -> float:
>>>>>>> REPLACE
```

Now update `_call_endpoint` to route based on provider:

```text
<<<<<<< SEARCH
    def _call_endpoint(
        self,
        endpoint: EndpointConfig,
        prompt: str,
    ) -> tuple:
        """Call an OpenAI-compatible chat completion endpoint.

        Args:
            endpoint: The endpoint configuration.
            prompt: The formatted prompt string.

        Returns:
            Tuple of (answer_text, success_bool).
        """
        headers = {"Content-Type": "application/json"}
=======
    def _call_endpoint(
        self,
        endpoint: EndpointConfig,
        prompt: str,
    ) -> tuple:
        """Call an LLM endpoint. Routes to Anthropic or OpenAI-compatible based on provider.

        Args:
            endpoint: The endpoint configuration.
            prompt: The formatted prompt string.

        Returns:
            Tuple of (answer_text, success_bool).
        """
        # Route to Anthropic if provider is set
        if getattr(endpoint, 'provider', 'openai') == 'anthropic':
            return self._call_anthropic(endpoint, prompt)

        headers = {"Content-Type": "application/json"}
>>>>>>> REPLACE
```

### Step 3: Add Claude endpoint to harness config

File: `/ganuda/lib/harness/config.yaml`

```text
<<<<<<< SEARCH
  enable_thermal_audit: true
=======
  enable_thermal_audit: true

# --- Claude Backend ---
# DC-11: External API as REACT enzyme. Governance stays local.
# SENSE and EVALUATE always run on redfin. Only REACT speciates.
# Requires ANTHROPIC_API_KEY in secrets.env.
# NOT a default tier -- used when explicitly routed or as Tier 2 fallback.
claude_endpoint:
  url: "https://api.anthropic.com/v1/messages"
  model: "claude-sonnet-4-6"
  api_key: "${ANTHROPIC_API_KEY}"
  timeout_seconds: 30
  max_tokens: 4096
  temperature: 0.7
  provider: "anthropic"
>>>>>>> REPLACE
```

## Verification

```text
cd /ganuda && python3 -c "
from lib.harness.config import EndpointConfig

# Test provider field
ep = EndpointConfig.from_dict({
    'url': 'https://api.anthropic.com/v1/messages',
    'model': 'claude-sonnet-4-6',
    'provider': 'anthropic',
    'timeout_seconds': 30,
})
print(f'Provider: {ep.provider}')
assert ep.provider == 'anthropic'

# Test default is openai
ep2 = EndpointConfig()
print(f'Default provider: {ep2.provider}')
assert ep2.provider == 'openai'

print('EndpointConfig provider field: OK')
"
```

## Notes

- The ANTHROPIC_API_KEY must be added to /ganuda/config/secrets.env
- Claude is added as an OPTION, not as default routing target
- Routing decisions (when to use Claude vs local) will be a separate task
- SENSE, EVALUATE, CALIBRATE always run locally — only REACT uses external API
- No data leaves the building unless explicitly routed to Claude endpoint
- The misalignment monitor (JR-MISALIGNMENT-MONITOR) watches external API immune breach rate
- If breach rate exceeds threshold, circuit breaker trips and routes locally
- Council vote: unanimous YES with Coyote/Eagle Eye/Spider conditions
