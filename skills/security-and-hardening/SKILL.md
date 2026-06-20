---
name: security-and-hardening
description: "Security-first development practices for web applications. Treat every input as hostile, every secret as sacred."
version: 1.0.0
author: Hermes Agent (adapted from addyosmani/agent-skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [security, hardening, owasp, threat-modeling, fastapi, auth]
    related_skills: [requesting-code-review, fastapi-jinja2-feature-build, api-and-interface-design]
---

# Security and Hardening

## Overview

Security-first development practices for web applications. Treat every external input as hostile, every secret as sacred, and every authorization check as mandatory. Security isn't a phase — it's a constraint on every line of code that touches user data, authentication, or external systems.

**Core principle:** Controls bolted on without a threat model are guesses. Spend five minutes thinking like an attacker before hardening.

## When to Use

- Building anything that accepts user input
- Implementing authentication or authorization
- Storing or transmitting sensitive data
- Integrating with external APIs or services
- Adding file uploads, webhooks, or callbacks
- Handling payment or PII data

## Process: Threat Model First

### 1. Map the Trust Boundaries

Where does untrusted data cross into your system? HTTP requests, form fields, file uploads, webhooks, third-party APIs, message queues, and **LLM output**. Every boundary is attack surface.

### 2. Name the Assets

What's worth stealing or breaking? Credentials, PII, payment data, admin actions, money movement.

### 3. Run STRIDE Over Each Boundary

| Threat | Ask | Typical Mitigation |
|---|---|---|
| **S**poofing | Can someone impersonate a user/service? | Authentication, signature verification |
| **T**ampering | Can data be altered in transit or at rest? | Integrity checks, parameterized queries, HTTPS |
| **R**epudiation | Can someone deny they did something? | Audit logs, signed transactions |
| **I**nformation Disclosure | Can someone see data they shouldn't? | Authorization checks, encrypted storage |
| **D**enial of Service | Can someone make this unusable? | Rate limiting, resource limits, queues |
| **E**levation of Privilege | Can someone gain more access than they should? | RBAC, least privilege, principle of least authority |

## OWASP Top 10 Prevention

### 1. Injection (SQL, Command, LDAP, etc.)

**Problem:** Untrusted data is executed as code.

```python
# BAD: SQL injection via f-string
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# GOOD: Parameterized query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# BAD: Command injection via os.system
os.system(f"ls {user_input}")

# GOOD: Safe subprocess
subprocess.run(["ls", user_input], check=True, shell=False)

# BAD: eval/exec with user input
result = eval(f"calculate({user_input})")

# GOOD: Whitelist operations
allowed_operations = {'add': operator.add, 'sub': operator.sub}
op = allowed_operations.get(user_input)
```

**Rules:**
- Never concatenate user input into SQL, shell commands, or code execution
- Use parameterized queries for all database access
- Whitelist allowed operations, don't blacklist disallowed ones
- Validate input format before processing (regex, type checking, allowlists)

### 2. Broken Authentication

**Problem:** Attackers can steal or forge authentication tokens.

```python
# BAD: No rate limiting on login
@app.post("/login")
async def login(form: LoginForm):
    user = await authenticate(form.username, form.password)
    token = create_token(user)
    return {"token": token}

# GOOD: Rate-limited, proper error messages
@app.post("/login")
@rate_limit(max_attempts=5, window_seconds=300)
async def login(form: LoginForm):
    # Constant-time comparison to prevent timing attacks
    if not constant_time_compare(form.password, stored_hash):
        # Generic error — don't reveal whether user exists
        raise HTTPException(401, "Invalid credentials")
    token = create_secure_token(user)
    return {"token": token}
```

**Rules:**
- Use constant-time comparison for password/token checks
- Return generic error messages ("Invalid credentials" not "User not found")
- Implement rate limiting on authentication endpoints
- Use short-lived tokens with refresh mechanisms
- Store passwords with bcrypt/argon2, never plain text or MD5

### 3. Broken Access Control

**Problem:** Users can access resources they shouldn't.

```python
# BAD: No authorization check
@app.get("/api/orders/{order_id}")
async def get_order(order_id: int):
    order = await db.orders.get(order_id)
    return order

# GOOD: Verify ownership
@app.get("/api/orders/{order_id}")
async def get_order(order_id: int, user: CurrentUser):
    order = await db.orders.get(order_id)
    if order.user_id != user.id:
        raise HTTPException(403, "Access denied")
    return order
```

**Rules:**
- Check authorization on EVERY endpoint that returns user data
- Deny by default — grant access explicitly
- Verify ownership or explicit permission
- Use RBAC (Role-Based Access Control) for admin actions

### 4. Insecure Design

**Problem:** Security is an afterthought, not a design constraint.

**Rules:**
- Apply the threat model (STRIDE) during design, not after
- Assume attackers can see your source code — don't rely on "security by obscurity"
- Design for least privilege — every component gets the minimum access it needs
- Log all security-relevant events (auth attempts, access denied, data modifications)

### 5. Security Misconfiguration

**Problem:** Default configurations, exposed debug info, unnecessary features enabled.

**Rules:**
- Disable debug mode in production (`DEBUG = False`)
- Remove default credentials
- Disable unnecessary HTTP methods (DELETE, PUT on endpoints that don't need them)
- Set security headers (HSTS, CSP, X-Frame-Options)
- Don't expose stack traces or internal paths in error messages

### 6. Vulnerable and Outdated Components

**Rules:**
- Regularly update dependencies (`pip list --outdated`)
- Monitor for security advisories (Security Advisories in pip)
- Pin dependency versions in requirements.txt
- Remove unused dependencies — they're attack surface

### 7. Identification and Authentication Failures

See Broken Authentication (#2) above.

### 8. Software and Data Integrity

**Problem:** Supply chain attacks, unsigned updates, unvalidated deserialization.

```python
# BAD: Pickle deserialization (can execute arbitrary code)
import pickle
data = pickle.loads(user_input)

# GOOD: Use JSON or validated formats
import json
data = json.loads(user_input)
validate_schema(data)
```

**Rules:**
- Never deserialize untrusted data with pickle, yaml.load(), or marshal
- Sign and verify code updates
- Use checksums for downloaded dependencies
- Validate all input against a schema before processing

### 9. Security Logging and Monitoring Failures

**Rules:**
- Log all authentication attempts (success and failure)
- Log all authorization failures (access denied)
- Log all data modifications
- Include user ID, IP address, timestamp in every log entry
- Monitor for anomalies (multiple failed logins, unusual access patterns)
- **Never log passwords, tokens, or PII**

### 10. Server-Side Request Forgery (SSRF)

**Problem:** Application makes requests to unintended internal resources.

```python
# BAD: Let user control the URL
async def fetch_url(user_url: str):
    return await httpx.get(user_url)

# GOOD: Whitelist allowed domains
ALLOWED_DOMAINS = {'api.trusted.com', 'cdn.trusted.com'}
async def fetch_url(user_url: str):
    parsed = urlparse(user_url)
    if parsed.hostname not in ALLOWED_DOMAINS:
        raise ValueError("Domain not allowed")
    return await httpx.get(user_url)
```

**Rules:**
- Never let users control outbound URLs directly
- Whitelist allowed destinations
- Block requests to internal/private IP ranges (10.x, 192.168.x, 127.x)
- Use HTTP clients with connection timeouts

## FastAPI-Specific Security

### Input Validation with Pydantic

```python
# Pydantic provides type validation automatically
class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr  # Built-in email validation
    age: int = Field(..., ge=0, le=150)
```

### CORS Configuration

```python
# Be specific — don't use allow_origins=["*"] in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Security Headers

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## Verification

After implementing security measures:

1. **Run static analysis** — `bandit -r app/` for Python, `trivy` for Docker
2. **Check for hardcoded secrets** — grep for `password=`, `secret=`, `api_key=` in code
3. **Review all endpoints** — does each one have auth + authorization?
4. **Test boundary conditions** — what happens with empty input, max-length input, binary input?
5. **Review logs** — are security events being logged appropriately?

## Integration with Other Skills

**requesting-code-review:** Security checks run as part of the code review pipeline. STRIDE threat model for new features.

**fastapi-jinja2-feature-build:** Apply security controls during Phase 1 (spec) and Phase 3 (implementation). Every new endpoint gets auth + input validation.

**api-and-interface-design:** Threat model the API contract before implementation. Define trust boundaries explicitly.

**docker-compose-deployment:** Security in Docker: non-root user, minimal base image, no sensitive data in image layers.