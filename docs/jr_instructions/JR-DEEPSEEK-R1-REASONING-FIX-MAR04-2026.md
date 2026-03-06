# Fix DeepSeek R1 Empty Response — Reasoning Field Extraction

## Context
Coyote Cam (DC-5 first scan) detected: DeepSeek bmasass:8800 returned empty on 2/2 calls.
Root cause confirmed via SSH: DeepSeek R1 is a reasoning model. It returns a `reasoning` field
with its chain-of-thought and a `content` field with the final answer. The reasoning phase
consumes most of the token budget. At max_tokens=500, the model burns all tokens on reasoning
and content is empty.

Evidence:
- max_tokens=200: reasoning only, content=""
- max_tokens=500: reasoning only, content=""
- max_tokens=1000: reasoning=797 chars, content="Hello!" (success)

Two fixes needed:
1. Increase max_tokens floor for DeepSeek from 500 to 1500
2. Extract reasoning field as fallback when content is empty

Kanban: #1955 | Long Man phase: BUILD (Coyote Cam signal response)

## Changes

### Step 1: Increase DeepSeek max_tokens floor

File: `/ganuda/lib/specialist_council.py`

```
<<<<<<< SEARCH
        if b == DEEPSEEK_BACKEND:
            max_tokens = max(max_tokens, 500)
=======
        if b == DEEPSEEK_BACKEND:
            max_tokens = max(max_tokens, 1500)
>>>>>>> REPLACE
```

### Step 2: Extract reasoning field when content is empty

File: `/ganuda/lib/specialist_council.py`

```
<<<<<<< SEARCH
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]

            # DeepSeek fallback: if deep path returns empty, retry on Qwen (mobile bandwidth issue)
            if b == DEEPSEEK_BACKEND and (not content or len(content.strip()) < 10):
=======
            response.raise_for_status()
            resp_data = response.json()["choices"][0]["message"]
            content = resp_data.get("content", "")

            # DeepSeek R1: reasoning model puts chain-of-thought in 'reasoning' field
            # If content is empty but reasoning exists, extract the conclusion
            if b == DEEPSEEK_BACKEND and (not content or len(content.strip()) < 10):
                reasoning = resp_data.get("reasoning", "")
                if reasoning and len(reasoning.strip()) > 20:
                    # Use the last paragraph of reasoning as the response
                    paragraphs = [p.strip() for p in reasoning.split("\n\n") if p.strip()]
                    content = paragraphs[-1] if paragraphs else reasoning[-500:]
                    print(f"[COUNCIL] {specialist_id} -> Extracted from DeepSeek reasoning ({len(reasoning)} chars)")

            # DeepSeek fallback: if STILL empty after reasoning extraction, retry on Qwen
            if b == DEEPSEEK_BACKEND and (not content or len(content.strip()) < 10):
>>>>>>> REPLACE
```

## Verification
1. Council vote with high_stakes=True routes Turtle/Raven to DeepSeek
2. DeepSeek returns non-empty content (either direct or extracted from reasoning)
3. Fallback to Qwen only triggers if BOTH content AND reasoning are empty
4. Token spend per DeepSeek call increases but reasoning quality preserved
