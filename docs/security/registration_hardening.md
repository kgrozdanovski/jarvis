# Registration Security Hardening

**Status:** Plan / Not yet implemented  
**Last updated:** 2026-04-09  
**Scope:** `/user/auth/register` and adjacent endpoints (`/auth/lookup`, `/auth/send-verification`)

---

## Current Baseline

What is already in place and does not need to be changed:

| Control | Implementation |
|---------|---------------|
| Password hashing | bcrypt, configurable rounds (default 12) — `backend/src/core/security.py:72` |
| Email format validation | Pydantic `EmailStr` on `RegisterRequest` — `backend/src/model/router.py:37` |
| Email uniqueness | DB lookup before insert — `backend/src/routers/users.py:164` |
| Email verification tokens | 48-byte `secrets.token_urlsafe()`, stored as SHA-256 hash, 24 h TTL — `backend/src/core/security.py:97` |
| Single active token per user | Partial unique DB index on `user_tokens` — `backend/migrations/` |
| Constant-time comparison | `hmac.compare_digest` — `backend/src/core/security.py:127` |
| Global registration caps | Daily/monthly limits via `ensure_system_capacity` — `backend/src/service/system_limits.py:120` |
| Verified-account gate at login | Unverified accounts cannot log in — `backend/src/routers/users.py:86` |

---

## Hardening Checklist

### 1. Email Domain Blacklist

**Problem:** Any syntactically valid email domain is currently accepted, including disposable/temporary providers (Mailinator, Guerrilla Mail, 10-Minute Mail, Temp Mail, etc.). These are commonly used for spam registrations, trial abuse, and throwaway accounts that circumvent bans.

**What to do:**

Maintain a static blocklist of known disposable email domains and reject registrations that use them. The community-maintained list at `https://github.com/disposable-email-domains/disposable-email-domains` (raw file: `disposable_email_blocklist.conf`) contains ~4,000 domains and is updated regularly.

**Implementation approach:**

1. Add a `BLOCKED_EMAIL_DOMAINS` set loaded at startup from a bundled text file (one domain per line) placed at `backend/src/data/blocked_email_domains.txt`.
2. Add a Pydantic `field_validator` on `RegisterRequest.email` that extracts the domain part and checks it against the set.
3. Return HTTP 400 with a user-facing message (`"Email domain not allowed."`) on a match.
4. Allow overriding the blocklist path via env var `BLOCKED_EMAIL_DOMAINS_PATH` so the file can be updated in production without a code deploy.

**Code locations to modify:**
- `backend/src/model/router.py` — add `@field_validator("email")` to `RegisterRequest`
- `backend/src/data/blocked_email_domains.txt` — new file (bundled list)

**Do not:**
- Reject based on MX record lookups at registration time (adds latency, can cause false positives under DNS failures)
- Hardcode the list inline in Python (hard to update)

---

### 2. Per-IP Rate Limiting on Registration

**Problem:** The `/user/auth/register` endpoint has no per-source rate limiting. The only throttle is a global daily/monthly registration cap (`SYSTEM_LIMIT_USER_REG_DAILY/MONTHLY`), which defaults to unlimited (0). An attacker can create thousands of accounts from a single IP in a short window.

The identical mechanism used for `/contact` and `/newsletter/subscribe` exists in `backend/src/routers/default.py:32-53` and is not wired up for registration.

**What to do:**

Instantiate a separate set of `InMemoryRateLimiter` instances scoped to registration and apply them inside the `register()` handler, mirroring the pattern in `default.py`.

**Suggested limits (configurable via env):**

| Limiter | Limit | Window | Env var |
|---------|-------|--------|---------|
| Per-IP | 5 registrations | 1 hour | `REG_RATE_LIMIT_IP` |
| Global | 200 registrations | 1 hour | `REG_RATE_LIMIT_GLOBAL` |

Return HTTP 429 on breach. Do not reveal which limit was hit.

