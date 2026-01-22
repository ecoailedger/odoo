"""
auth.session - Session Management

Tracks active user sessions for security and monitoring.
"""
from datetime import datetime, timedelta
from openflow.server.core.orm import Model, fields


class AuthSession(Model):
    """
    User Sessions

    Tracks active sessions for security monitoring and management.
    Sessions can be invalidated remotely for security purposes.
    """
    _name = 'auth.session'
    _description = 'User Session'
    _order = 'created_at desc'

    session_id = fields.Char(
        string='Session ID',
        required=True,
        index=True,
        help='Unique session identifier'
    )

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        help='User associated with this session'
    )

    created_at = fields.DateTime(
        string='Created At',
        required=True,
        default=lambda self: datetime.utcnow(),
        help='When the session was created'
    )

    last_activity = fields.DateTime(
        string='Last Activity',
        required=True,
        default=lambda self: datetime.utcnow(),
        help='Last activity timestamp'
    )

    expires_at = fields.DateTime(
        string='Expires At',
        required=True,
        help='When the session expires'
    )

    ip_address = fields.Char(
        string='IP Address',
        help='Client IP address'
    )

    user_agent = fields.Char(
        string='User Agent',
        help='Client user agent string'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether the session is active'
    )

    revoked = fields.Boolean(
        string='Revoked',
        default=False,
        help='Whether the session was manually revoked'
    )

    revoked_at = fields.DateTime(
        string='Revoked At',
        readonly=True,
        help='When the session was revoked'
    )

    device_type = fields.Selection([
        ('web', 'Web Browser'),
        ('mobile', 'Mobile App'),
        ('desktop', 'Desktop App'),
        ('api', 'API Client'),
    ], string='Device Type', default='web',
        help='Type of device/client')

    # Computed fields
    is_expired = fields.Boolean(
        string='Is Expired',
        compute='_compute_is_expired',
        store=False,
        help='Whether the session has expired'
    )

    def _compute_is_expired(self):
        """Check if session is expired"""
        now = datetime.utcnow()
        for session in self:
            session.is_expired = session.expires_at < now if session.expires_at else False

    def is_valid(self) -> bool:
        """
        Check if session is valid (active and not expired)

        Returns:
            True if session is valid
        """
        if not self.active or self.revoked:
            return False

        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False

        return True

    def revoke(self) -> None:
        """
        Revoke the session (logout)
        """
        self.write({
            'active': False,
            'revoked': True,
            'revoked_at': datetime.utcnow(),
        })

    def update_activity(self) -> None:
        """
        Update last activity timestamp
        """
        self.write({
            'last_activity': datetime.utcnow(),
        })

    async def cleanup_expired(self) -> int:
        """
        Clean up expired sessions

        Returns:
            Number of sessions removed
        """
        expired = await self.search([
            ('expires_at', '<', datetime.utcnow())
        ])
        count = len(expired._ids)
        await expired.unlink()
        return count

    def __repr__(self):
        return f"<AuthSession {self.session_id} for {self.user_id.login}>"
