# Jr Instruction: Research User Profiles for Telegram Bot

**Task ID**: RESEARCH-PROFILES-001
**Priority**: P1
**Estimated Steps**: 4
**Kanban**: TBD
**Date**: February 9, 2026

## Context

The research pipeline (`/research` command on @ganudabot) treats every user identically. A 35-year sysadmin veteran gets the same beginner-friendly report as someone who installed Ubuntu yesterday. We need user profiles that tune research responses based on WHO is asking.

The integration is clean:
- `telegram_chief_v3.py:370` calls `build_research_query(question, persona)`
- `research_personas.py:107` builds the query with persona prompt + question
- User profiles inject expertise context into this prompt BEFORE dispatch

## Architecture

```
User sends /research → telegram_chief_v3.py
  → lookup user profile (new: user_research_profiles table)
  → build_research_query(question, persona, user_profile)  ← MODIFIED
  → dispatcher.queue_research(full_query, ...)
  → research_worker → ii-researcher → vLLM 72B
  → response tuned to user's expertise level
```

## Step 1: Create Database Table

Run this SQL on the database (host=192.168.132.222, user=claude, db=zammad_production):

```sql
CREATE TABLE IF NOT EXISTS user_research_profiles (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT UNIQUE NOT NULL,
    display_name VARCHAR(100),
    expertise_level VARCHAR(20) DEFAULT 'intermediate'
        CHECK (expertise_level IN ('novice', 'intermediate', 'expert', 'specialist')),
    domains TEXT[] DEFAULT '{}',
    communication_style VARCHAR(30) DEFAULT 'balanced'
        CHECK (communication_style IN ('verbose', 'balanced', 'bullet_points', 'deep_dive', 'executive_summary')),
    context_notes TEXT DEFAULT '',
    preferred_persona VARCHAR(30) DEFAULT 'telegram',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_urp_telegram_id ON user_research_profiles(telegram_user_id);

-- Seed Darrell's profile
INSERT INTO user_research_profiles
    (telegram_user_id, display_name, expertise_level, domains, communication_style, context_notes, preferred_persona)
VALUES (
    8025375307,
    'Darrell (Flying Squirrel)',
    'specialist',
    ARRAY['linux_admin', 'networking', 'databases', 'hardware', 'security', 'ai_infrastructure', 'distributed_systems'],
    'bullet_points',
    '35+ years sysadmin experience. DOS 3.1 through modern Linux. HP-UX, AIX, OS2 Warp, every Linux flavor. Manages Cherokee AI Federation 6-node cluster with RTX PRO 6000 96GB, NVMe storage, PostgreSQL, vLLM inference. Thinks strategically — questions about technology are usually about OUR infrastructure, not abstract. Skip basics, focus on performance trade-offs, edge cases, and middleware compatibility.',
    'telegram'
);
```

## Step 2: Modify research_personas.py

File: `/ganuda/lib/research_personas.py`

SEARCH:
```python
def build_research_query(question: str, persona_key: str = "default") -> str:
    """
    Build full research query with persona context prepended.

    Args:
        question: The user's research question
        persona_key: The persona to use for context

    Returns:
        Full query string with persona context + question
    """
    persona_prompt = get_persona_prompt(persona_key)
    return f"{persona_prompt}\n\n---\n\nResearch Question: {question}"
```

REPLACE:
```python
def get_user_profile(telegram_user_id: int) -> dict:
    """
    Look up user research profile from database.
    Returns empty dict if no profile found.
    """
    try:
        from lib.secrets_loader import get_db_config
        import psycopg2
        conn = psycopg2.connect(**get_db_config())
        cur = conn.cursor()
        cur.execute("""
            SELECT expertise_level, domains, communication_style,
                   context_notes, preferred_persona, display_name
            FROM user_research_profiles
            WHERE telegram_user_id = %s
        """, (telegram_user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            return {
                'expertise_level': row[0],
                'domains': row[1] or [],
                'communication_style': row[2],
                'context_notes': row[3] or '',
                'preferred_persona': row[4],
                'display_name': row[5] or ''
            }
    except Exception:
        pass
    return {}


def _build_profile_injection(profile: dict) -> str:
    """Build a prompt injection string from a user profile."""
    if not profile:
        return ""

    level = profile.get('expertise_level', 'intermediate')
    style = profile.get('communication_style', 'balanced')
    context = profile.get('context_notes', '')
    domains = profile.get('domains', [])

    parts = ["\n\n--- USER PROFILE (adjust response accordingly) ---"]

    if level == 'specialist':
        parts.append("This user is a SPECIALIST with decades of experience. Skip all introductory material, definitions, and basics. Focus on: performance benchmarks, trade-offs, edge cases, middleware compatibility, and strategic implications for their infrastructure.")
    elif level == 'expert':
        parts.append("This user is an EXPERT. Be concise. Skip basic explanations. Focus on technical depth, trade-offs, and actionable recommendations.")
    elif level == 'novice':
        parts.append("This user is a NOVICE. Be thorough and accessible. Define technical terms. Provide step-by-step guidance. Err on the side of more explanation.")

    if style == 'bullet_points':
        parts.append("Format: Use bullet points and tables. Minimize prose. Be direct.")
    elif style == 'deep_dive':
        parts.append("Format: Provide deep technical analysis with benchmarks and citations.")
    elif style == 'executive_summary':
        parts.append("Format: Lead with a 2-3 sentence executive summary, then supporting details.")

    if domains:
        parts.append(f"Domains of expertise: {', '.join(domains)}")

    if context:
        parts.append(f"Context: {context}")

    parts.append("--- END USER PROFILE ---")
    return "\n".join(parts)


def build_research_query(question: str, persona_key: str = "default", telegram_user_id: int = None) -> str:
    """
    Build full research query with persona context and optional user profile.

    Args:
        question: The user's research question
        persona_key: The persona to use for context
        telegram_user_id: Optional Telegram user ID for profile lookup

    Returns:
        Full query string with persona context + user profile + question
    """
    persona_prompt = get_persona_prompt(persona_key)

    profile_injection = ""
    if telegram_user_id:
        profile = get_user_profile(telegram_user_id)
        if profile:
            profile_injection = _build_profile_injection(profile)
            # Use preferred persona if user has one and no explicit persona was chosen
            if persona_key == "default" and profile.get('preferred_persona'):
                persona_prompt = get_persona_prompt(profile['preferred_persona'])

    return f"{persona_prompt}{profile_injection}\n\n---\n\nResearch Question: {question}"
```

