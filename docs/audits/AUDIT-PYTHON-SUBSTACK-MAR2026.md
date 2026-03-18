# Security Audit: python-substack (ma2za/python-substack)

**Date**: 2026-03-17
**Auditor**: TPM (Claude Opus 4.6)
**Repository**: https://github.com/ma2za/python-substack
**Version Audited**: 0.1.18 (commit 3a3bfdf)
**Verdict**: CLEARED WITH CONDITIONS

---

## Executive Summary

The python-substack library is a lightweight Python wrapper around the Substack API. It consists of 3 core Python files (~640 lines of library code) with a single runtime dependency (`requests`). The library is **free of malicious code, telemetry, phone-home behavior, and code injection vectors**. All HTTP calls target `*.substack.com` exclusively via HTTPS. However, it has design-level credential handling weaknesses that require operational controls when deployed.

---

## 1. Credential Flow Analysis

### Entry Points
- **Email/Password**: Passed as constructor args to `Api(email=, password=)` (api.py:30-81)
- **Cookies file**: JSON file path via `cookies_path=` (api.py:71-74)
- **Cookies string**: Semicolon-separated cookie string via `cookies_string=` (api.py:76-78)

### In-Memory Storage
- Email and password are **not stored** as instance attributes. They are passed directly to `self.login()` and then discarded. **GOOD.**
- Session cookies are held in `self._session.cookies` (a `requests.Session` CookieJar) for the lifetime of the `Api` object.

### Disk Persistence
- `export_cookies()` (api.py:180-188) writes session cookies to a plaintext JSON file at a user-specified path. Default: `cookies.json`.
- **FINDING [MEDIUM]**: Cookie file is written with no restricted permissions (no `os.chmod(path, 0o600)`). On multi-user systems, session cookies could be readable by other users.

### Transmission
- Login sends email+password as JSON POST body to `https://substack.com/api/v1/login` (api.py:145-154).
- All subsequent requests use session cookies (no password re-transmission).
- **All URLs are HTTPS**. No HTTP fallback exists anywhere in the codebase. **GOOD.**

### Password in Login Payload
- The login JSON body includes `email` and `password` in plaintext over HTTPS (api.py:147-153). This is standard for Substack's own login flow. The password is **not** logged, hashed client-side, or stored after the call returns.

---

## 2. Network Call Inventory

Every HTTP call in the library is made through `self._session` (a `requests.Session`). All base URLs default to `https://substack.com/api/v1` or `https://<subdomain>.substack.com/api/v1`.

| File | Line(s) | Method | URL Pattern | Purpose | Credential Sent? |
|------|---------|--------|-------------|---------|-----------------|
| api.py | 145-154 | POST | `{base_url}/login` | Authenticate with email/password | YES (email+password in body) |
| api.py | 162-164 | GET | `https://substack.com/sign-in?redirect=...&for_pub=...` | Sign into specific publication | YES (session cookies) |
| api.py | 300 | GET | `{base_url}/user/profile/self` | Get user profile | YES (session cookies) |
| api.py | 311 | GET | `{base_url}/settings` | Get user settings | YES (session cookies) |
| api.py | 322 | GET | `{publication_url}/publication/users` | List publication users | YES (session cookies) |
| api.py | 334-335 | GET | `{publication_url}/publication_launch_checklist` | Get subscriber count | YES (session cookies) |
| api.py | 346-353 | GET | `{publication_url}/post_management/published` | List published posts | YES (session cookies) |
| api.py | 364 | GET | `{base_url}/reader/posts` | Get posts | YES (session cookies) |
| api.py | 379-381 | GET | `{publication_url}/drafts` | List drafts | YES (session cookies) |
| api.py | 390 | GET | `{publication_url}/drafts/{id}` | Get single draft | YES (session cookies) |
| api.py | 402 | DELETE | `{publication_url}/drafts/{id}` | Delete draft | YES (session cookies) |
| api.py | 414 | POST | `{publication_url}/drafts` | Create draft | YES (session cookies) |
| api.py | 427-429 | PUT | `{publication_url}/drafts/{id}` | Update draft | YES (session cookies) |
| api.py | 443-444 | GET | `{publication_url}/drafts/{id}/prepublish` | Pre-publish check | YES (session cookies) |
| api.py | 461-464 | POST | `{publication_url}/drafts/{id}/publish` | Publish draft | YES (session cookies) |
| api.py | 477-479 | POST | `{publication_url}/drafts/{id}/schedule` | Schedule draft | YES (session cookies) |
| api.py | 492-493 | POST | `{publication_url}/drafts/{id}/schedule` | Unschedule draft | YES (session cookies) |
| api.py | 512-514 | POST | `{publication_url}/image` | Upload image | YES (session cookies) |
| api.py | 526 | GET | `{base_url}/categories` | List categories | YES (session cookies) |
| api.py | 540-542 | GET | `{base_url}/category/public/{id}/{type}` | Get category | YES (session cookies) |
| api.py | 601-602 | GET | `{publication_url}/subscriptions` | Get sections | YES (session cookies) |
| api.py | 634-637 | ANY | `{publication_url}/{endpoint}` | Generic API call | YES (session cookies) |