**Code locations to modify:**
- `backend/src/routers/users.py` — add limiter instances at module level, apply checks at the top of `register()`
- IP extraction: reuse `_extract_client_meta()` from `default.py` or move it to a shared utility

**Note on in-memory limiters:** The existing `InMemoryRateLimiter` is process-local. If multiple backend workers/processes are running, each has its own counter. This is acceptable for a basic defence layer. For strict enforcement across processes, replace with a Redis-backed counter (e.g., via `redis-py` with a sliding window using `ZADD`/`ZREMRANGEBYSCORE`).

---

### 3. Password Strength Enforcement

**Problem:** `RegisterRequest.password` is validated only for presence. The string `"a"` is a valid password. bcrypt correctly hashes whatever is given, so weak passwords are silently accepted and stored.

**What to do:**

Add a `@field_validator("password")` on `RegisterRequest` that enforces:

1. **Minimum length:** 10 characters. (NIST SP 800-63B recommends at least 8; 10 is a reasonable production default.)
2. **Maximum length:** 128 characters. bcrypt silently truncates inputs at 72 bytes; enforce an explicit max to make this behaviour visible and prevent DoS via enormous bcrypt inputs.
3. **No leading/trailing whitespace:** Strip and reject if the stripped length differs (avoids user confusion at login).
4. **Character variety (optional, NIST-discouraged for mandatory rules):** If desired, require at least one non-alphabetic character. Keep this off by default — NIST now recommends against mandatory complexity rules in favour of length.

**Optional — HIBP breach check:**

