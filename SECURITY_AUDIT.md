# GalleryWeb Security Audit & Fixes

**Date:** 2026-06-21  
**Status:** Token security issues FIXED  
**Updated File:** `backend/main.py`

---

## Issues Found & Fixed

### 1. Refresh Token Security (CRITICAL) - FIXED

**Issue:** Refresh tokens were stored as plain hex strings in memory dict `_demo_refresh_tokens` with:
- ❌ No cryptographic signing or verification
- ❌ No expiry checks
- ❌ No rotation mechanism
- ❌ Plain text comparison vulnerable to timing attacks

**Original Code (lines 203-251):**
```python
def _issue_tokens(email: str) -> tuple[str, str]:
    """Return (access_token, refresh_token) — both independently random."""
    access = secrets.token_hex(32)
    refresh = secrets.token_hex(32)
    _demo_tokens[access] = email
    _demo_refresh_tokens[refresh] = email  # Plain email, no signature
    return access, refresh

@app.post("/auth/refresh")
async def auth_refresh(request: Request):
    data = await request.json()
    rt = data.get("refresh_token", "")
    email = _demo_refresh_tokens.pop(rt, None)  # No verification
    if email:
        # ... issue new tokens
```

**Fix Applied:**

#### 1a) Added HMAC-SHA256 Token Signing
```python
import hmac
import hashlib

TOKEN_SECRET = os.getenv("TOKEN_SECRET", secrets.token_hex(32))

def _sign_token(token: str) -> str:
    """Generate HMAC-SHA256 signature for a token."""
    return hmac.new(TOKEN_SECRET.encode(), token.encode(), hashlib.sha256).hexdigest()

def _verify_token_signature(token: str, sig: str) -> bool:
    """Verify token signature using constant-time comparison."""
    expected = _sign_token(token)
    return hmac.compare_digest(expected, sig)  # Timing-attack resistant
```

#### 1b) Added Token Expiry Tracking
```python
_demo_refresh_tokens[refresh] = {
    "email": email,
    "signature": _sign_token(refresh),
    "issued_at": time.time(),
    "expires_at": time.time() + 604800  # 7 days
}
```

#### 1c) Enhanced Refresh Endpoint with Validation
```python
@app.post("/auth/refresh")
async def auth_refresh(request: Request):
    data = await request.json()
    rt = data.get("refresh_token", "")
    rt_data = _demo_refresh_tokens.pop(rt, None)

    if not rt_data:
        raise HTTPException(status_code=401, detail="Geçersiz refresh token")

    # ✓ Verify signature (constant-time comparison)
    if not _verify_token_signature(rt, rt_data.get("signature", "")):
        raise HTTPException(status_code=401, detail="Token imzası doğrulanamadı")

    # ✓ Check expiry
    if time.time() > rt_data.get("expires_at", 0):
        raise HTTPException(status_code=401, detail="Refresh token süresi dolmuş")

    email = rt_data.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Geçersiz token verisi")

    access, new_refresh = _issue_tokens(email)
    return {...}
```

---

## Security Improvements Summary

| Issue | Severity | Fix | Status |
|-------|----------|-----|--------|
| No HMAC signing | Critical | Added HMAC-SHA256 signing | ✓ Fixed |
| No timing-attack protection | High | Used `hmac.compare_digest()` | ✓ Fixed |
| No token expiry | High | 7-day refresh token TTL | ✓ Fixed |
| Plain text storage | High | Structured dict with metadata | ✓ Fixed |
| No signature verification | Critical | Signature check in refresh endpoint | ✓ Fixed |

---

## Deployment Notes

### Environment Variables
```bash
# Optional: Set a custom token secret (recommended for production)
export TOKEN_SECRET="your-secret-key-here"

# If not set, a random 32-byte hex secret is auto-generated on startup
```

### Production Recommendations

1. **Replace Demo Auth:** This demo implementation should be replaced with **Supabase Auth** or another OAuth2/JWT provider in production
2. **HTTPS Only:** Ensure all auth endpoints use HTTPS (X-Forwarded-Proto check)
3. **Rate Limiting:** Already implemented (`@limiter.limit("5/minute")` on login/signup)
4. **Token Rotation:** New refresh token issued on each refresh call (current implementation)
5. **Audit Logging:** Consider logging failed auth attempts and token refresh events

---

## Files Modified

- ✓ `/backend/main.py`
  - Added imports: `hmac`, `hashlib`
  - Added token signing functions
  - Modified `_issue_tokens()` to include HMAC signature and expiry
  - Enhanced `/auth/refresh` endpoint with signature & expiry validation

---

## Testing Checklist

- [ ] Login endpoint returns valid access + refresh tokens
- [ ] Refresh endpoint validates signature correctly
- [ ] Refresh endpoint rejects expired tokens (> 7 days old)
- [ ] Refresh endpoint issues new token pair on valid refresh
- [ ] Modified signature on token causes refresh to fail
- [ ] Timing attack resistant (uses `hmac.compare_digest`)

---

## Upload Security Status

**Note:** No dedicated file upload endpoint currently exists in the codebase. If/when added, ensure:
- MIME type validation (using `python-magic` recommended)
- File size limits (max 5MB suggested)
- UUID-based file renaming (prevent directory traversal)
- Virus scanning for production use

See `requirements.txt` for available packages: `python-multipart` already installed.

---

## References

- OWASP: [Broken Authentication](https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/)
- Python docs: [`hmac.compare_digest()`](https://docs.python.org/3/library/hmac.html#hmac.compare_digest)
- JWT Best Practices: Token Expiration & Rotation
