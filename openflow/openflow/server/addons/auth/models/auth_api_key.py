"""
auth.api.key - API Key Authentication

Manages API keys for external system authentication.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from openflow.server.core.orm import Model, fields
from openflow.server.core.security import hash_password, verify_password


class AuthApiKey(Model):
    """
    API Keys

    Provides token-based authentication for external systems and integrations.
    Keys can be scoped to specific permissions and have expiration dates.
    """
    _name = 'auth.api.key'
    _description = 'API Key'
    _order = 'created_at desc'

    name = fields.Char(
        string='Name',
        required=True,
        help='Descriptive name for this API key'
    )

    key = fields.Char(
        string='API Key',
        required=True,
        index=True,
        readonly=True,
        help='The API key (store hashed version only!)'
    )

    key_prefix = fields.Char(
        string='Key Prefix',
        size=8,
        readonly=True,
        help='First 8 characters of key for identification'
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        help='User this API key authenticates as'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether the API key is active'
    )

    created_at = fields.DateTime(
        string='Created At',
        required=True,
        default=lambda self: datetime.utcnow(),
        readonly=True,
        help='When the key was created'
    )

    expires_at = fields.DateTime(
        string='Expires At',
        help='When the key expires (optional)'
    )

    last_used_at = fields.DateTime(
        string='Last Used',
        readonly=True,
        help='When the key was last used'
    )

    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        readonly=True,
        help='Number of times this key has been used'
    )

    ip_whitelist = fields.Text(
        string='IP Whitelist',
        help='Comma-separated list of allowed IP addresses (optional)'
    )

    scopes = fields.Char(
        string='Scopes',
        help='Comma-separated list of allowed scopes/permissions'
    )

    description = fields.Text(
        string='Description',
        help='Additional notes about this API key'
    )

    revoked = fields.Boolean(
        string='Revoked',
        default=False,
        help='Whether the key has been revoked'
    )

    revoked_at = fields.DateTime(
        string='Revoked At',
        readonly=True,
        help='When the key was revoked'
    )

    # Computed fields
    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_is_expired',
        store=False,
        help='Whether the key has expired'
    )

    def _compute_is_expired(self):
        """Check if key is expired"""
        now = datetime.utcnow()
        for key in self:
            key.is_expired = key.expires_at < now if key.expires_at else False

    @staticmethod
    def generate_key() -> str:
        """
        Generate a secure random API key

        Returns:
            The generated API key (plain text)
        """
        # Generate 32 bytes = 256 bits of randomness
        # Base64 encoding gives us ~43 characters
        return secrets.token_urlsafe(32)

    async def create(self, vals: dict) -> 'AuthApiKey':
        """
        Override create to generate and hash API key

        Args:
            vals: Values to create key with

        Returns:
            Created API key record
        """
        # Generate key if not provided
        if 'key' not in vals:
            plain_key = self.generate_key()
        else:
            plain_key = vals['key']

        # Store key prefix for identification (first 8 chars)
        vals['key_prefix'] = plain_key[:8]

        # Hash the key before storing (like passwords)
        vals['key'] = hash_password(plain_key)

        record = await super().create(vals)

        # Log the plain key once (should be shown to user)
        # In production, this would be returned to the user and never stored
        print(f"Generated API Key: {plain_key}")
        print(f"Key Prefix: {vals['key_prefix']}")
        print("IMPORTANT: Store this key securely. It cannot be retrieved again.")

        return record

    def verify_key(self, plain_key: str) -> bool:
        """
        Verify an API key against the stored hash

        Args:
            plain_key: The plain text API key to verify

        Returns:
            True if key is valid
        """
        return verify_password(plain_key, self.key)

    def is_valid(self, ip_address: Optional[str] = None) -> bool:
        """
        Check if API key is valid

        Args:
            ip_address: Optional IP address to check against whitelist

        Returns:
            True if key is valid
        """
        # Check basic validity
        if not self.active or self.revoked:
            return False

        # Check expiration
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False

        # Check IP whitelist if configured
        if self.ip_whitelist and ip_address:
            allowed_ips = [ip.strip() for ip in self.ip_whitelist.split(',')]
            if ip_address not in allowed_ips:
                return False

        return True

    def record_usage(self) -> None:
        """
        Record that this API key was used
        """
        self.write({
            'last_used_at': datetime.utcnow(),
            'usage_count': self.usage_count + 1,
        })

    def revoke(self) -> None:
        """
        Revoke the API key
        """
        self.write({
            'active': False,
            'revoked': True,
            'revoked_at': datetime.utcnow(),
        })

    async def cleanup_expired(self) -> int:
        """
        Clean up expired API keys

        Returns:
            Number of keys removed
        """
        expired = await self.search([
            ('expires_at', '<', datetime.utcnow()),
            ('expires_at', '!=', False)
        ])
        count = len(expired._ids)
        await expired.unlink()
        return count

    def __repr__(self):
        return f"<AuthApiKey {self.name} ({self.key_prefix}...)>"