## Step 3: Modify telegram_chief_v3.py

File: `/ganuda/telegram_bot/telegram_chief_v3.py`

Pass the user's Telegram ID into `build_research_query` so profile lookup happens.

SEARCH (around line 370):
```python
        full_query = build_research_query(question, persona)
```

REPLACE:
```python
        full_query = build_research_query(question, persona, telegram_user_id=user.id)
```

## Step 4: Add /profile command to telegram_chief_v3.py

File: `/ganuda/telegram_bot/telegram_chief_v3.py`

Add a new command handler for users to view and set their profile. Insert this function BEFORE the `results_command` function (before line 391):

```python
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /profile command — view or set user research profile"""
    user = update.effective_user

    if not context.args:
        # Show current profile
        try:
            from research_personas import get_user_profile
            profile = get_user_profile(user.id)
            if profile:
                domains = ', '.join(profile.get('domains', []))
                await update.message.reply_text(
                    f"📋 Research Profile for {profile.get('display_name', user.first_name)}\n\n"
                    f"Expertise: {profile.get('expertise_level', 'intermediate')}\n"
                    f"Style: {profile.get('communication_style', 'balanced')}\n"
                    f"Domains: {domains or 'none set'}\n"
                    f"Persona: {profile.get('preferred_persona', 'telegram')}\n\n"
                    f"Context: {profile.get('context_notes', 'none')[:200]}\n\n"
                    f"To update: /profile set <field> <value>\n"
                    f"Fields: expertise, style, persona\n"
                    f"Expertise: novice, intermediate, expert, specialist\n"
                    f"Style: verbose, balanced, bullet_points, deep_dive, executive_summary"
                )
            else:
                await update.message.reply_text(
                    f"No research profile found for {user.first_name}.\n\n"
                    f"Create one: /profile set expertise <level>\n"
                    f"Levels: novice, intermediate, expert, specialist"
                )
        except Exception as e:
            await update.message.reply_text(f"Error loading profile: {e}")
        return

    if len(context.args) >= 3 and context.args[0].lower() == "set":
        field = context.args[1].lower()
        value = " ".join(context.args[2:])

        valid_fields = {
            'expertise': ('expertise_level', ['novice', 'intermediate', 'expert', 'specialist']),
            'style': ('communication_style', ['verbose', 'balanced', 'bullet_points', 'deep_dive', 'executive_summary']),
            'persona': ('preferred_persona', list(PERSONAS.keys())),
        }

        if field not in valid_fields:
            await update.message.reply_text(f"Unknown field: {field}. Valid: {', '.join(valid_fields.keys())}")
            return

        col_name, valid_values = valid_fields[field]
        if value.lower() not in valid_values:
            await update.message.reply_text(f"Invalid value. Options: {', '.join(valid_values)}")
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute(f"""
                INSERT INTO user_research_profiles (telegram_user_id, display_name, {col_name})
                VALUES (%s, %s, %s)
                ON CONFLICT (telegram_user_id) DO UPDATE SET {col_name} = EXCLUDED.{col_name}, updated_at = NOW()
            """, (user.id, user.first_name, value.lower()))
            conn.commit()
            cur.close()
            conn.close()
            await update.message.reply_text(f"✅ Profile updated: {field} = {value}")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
        return

    await update.message.reply_text("Usage: /profile or /profile set <field> <value>")
```

Then register the handler. Find where other handlers are registered (around line 441):

SEARCH:
```python
    app.add_handler(CommandHandler("research", research_command))
```

REPLACE:
```python
    app.add_handler(CommandHandler("research", research_command))
    app.add_handler(CommandHandler("profile", profile_command))
```

## Verification

After deployment, restart the bot:
```
sudo systemctl restart derpatobot.service
```

Test:
1. `/profile` — should show Darrell's pre-seeded profile (specialist, bullet_points)
2. `/research what is the best filesystem for NVMe with large ML models` — should get a concise, technical, bullet-point response focused on performance
3. From a different user (Joe): `/research what is a filesystem` — should get the full beginner-friendly treatment (no profile = default behavior)

## Notes

- The profile lookup adds one DB query per research request (~1ms). Negligible.
- The `build_research_query` change is BACKWARDS COMPATIBLE — `telegram_user_id=None` preserves existing behavior for non-Telegram callers.
- VetAssist is NOT affected — it uses its own persona path.
- Future: SAG integration would call `get_user_profile()` + augment `context_notes` with real-time activity context.
