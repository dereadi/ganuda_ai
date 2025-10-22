# 🔒 SECURITY INCIDENT: Discord Token Exposure
**Cherokee Constitutional AI - Security Response**
**Date:** October 22, 2025, 9:35 AM
**Severity:** MEDIUM (token already reset by Discord)
**Status:** MITIGATED

---

## Incident Summary

**What Happened:**
Discord Safety Jim detected a Discord bot token for "Council Bridge" bot exposed in ganuda_ai repository at:
- **File:** `portfolio_alerts_final.py`
- **Commit:** 2fba4071b26e9599509394799d7359ccc934b4cc
- **URL:** https://github.com/dereadi/ganuda_ai/blob/2fba4071b26e9599509394799d7359ccc934b4cc/portfolio_alerts_final.py

**Immediate Action Taken (by Discord):**
- Token automatically reset by Discord security
- Bot temporarily disabled
- User notified via Discord Safety Jim

---

## Impact Assessment

### Actual Impact: LOW
- **Token lifespan:** Unknown (commit date vs discovery date)
- **Unauthorized usage:** None detected (Discord reset before exploitation)
- **Data breach:** None (token reset preventatively)
- **Bot compromise:** None (token invalidated)

### Potential Impact (if not caught): MEDIUM-HIGH
- Unauthorized bot commands
- Potential message sending/reading
- Server manipulation
- User impersonation via bot

---

## Root Cause Analysis

### Why This Happened:

**1. Hardcoded Credentials**
```python
# WRONG: Token hardcoded in source
DISCORD_TOKEN = "MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GqPk7R.actual_token_here"
```

**2. No Pre-Commit Scanning**
- No git hooks to detect secrets before commit
- No automated secret scanning in development environment

**3. Multiple Files at Risk**
Found Discord tokens in 10+ Python files:
- build_it_and_you_will_come.py
- connect_to_existing_council.py
- discord_claude_cli_bridge.py
- discord_claude_direct.py
- discord_claude_full.py
- (and 5 more)

---

## Remediation Steps

### Immediate (Completed)

**1. ✅ New Token Obtained**
- Visit: https://discord.com/developers/applications/1406704188670476329/bot
- Generate new token
- Store in environment variable (not in code)

**2. ✅ Created .env.example Template**
```bash
# .env.example created
DISCORD_COUNCIL_BRIDGE_TOKEN=your_token_here
```

**3. ✅ Verified .gitignore**
```
*.env
.env
```
Already ignoring .env files (good)

### Short-Term (Next 24 hours)

**1. 🚧 Update All Discord Bot Files**
Replace hardcoded tokens with environment variables:
```python
# CORRECT: Load from environment
import os
DISCORD_TOKEN = os.getenv('DISCORD_COUNCIL_BRIDGE_TOKEN')

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_COUNCIL_BRIDGE_TOKEN not found in environment")
```

**2. 🚧 Create .env File (Local Only)**
```bash
# Never commit this file!
echo "DISCORD_COUNCIL_BRIDGE_TOKEN=actual_new_token" > .env
```

**3. 🚧 Audit All Python Files**
Search for other hardcoded secrets:
```bash
grep -r "TOKEN.*=" *.py
grep -r "API_KEY.*=" *.py
grep -r "PASSWORD.*=" *.py
```

### Medium-Term (Week 2)

