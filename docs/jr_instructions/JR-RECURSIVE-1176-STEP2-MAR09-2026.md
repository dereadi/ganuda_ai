# [RECURSIVE] Qwen3 Think-Tag Strip in Specialist Council - Step 2

**Parent Task**: #1176
**Auto-decomposed**: 2026-03-09T15:23:09.997173
**Original Step Title**: Strip think tags in query_vllm_sync() return

---

### Step 2: Strip think tags in query_vllm_sync() return

TARGET FILE: /ganuda/lib/specialist_council.py

<<<< SEARCH
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR: {str(e)}]"
>>>> REPLACE
        response.raise_for_status()
        _raw = response.json()["choices"][0]["message"]["content"]
        return re.sub(r'<think>.*?</think>', '', _raw, flags=re.DOTALL).strip()
    except Exception as e:
        return f"[ERROR: {str(e)}]"
<<<<
