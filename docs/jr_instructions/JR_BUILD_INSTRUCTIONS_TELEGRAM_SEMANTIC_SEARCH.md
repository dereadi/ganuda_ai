# Jr Build Instructions: Telegram Bot Semantic Search

## Priority: MEDIUM - Enhances User Experience

---

## Overview

Add semantic search capability to the Cherokee Chief Telegram Bot. This allows users to search thermal memory using natural language queries via the federated embedding service.

**Bot Location**: `/ganuda/telegram_bot/telegram_chief.py`
**Embedding Service**: `http://localhost:8003` (redfin)

---

## Changes Required

### 1. Add search_memories Method to TribeInterface

After the `get_iot_summary` method, add:

```python
def search_memories(self, query: str, limit: int = 5, threshold: float = 0.6) -> list:
    """Semantic search in thermal memory via embedding service"""
    try:
        response = requests.post(
            "http://localhost:8003/v1/search",
            json={
                "query": query,
                "scope": "central",
                "limit": limit,
                "threshold": threshold
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
```

### 2. Add /remember Command Handler

After the IoT handlers in `main()`, add:

```python
app.add_handler(CommandHandler("remember", remember_command))
```

### 3. Add remember_command Function

Add this async function:

```python
async def remember_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search thermal memory - /remember <query>"""
    if not context.args:
        await update.message.reply_text("Usage: /remember <search query>\n\nExample: /remember security concerns")
        return

    query = " ".join(context.args)
    tribe = TribeInterface()

    await update.message.reply_text(f"Searching thermal memory for: {query}...")

    results = tribe.search_memories(query, limit=5)

    if isinstance(results, dict) and "error" in results:
        await update.message.reply_text(f"Search error: {results['error']}")
        return

    if not results:
        await update.message.reply_text("No relevant memories found.")
        return

    response = f"Found {len(results)} memories:\n\n"
    for i, r in enumerate(results, 1):
        similarity = r.get('similarity', 0) * 100
        content = r.get('content', '')[:200]
        source = r.get('source', 'central')
        response += f"{i}. [{similarity:.0f}%] ({source})\n{content}...\n\n"

    await update.message.reply_text(response[:4000])  # Telegram limit
```

### 4. Update Help Text

Add to the help_command response:

```python
"Memory Commands:\n"
"/remember <query> - Search thermal memory\n\n"
```

---

## Testing

```bash
# In Telegram, send:
/remember security vulnerabilities
/remember database optimization
/remember authentication
```

---

## Success Criteria

- [ ] `/remember` command works in Telegram
- [ ] Returns semantically similar memories
- [ ] Shows similarity percentage
- [ ] Handles errors gracefully
- [ ] Help text updated

---

*For Seven Generations*