### Telemetry / Phone-Home Check
- **NONE FOUND.** Zero calls to any analytics service, tracking pixel, or non-Substack host. **GOOD.**

### Third-Party Host Contact
- The library contacts ONLY `*.substack.com`. No other domains. **GOOD.**

---

## 3. Code Injection Vector Analysis

| Vector | Found? | Details |
|--------|--------|---------|
| `eval()` | NO | Not present anywhere |
| `exec()` | NO | Not present anywhere |
| `pickle` | NO | Not imported or used |
| `yaml.load()` (unsafe) | NO | Only `yaml.safe_load()` used (examples/publish_post.py:34) |
| `subprocess` | NO | Not imported or used |
| `os.system()` | NO | Not used |
| `__import__()` | NO | Not used |
| `compile()` | NO | Not used |
| Deserialization of untrusted data | NO | `json.load()` used only for local cookie files (user-controlled) |

**VERDICT: Clean.** No code injection vectors found.

---

## 4. Dependency Inventory

| Package | Locked Version | Known CVEs (as of Mar 2026) | Status |
|---------|---------------|---------------------------|--------|
| requests | 2.32.5 | None known | OK |
| python-dotenv | 0.21.1 | None known | OK |
| PyYAML | 6.0.3 | None known (safe_load used in examples) | OK |
| certifi | 2025.11.12 | None known | OK |
| charset-normalizer | 3.4.4 | None known | OK |
| idna | 3.11 | None known | OK |
| urllib3 | 2.6.3 | None known | OK |

**Note**: `pip-audit` was not available on this system. Versions were manually checked against the locked poetry.lock. All dependencies are at recent versions. PyYAML is listed as a direct dependency in pyproject.toml but is only used in the example scripts (not the library core).

---

## 5. Findings

### MEDIUM: Arbitrary Base URL Allows Credential Redirection (api.py:61)

The `base_url` parameter defaults to `https://substack.com/api/v1` but can be overridden to ANY URL. If a caller passes a malicious `base_url`, email/password would be sent to an attacker-controlled server. Similarly, `publication_url` is derived from API responses but the `call()` method (api.py:623-639) constructs URLs from `self.publication_url` which originates from Substack API data — this is safe in normal use.

**Risk**: If our code allows user-controlled input to flow into `base_url`, credentials leak. In our use case (hardcoded or env-var controlled), this is a non-issue.

**Mitigation**: Never pass untrusted input as `base_url`. Always hardcode or use a validated env var.

### MEDIUM: Cookie Export Has No File Permission Restriction (api.py:180-188)

`export_cookies()` writes session cookies to a JSON file using default `open()` permissions (typically 0o644). On multi-user systems, this makes session tokens readable by other users.

**Mitigation**: If we use cookie export, wrap it with `os.chmod(path, 0o600)` after writing, or set umask before calling.

### LOW: Password Held in Caller Scope After Login (api.py:80-81)

While the library itself does not store the password, the caller's variables (`os.getenv("PASSWORD")`) remain in memory. This is standard Python behavior and not a library defect.

### LOW: Debug Mode Enables Global Logging (api.py:63-65)

Passing `debug=True` sets the root logger to DEBUG level. This could cause other libraries to emit sensitive data to logs. The library itself does not log credentials, but `requests` at DEBUG level logs full HTTP headers (including cookies).

**Mitigation**: Do not use `debug=True` in production.

### LOW: Generic `call()` Method Allows Arbitrary Endpoint Construction (api.py:623-639)

The `call()` method takes an arbitrary `endpoint` string and `method`, constructing a URL as `{publication_url}/{endpoint}`. While this is a convenience method, it could be misused if endpoint values come from untrusted input.

**Mitigation**: Never pass untrusted input to `call()`.

### INFO: PyYAML Listed as Dependency But Unused in Library Core

PyYAML is declared in pyproject.toml dependencies but is only imported in `examples/publish_post.py`. The library itself (`substack/`) never imports or uses YAML. This is unnecessary dependency bloat but not a security risk (and `safe_load` is used correctly in the example).

---

## 6. Conditions for Use

This library is **CLEARED WITH CONDITIONS** for use in the Stoneclad federation under the following terms:

1. **NEVER pass untrusted input as `base_url`**. Hardcode `https://substack.com/api/v1` or omit to use the default.
2. **Use cookie-based auth** (`cookies_path` or `cookies_string`) instead of email/password where possible, to minimize credential exposure.
3. **If using `export_cookies()`**, chmod the output file to 0o600 immediately after writing.
4. **Do NOT enable `debug=True`** in production or any environment where logs are persisted/forwarded. Session cookies will appear in debug-level request logs.
5. **Pin the version** to 0.1.18 (commit 3a3bfdf). Review any future updates before upgrading.
6. **Store credentials in environment variables** (via python-dotenv), never in source code. The examples already follow this pattern.

---

## 7. Summary

| Category | Result |
|----------|--------|
| Malicious code | NONE |
| Telemetry / phone-home | NONE |
| Code injection vectors | NONE |
| All traffic HTTPS | YES |
| All traffic to *.substack.com | YES |
| Dependencies up-to-date | YES |
| Known CVEs in deps | NONE |
| Credential handling | ACCEPTABLE with conditions |

**Final Verdict: CLEARED WITH CONDITIONS**