Check the password against the [Have I Been Pwned Passwords API](https://haveibeenpwned.com/API/v3#PwnedPasswords) using k-anonymity (only the first 5 hex chars of the SHA-1 hash are sent). If the password appears in a known breach, reject with a clear message prompting the user to choose a different one. This adds an async HTTP call; run it as part of the `register()` handler, not as a validator, so it can be skipped under failure gracefully.

**Code locations to modify:**
- `backend/src/model/router.py` — add `@field_validator("password")` to `RegisterRequest`
- `backend/src/routers/users.py` — optionally add HIBP check inside `register()` before `create_user()`

---

### 4. Honeypot Field on Registration

**Problem:** The `/contact` and `/newsletter/subscribe` endpoints both use a honeypot field (`website`, aliased to `honeypot` in the model) that is hidden from real users via CSS. Simple bots that fill all visible fields will populate it and get rejected with HTTP 400. This defence is absent from the registration endpoint.

**What to do:**

Add the same pattern to `RegisterRequest`:

1. Add a field `honeypot: Optional[str] = Field(default=None, alias="website")` to `RegisterRequest` in `backend/src/model/router.py`.
2. At the top of `register()` in `backend/src/routers/users.py`, check `if request.honeypot: raise HTTPException(status_code=400, detail="Bad request.")`.
3. On the frontend, ensure the `website` field is present in the DOM but hidden via CSS (`display: none` or `visibility: hidden`) and never auto-filled by the frontend code.

**Code locations to modify:**
- `backend/src/model/router.py` — add `honeypot` field to `RegisterRequest`
- `backend/src/routers/users.py` — add honeypot check at the start of `register()`
- Frontend registration form — add hidden `website` input

**Note:** This is a low-friction, zero-latency first filter. It does not stop sophisticated bots that parse the DOM and skip hidden fields, but it eliminates a large class of naive bots with no user-facing cost.

---

### 5. `/auth/lookup` Endpoint Hardening

**Problem:** The `POST /user/auth/lookup` endpoint (`backend/src/routers/users.py:35`) accepts an email and returns `{ exists: true/false, is_verified: true/false, status: "verified"|"unverified" }`. This is a public, unauthenticated, unthrottled account enumeration oracle. An attacker can enumerate whether any email address has an account, and whether it is verified, with no rate limiting.

**What to do:**

Choose one of these approaches based on whether the lookup is needed for UX (e.g., to show "sign in instead" on the registration page):

**Option A — Remove the endpoint (preferred if UX can be restructured):**  
Inline the "does this email exist?" check into the registration flow itself. The registration endpoint already returns HTTP 400 with `"Already exists."` — the frontend can react to that response code instead of pre-checking.

**Option B — Rate-limit aggressively:**  
Apply per-IP rate limiting tighter than registration: e.g., 10 lookups per IP per hour. Use the same `InMemoryRateLimiter` pattern. Return HTTP 429 on breach.

**Option C — Require a signed token (most secure):**  
Issue a short-lived signed challenge token from the frontend load (e.g., embedded in the page or fetched from a `/challenge` endpoint that itself is rate-limited) and require it on the lookup call. This prevents automated enumeration without browser-level interaction.

**Regardless of which option is chosen, add per-IP rate limiting at minimum.** The current state (no limiting, full enumeration detail) is the most permissive possible configuration.

**Code locations to modify:**
- `backend/src/routers/users.py:35` — `email_exists()` handler

---

### 6. Registration Audit Logging

**Problem:** No metadata is captured at registration time. The contact submission flow logs IP address, user agent, page URL, and timestamp (`backend/src/routers/default.py:203-214`), which is useful for fraud investigation. Registration captures none of this.

**What to do:**

At the end of a successful `register()` call, log the following to a structured log (Sentry breadcrumb + Python logger):

- IP address (from `x-forwarded-for` / `X-Real-IP` / `request.client.host`)
- User agent string
- Timestamp (already implicit in the log entry)
- Registration source (referrer header, or `request.next` if present)
- Plan key if provided (`request.plan_key`)

For deeper forensics, consider inserting a row into an `audit_log` table (or reusing `user_audit` if schema allows) with these fields, linked to the new user's ID.

**Code locations to modify:**
- `backend/src/routers/users.py:155` — add `request: Request` parameter to `register()`, extract and log metadata after successful `create_user()`

**Note:** Do not log passwords, tokens, or any credential material. Log only metadata.

---

### 7. Name Field Validation

**Problem:** The `name` field on `RegisterRequest` accepts any string with no minimum length and no maximum enforced at the model layer. The service silently truncates names longer than 180 characters (`backend/src/service/user.py:71`) without raising a validation error — the caller receives no feedback. A zero-character name passes the model validator and only fails the `if not request.name` check in the handler.

**What to do:**

Replace the bare `name: str` field with:

```python
name: str = Field(min_length=2, max_length=100, strip_whitespace=True)
```

- `min_length=2` — rejects single-character names and empty strings at the model layer with a clear Pydantic validation error.
- `max_length=100` — enforces the limit at the boundary rather than silently truncating in the service. 100 characters covers all realistic names while preventing abuse.
- `strip_whitespace=True` — normalises whitespace before validation so `"  A  "` (length 5) is treated as `"A"` (length 1) and rejected.

**Code locations to modify:**
- `backend/src/model/router.py:36` — update `name` field on `RegisterRequest`

---

### 8. CAPTCHA / Bot Challenge

**Problem:** There is no challenge mechanism on registration. Automated bots can submit the registration form programmatically at high volume without any human-interaction proof. The honeypot field (item 4) filters naive bots; this item addresses sophisticated ones.

**What to do:**

Integrate [Cloudflare Turnstile](https://developers.cloudflare.com/turnstile/) (preferred) or hCaptcha. Both offer an invisible mode that challenges only suspicious traffic, imposing no friction on legitimate users.

**Flow:**

1. Frontend renders the Turnstile widget on the registration page (one `<script>` tag + a `<div>` with the site key).
2. On form submission, Turnstile provides a short-lived `cf-turnstile-response` token.
3. Frontend includes this token in the registration request body.
4. Backend calls the Turnstile siteverify API (`https://challenges.cloudflare.com/turnstile/v0/siteverify`) with the token and the server-side secret key.
5. If verification fails or the token is missing, return HTTP 400.

**Model change:** Add `captcha_token: Optional[str] = None` to `RegisterRequest`.

**Backend verification:** Add a `verify_turnstile_token(token: str) -> bool` helper in `backend/src/core/` that calls the siteverify endpoint. This is an async HTTP call; run it before `create_user()`.

**Env vars needed:**
- `TURNSTILE_SECRET_KEY` — server-side secret from Cloudflare dashboard
- `CAPTCHA_ENABLED=true` — feature flag to disable in local dev/test

**Note:** Skip CAPTCHA verification when `CAPTCHA_ENABLED` is false. Never skip it in production.

---

### 9. Email Verification TTL Reduction

**Problem:** Verification tokens are valid for 24 hours (`EMAIL_VERIFICATION_TTL_HOURS=24`, `backend/src/core/security.py:26`). This is a generous window. If a verification email is intercepted or the token URL is cached by a link-preview bot, the token remains exploitable for a full day.

**What to do:**

Reduce `EMAIL_VERIFICATION_TTL_HOURS` to 4 hours. The resend flow (`/auth/send-verification`) with its 45-second cooldown allows users who miss the window to easily request a new token.

**Also consider:**

- Marking tokens as single-use immediately on first click, before completing verification server-side (already done via `used_at` — confirm this is set atomically).
- Logging when a token is used, to detect replay attempts against the same token hash.

**Config to change:**
- `EMAIL_VERIFICATION_TTL_HOURS` env var (change default in `backend/src/core/security.py:26` from `"24"` to `"4"`)

---

### 10. Unverified Account Cleanup

**Problem:** Every registration creates a user row in the `users` table, regardless of whether the email is ever verified. Unverified accounts accumulate indefinitely. This inflates user counts, wastes storage, and means that if a legitimate user's email is used by an attacker to register first, the legitimate user can never register (uniqueness constraint blocks them) even after the attacker abandons the account.

**What to do:**

Add a scheduled cleanup job that deletes users where:
- `is_verified = false`
- `created_at < NOW() - INTERVAL '7 days'`

Before deletion, ensure any associated `user_tokens` rows are also cleaned up (cascade delete or explicit delete in the same transaction).

**Implementation options:**

1. **Database cron job (pg_cron):** Add a recurring SQL job directly in Postgres. Simple, no application code needed.
2. **Application-level script:** Add a Python script in `backend/scripts/` that runs the cleanup query and is invoked by a system cron or a scheduler (e.g., GitHub Actions scheduled workflow, or a simple cron on the server).

**Suggested SQL:**

```sql
DELETE FROM users
WHERE is_verified = false
  AND created_at < NOW() - INTERVAL '7 days';
```

Ensure `user_tokens` has an `ON DELETE CASCADE` foreign key referencing `users.id`, or add an explicit delete before the user delete.

**Note on the enumeration side-effect:** After cleanup runs, a previously-registered-but-never-verified email becomes available again. This is the desired behaviour — it unblocks legitimate users — but be aware it also means a cleaned-up attacker could re-register with the same address.

---

## Priority Summary

| # | Item | Risk reduced | Effort |
|---|------|-------------|--------|
| 2 | Per-IP rate limiting on registration | Account farming, credential stuffing setup | Low |
| 1 | Email domain blacklist | Trial abuse, disposable accounts | Low |
| 3 | Password strength enforcement | Weak credential storage | Low |
| 4 | Honeypot field on registration | Naive bot registrations | Low |
| 7 | Name field validation | Input abuse, silent truncation bugs | Low |
| 6 | Registration audit logging | Forensic blind spot | Low |
| 5 | `/auth/lookup` hardening | Account enumeration | Low–Medium |
| 9 | Verification token TTL reduction | Token interception window | Low (config only) |
| 10 | Unverified account cleanup | Resource exhaustion, email squatting | Medium |
| 8 | CAPTCHA integration | Sophisticated bot registrations | Medium |
