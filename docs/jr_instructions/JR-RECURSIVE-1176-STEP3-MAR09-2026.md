# [RECURSIVE] Qwen3 Think-Tag Strip in Specialist Council - Step 3

**Parent Task**: #1176
**Auto-decomposed**: 2026-03-09T15:23:09.998973
**Original Step Title**: Strip think tags in _query_specialist() content extraction

---

### Step 3: Strip think tags in _query_specialist() content extraction

TARGET FILE: /ganuda/lib/specialist_council.py

<<<< SEARCH
            content = resp_data.get("content", "")

            # DeepSeek R1: reasoning model puts chain-of-thought in 'reasoning' field
>>>> REPLACE
            content = resp_data.get("content", "")
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()

            # DeepSeek R1: reasoning model puts chain-of-thought in 'reasoning' field
<<<<

Test: python3 -c "import py_compile; py_compile.compile('/ganuda/lib/specialist_council.py', doraise=True)"
