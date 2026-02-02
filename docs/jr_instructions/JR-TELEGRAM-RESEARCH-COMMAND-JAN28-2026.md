# JR Instruction: Telegram Chief /research Command

**JR ID:** JR-TELEGRAM-RESEARCH-COMMAND-JAN28-2026
**Priority:** P2
**Assigned To:** Telegram Jr.
**Related:** JR-II-RESEARCHER-ASYNC-PATTERN-JAN28-2026

---

## Objective

Add `/research` command to Telegram Chief that queues async research jobs and notifies user when complete.

---

## User Flow

```
User: /research VA tinnitus rating criteria
Bot: 🔍 Research queued (job: research-abc123). I'll notify you when complete (3-5 min).

... 4 minutes later ...

Bot: 📊 Research Complete

Tinnitus is rated under 38 CFR 4.87, Diagnostic Code 6260. The maximum
schedular rating is 10%. Tinnitus is evaluated as recurrent...

Job: research-abc123
```

---

## Implementation

### File: `/ganuda/telegram_bot/telegram_chief.py`

Add to imports:
```python
import requests
```

Add research command handler:
```python
@bot.message_handler(commands=['research'])
def handle_research(message):
    """Queue async research job with Telegram callback."""
    query = message.text.replace('/research', '').strip()

    if not query:
        bot.reply_to(message, "Usage: /research <your question>\n\nExample: /research VA tinnitus rating criteria")
        return

    chat_id = str(message.chat.id)

    try:
        # Queue research job with Telegram callback
        response = requests.post(
            "http://192.168.132.223:8080/v1/research/async",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY  # Use existing bot API key
            },
            json={
                "query": query,
                "max_steps": 5
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            job_id = data.get("job_id", "unknown")

            # Also register for Telegram callback
            register_telegram_callback(job_id, chat_id)

            bot.reply_to(
                message,
                f"🔍 Research queued (job: {job_id}).\n\n"
                f"I'll notify you when complete (3-5 min).\n\n"
                f"Check status: /research_status {job_id}"
            )
        else:
            bot.reply_to(message, f"❌ Failed to queue research: {response.text}")

    except Exception as e:
        bot.reply_to(message, f"❌ Research error: {str(e)}")


def register_telegram_callback(job_id: str, chat_id: str):
    """Update job with Telegram callback info."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='192.168.132.222',
            database='zammad_production',
            user='claude',
            password='jawaseatlasers2'
        )
        cur = conn.cursor()
        cur.execute("""
            UPDATE research_jobs
            SET callback_type = 'telegram', callback_target = %s
            WHERE job_id = %s
        """, (chat_id, job_id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logging.error(f"Failed to register callback: {e}")


@bot.message_handler(commands=['research_status'])
def handle_research_status(message):
    """Check status of a research job."""
    job_id = message.text.replace('/research_status', '').strip()

    if not job_id:
        bot.reply_to(message, "Usage: /research_status <job_id>")
        return

    try:
        response = requests.get(
            f"http://192.168.132.223:8080/v1/research/status/{job_id}",
            headers={"X-API-Key": API_KEY},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "unknown")

            if status == "completed":
                summary = data.get("result_summary", "No summary")
                bot.reply_to(message, f"✅ *Completed*\n\n{summary}", parse_mode="Markdown")
            elif status == "running":
                bot.reply_to(message, "⏳ Still running... Check back soon.")
            elif status == "pending":
                bot.reply_to(message, "📋 Queued, waiting for worker.")
            else:
                error = data.get("error", "Unknown error")
                bot.reply_to(message, f"❌ Failed: {error}")
        else:
            bot.reply_to(message, f"Job not found: {job_id}")

    except Exception as e:
        bot.reply_to(message, f"❌ Status check error: {str(e)}")
```

---

## Environment Variable

Add to research-worker.service:
```ini
Environment=TELEGRAM_BOT_TOKEN=<bot_token_from_telegram_chief>
```

Or source from existing config.

---

## Testing

1. Start Telegram Chief
2. Send: `/research What is the VA rating for sleep apnea?`
3. Wait 3-5 minutes for notification
4. Verify file created in `/ganuda/research/completed/`

---

## Help Text Update

Add to `/help` command output:
```
/research <question> - Queue deep web research (3-5 min)
/research_status <job_id> - Check research job status
```

---

FOR SEVEN GENERATIONS
