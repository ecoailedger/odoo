# OpenFlow Security System

Comprehensive security and authentication system for the OpenFlow ERP framework.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Authorization](#authorization)
- [Security Components](#security-components)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Best Practices](#best-practices)

## Overview

The OpenFlow security system provides multi-layered protection:

1. **Authentication**: Verifying user identity
2. **Authorization**: Controlling access to resources
3. **Encryption**: Protecting sensitive data
4. **Audit**: Tracking security events

### Security Layers

```
┌─────────────────────────────────────────┐
│         API/Controller Layer            │
│  (Authentication, Rate Limiting)        │
├─────────────────────────────────────────┤
│         Model-Level Access              │
│  (CRUD permissions per group)           │
├─────────────────────────────────────────┤
│         Record-Level Rules              │
│  (Domain-based row filtering)           │
├─────────────────────────────────────────┤
│         Field-Level Security            │
│  (Group-based field visibility)         │
├─────────────────────────────────────────┤
│        Multi-Company Filtering          │
│  (Automatic company_id filtering)       │
└─────────────────────────────────────────┘
```

## Authentication

### 1. Password Hashing

Passwords are hashed using **Argon2id** (winner of the Password Hashing Competition).

```python
from openflow.server.core.security import hash_password, verify_password

# Hash a password
hashed = hash_password("my_secure_password")

# Verify a password
is_valid = verify_password("my_secure_password", hashed)
```

**Features:**
- Argon2id with bcrypt fallback
- Automatic hash migration
- Salt generation
- Configurable work factors

### 2. JWT Tokens

Session-less authentication using JSON Web Tokens.

```python
from openflow.server.core.security import create_token_pair, decode_token

# Create access and refresh tokens
tokens = create_token_pair(
    user_id="123",
    username="john",
    email="john@example.com"
)

# Tokens dict contains:
# - access_token: Short-lived (30 minutes)
# - refresh_token: Long-lived (7 days)
# - token_type: "bearer"

# Decode and validate token
payload = decode_token(tokens['access_token'])
user_id = payload['sub']
```

**Token Types:**
- **Access Token**: Used for API requests (30 min default)
- **Refresh Token**: Used to get new access tokens (7 days default)

### 3. Session Management

Track active user sessions for security monitoring.

```python
from openflow.server.core.security import session_manager

# Create session
session = session_manager.create_session(
    user_id="123",
    ip_address="192.168.1.1",
    user_agent="Mozilla/5.0",
    expires_in_hours=24
)

# Get session
session = session_manager.get_session(session_id)

# Invalidate session (logout)
session_manager.delete_session(session_id)

# Delete all user sessions
session_manager.delete_user_sessions(user_id)
```

### 4. API Key Authentication

Token-based authentication for external systems.

```python
# Create API key (in auth.api.key model)
api_key = env['auth.api.key'].create({
    'name': 'Integration with System X',
    'user_id': user.id,
    'expires_at': datetime.now() + timedelta(days=365),
    'scopes': 'read,write',
    'ip_whitelist': '10.0.0.1,10.0.0.2'
})

# Verify API key
if api_key.verify_key(plain_key) and api_key.is_valid(ip_address):
    api_key.record_usage()
    # Proceed with authenticated request
```

## Authorization

### 1. Model-Level Access (ir.model.access)

CRUD permissions per model per group.

**CSV Format:**
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_partner_user,Partner User,res.partner,base.group_user,1,1,1,0
access_partner_public,Partner Public,res.partner,,1,0,0,0
```

**Enforcement:**
```python
# Automatically checked in ORM operations
partners = await env['res.partner'].search([])  # Checks read access
await partner.write({'name': 'New Name'})       # Checks write access
await partner.unlink()                          # Checks unlink access
```

**Manual Check:**
```python
from openflow.server.core.security import AccessController

controller = AccessController(env)
has_access = controller.check_model_access('res.partner', 'write')
```

### 2. Record Rules (ir.rule)

Row-level security using domain expressions.

**Example: Users can only see their own records**
```python
{
    'name': 'Own Records Only',
    'model_id': ref('model_sale_order'),
    'domain_force': [('user_id', '=', user.id)],
    'groups': [ref('base.group_user')],
    'perm_read': True,
    'perm_write': True,
    'perm_create': False,
    'perm_unlink': False,
}
```

**Global Rules** (apply to all users):
```python
{
    'name': 'Active Records Only',
    'model_id': ref('model_res_partner'),
    'domain_force': [('active', '=', True)],
    'groups': [],  # Empty = global rule
    'perm_read': True,
}
```

**Automatic Application:**
Record rules are automatically applied to `search()` and `search_count()` operations.

### 3. Field-Level Security

Restrict field visibility to specific groups.

```python
from openflow.server.core.orm import fields

class ResUsers(Model):
    _name = 'res.users'

    name = fields.Char('Name')

    # Only system admins can see salary
    salary = fields.Float(
        'Salary',
        groups='base.group_system'
    )

    # Multiple groups (any of them can access)
    ssn = fields.Char(
        'Social Security Number',
        groups='base.group_system,hr.group_hr_manager'
    )
```

**Enforcement:**
Fields with `groups` attribute are automatically filtered out in `read()` operations for users not in those groups.

### 4. Multi-Company Security

Automatic filtering based on user's allowed companies.

```python
class SaleOrder(Model):
    _name = 'sale.order'
    _check_company_auto = True  # Enable auto-filtering (default)

    name = fields.Char('Name')
    company_id = fields.Many2one('res.company', 'Company')
```

**Automatic Filtering:**
```python
# User has access to companies 1, 3, 5
# Search automatically filters: [('company_id', 'in', [1, 3, 5])]
orders = await env['sale.order'].search([])
# Only returns orders from companies 1, 3, 5
```

**Disable Auto-Filtering:**
```python
class MyModel(Model):
    _name = 'my.model'
    _check_company_auto = False  # Disable automatic filtering
```

### 5. Superuser Bypass

User with ID=1 bypasses all access checks.

```python
from openflow.server.core.security import SUPERUSER_ID

# Check if superuser
if env.user.id == SUPERUSER_ID:
    # Has unlimited access
    pass
```

## Security Components

### Decorators

Protect model methods with security decorators.

```python
from openflow.server.core.security import (
    require_login,
    check_access,
    require_groups,
    superuser_only,
    with_company,
    rate_limit
)

class MyModel(Model):
    _name = 'my.model'

    @require_login
    def my_method(self):
        """Requires authenticated user"""
        pass

    @check_access('write')
    def update_data(self):
        """Requires write permission on my.model"""
        pass

    @require_groups('base.group_system')
    def admin_only_method(self):
        """Only system admins can call this"""
        pass

    @superuser_only
    def dangerous_operation(self):
        """Only superuser can call this"""
        pass

    @with_company(company_id=2)
    def do_in_company_2(self):
        """Execute in context of company 2"""
        pass

    @rate_limit(max_calls=5, period_seconds=60)
    def send_email(self):
        """Limited to 5 calls per minute"""
        pass
```

### Exceptions

```python
from openflow.server.core.security import (
    SecurityError,
    AccessDenied,
    AuthenticationError,
    InvalidCredentials,
    InvalidToken,
    SessionExpired,
    InsufficientPermissions,
    FieldAccessDenied,
    RecordAccessDenied,
)

try:
    await partner.unlink()
except AccessDenied as e:
    print(f"Access denied: {e}")
except InsufficientPermissions as e:
    print(f"Insufficient permissions: {e}")
```

## Usage Examples

### Complete Authentication Flow

```python
from fastapi import FastAPI, HTTPException
from openflow.server.core.security import (
    create_token_pair,
    session_manager,
    InvalidCredentials
)

app = FastAPI()

@app.post("/login")
async def login(username: str, password: str, request: Request):
    # Get user
    user = await env['res.users'].search([('login', '=', username)])

    if not user or not user.authenticate(password):
        raise HTTPException(401, "Invalid credentials")

    # Create tokens
    tokens = create_token_pair(
        user_id=str(user.id),
        username=user.login
    )

    # Create session
    session = session_manager.create_session(
        user_id=str(user.id),
        ip_address=request.client.host,
        user_agent=request.headers.get('user-agent')
    )

    # Update last login
    await user.update_login_date()

    return {
        **tokens,
        'session_id': session.session_id,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }
    }

@app.post("/logout")
async def logout(session_id: str):
    session_manager.delete_session(session_id)
    return {'message': 'Logged out'}
```

### Secure Model with All Features

```python
from openflow.server.core.orm import Model, fields
from openflow.server.core.security import (
    check_access,
    require_groups,
    require_login
)

class SecureDocument(Model):
    _name = 'secure.document'
    _description = 'Secure Document'
    _check_company_auto = True  # Multi-company filtering

    # Fields
    name = fields.Char('Name', required=True)
    content = fields.Text('Content')

    # Only HR can see employee data
    employee_data = fields.Text(
        'Employee Data',
        groups='hr.group_hr_manager'
    )

    # Multi-company
    company_id = fields.Many2one('res.company', 'Company')

    # Owner (for record rules)
    user_id = fields.Many2one('res.users', 'Owner')

    @require_login
    @check_access('write')
    def update_content(self, new_content):
        """Update document content"""
        self.write({'content': new_content})

    @require_groups('base.group_system')
    def delete_all(self):
        """Delete all documents (admin only)"""
        all_docs = self.search([])
        all_docs.unlink()
```

### Record Rule for Own Records

```xml
<record id="rule_document_own" model="ir.rule">
    <field name="name">Own Documents</field>
    <field name="model_id" ref="model_secure_document"/>
    <field name="domain_force">[('user_id', '=', user.id)]</field>
    <field name="groups" eval="[(4, ref('base.group_user'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_create" eval="True"/>
    <field name="perm_unlink" eval="True"/>
</record>
```

## Configuration

### Environment Variables

```bash
# JWT Configuration
SECRET_KEY=your-secret-key-here  # CHANGE IN PRODUCTION!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Policy (future)
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL=true
```

### Settings.py

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
```

## Best Practices

### 1. Password Security

✅ **DO:**
- Use strong passwords (min 12 characters)
- Hash passwords before storing
- Use `verify_and_update()` to migrate old hashes
- Implement password rotation policies

❌ **DON'T:**
- Store plain text passwords
- Log passwords
- Send passwords in URLs
- Reuse passwords across systems

### 2. Token Security

✅ **DO:**
- Use short-lived access tokens (15-30 minutes)
- Store tokens securely (httpOnly cookies or secure storage)
- Validate tokens on every request
- Implement token rotation
- Use HTTPS in production

❌ **DON'T:**
- Store tokens in localStorage (XSS risk)
- Use long-lived access tokens
- Share tokens between users
- Include sensitive data in tokens

### 3. Session Security

✅ **DO:**
- Track active sessions
- Implement session timeouts
- Allow users to view/revoke sessions
- Log session events
- Validate IP and user agent (optional)

❌ **DON'T:**
- Allow unlimited sessions
- Keep expired sessions
- Skip session validation

### 4. Access Control

✅ **DO:**
- Follow principle of least privilege
- Use groups for permissions
- Implement both model and record rules
- Test access controls thoroughly
- Document permission requirements

❌ **DON'T:**
- Give everyone admin access
- Rely only on model-level permissions
- Skip record rules
- Hardcode user IDs

### 5. API Security

✅ **DO:**
- Require authentication for sensitive endpoints
- Rate limit API calls
- Validate all inputs
- Use API keys for service accounts
- Log API usage

❌ **DON'T:**
- Expose admin endpoints publicly
- Allow unlimited requests
- Trust user input
- Use user passwords for API access

## Testing

Run security tests:

```bash
# All security tests
pytest tests/test_security_*.py

# Specific test files
pytest tests/test_security_password.py
pytest tests/test_security_jwt.py
pytest tests/test_security_session.py
```

## Troubleshooting

### "Access Denied" Errors

1. Check user has required groups
2. Verify model access rules
3. Check record rules aren't too restrictive
4. Confirm user is active

### "Invalid Token" Errors

1. Check token hasn't expired
2. Verify SECRET_KEY is correct
3. Ensure token type matches (access vs refresh)
4. Check token wasn't revoked

### Sessions Not Working

1. Verify session isn't expired
2. Check session manager is configured
3. Ensure session ID is correct
4. Check for session cleanup

## Security Checklist

- [ ] Change default SECRET_KEY in production
- [ ] Use HTTPS for all communications
- [ ] Implement rate limiting
- [ ] Enable audit logging
- [ ] Configure password policies
- [ ] Set up session timeouts
- [ ] Review access control rules
- [ ] Test with different user roles
- [ ] Monitor authentication logs
- [ ] Regular security audits

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [Password Hashing Competition](https://www.password-hashing.net/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

## Support

For security issues, please contact: security@openflow.example.com

**Do not open public issues for security vulnerabilities.**