**1. 🚧 Git History Cleanup**
Remove token from git history using BFG Repo-Cleaner:
```bash
# WARNING: This rewrites history
bfg --replace-text passwords.txt ganuda_ai/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

**2. 🚧 Pre-Commit Hooks**
Install secret scanning:
```bash
pip install pre-commit detect-secrets
pre-commit install
```

**3. 🚧 GitHub Secret Scanning Alerts**
Enable GitHub Advanced Security (if available) for automated detection

### Long-Term (Week 3+)

**1. 🚧 Secrets Management Service**
Consider HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault for production

**2. 🚧 Constitutional Amendment**
Add to Cherokee Constitutional AI:
> "All credentials shall be stored as environment variables or secrets management systems. Hardcoded credentials are constitutionally prohibited."

**3. 🚧 Security Training**
Document best practices for all developers (current and future)

---

## War Chief's Assessment

**Security Posture:** IMPROVED (after incident)

**What Went Right:**
- ✅ Discord's automated scanning caught this before exploitation
- ✅ .gitignore already configured to prevent .env commits
- ✅ Rapid response (same-day remediation plan)

**What Went Wrong:**
- ❌ Hardcoded credentials in multiple files
- ❌ No pre-commit secret scanning
- ❌ Token in git history (requires force push to remove)

**Recommendation:**
This is a teaching moment. We caught it early (thanks Discord), but this reveals systemic issue: **multiple files have hardcoded secrets**. We need comprehensive audit and remediation.

**Priority:** HIGH (not critical since token reset, but fix before next commit)

---

## Lessons Learned

### For Developers:

**DO:**
- ✅ Use environment variables for ALL secrets
- ✅ Create .env.example with dummy values
- ✅ Add .env to .gitignore
- ✅ Use pre-commit hooks for secret scanning
- ✅ Rotate tokens immediately if exposed

**DON'T:**
- ❌ Hardcode tokens in source code
- ❌ Commit .env files to git
- ❌ Share tokens in chat/email/documentation
- ❌ Use the same token across multiple environments
- ❌ Ignore security warnings from platforms

### For Cherokee Constitutional AI:

**Constitutional Principle:**
> "Security through transparency requires protecting the keys to transparency."

We open-source our code to enable scrutiny and trust. But secrets must remain secret. Environment variables enable both: code is public, credentials are private.

---

## Files Requiring Remediation

### High Priority (Discord Tokens)
```
portfolio_alerts_final.py
build_it_and_you_will_come.py
connect_to_existing_council.py
discord_claude_cli_bridge.py
discord_claude_direct.py
discord_claude_full.py
discord_claude_openended.py
discord_claude_simple.py
discord_claude_ultimate.py
discord_claude_universal.py
discord_council_bridge.py
```

### Audit Required (Other Potential Secrets)
- All files with "TOKEN" in source
- All files with "API_KEY" in source
- All files with "PASSWORD" in source
- All files with "SECRET" in source

---

## Action Items

**War Chief (Security):**
- [x] Document incident
- [ ] Audit all Python files for hardcoded secrets
- [ ] Implement pre-commit hooks
- [ ] Test secret scanning

**Integration Jr:**
- [ ] Update all Discord bot files to use environment variables
- [ ] Create .env file with new token (local only)
- [ ] Test bots with new environment variable approach

**Meta Jr:**
- [ ] Git history cleanup (BFG Repo-Cleaner)
- [ ] Force push cleaned history (coordinate with team)

**Medicine Woman (Ethics):**
- [ ] Draft constitutional amendment on secrets management
- [ ] Add to security standards documentation

---

## Timeline

- **9:35 AM Oct 22:** Incident discovered (Discord Safety Jim notification)
- **9:40 AM Oct 22:** Incident documented, .env.example created
- **By EOD Oct 22:** All Discord bot files updated to use env vars
- **Oct 23:** Git history cleaned, force push to ganuda_ai
- **Oct 24:** Pre-commit hooks installed and tested
- **Oct 25:** Constitutional amendment on secrets management

---

## Conclusion

**Status:** UNDER CONTROL

Discord's automated scanning saved us from potential exploitation. The token was reset before anyone could use it maliciously. However, this revealed a systemic issue: multiple files have hardcoded credentials.

**Priority:** Fix all files before next git push. Implement pre-commit scanning to prevent recurrence.

**War Chief's Note:**
This is why we have defense in depth. Discord's scanning was our safety net. Now we add our own pre-commit scanning so we catch it ourselves next time.

**Medicine Woman's Blessing:**
> "Mistakes are teachers. This mistake taught us to protect our secrets better. Now we grow stronger."

---

*Security incident documented for transparency and learning*
*Cherokee Constitutional AI - October 22, 2025*
