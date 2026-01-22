"""
auth.log - Authentication Audit Log

Tracks authentication events for security monitoring and compliance.
"""
from datetime import datetime
from openflow.server.core.orm import Model, fields


class AuthLog(Model):
    """
    Authentication Log

    Records all authentication attempts (successful and failed) for
    security monitoring, compliance, and debugging.
    """
    _name = 'auth.log'
    _description = 'Authentication Log'
    _order = 'created_at desc'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        index=True,
        help='User who attempted authentication (if known)'
    )

    login = fields.Char(
        string='Login',
        index=True,
        help='Login/username used in attempt'
    )

    event_type = fields.Selection([
        ('login_success', 'Login Success'),
        ('login_fail', 'Login Failed'),
        ('logout', 'Logout'),
        ('session_expired', 'Session Expired'),
        ('api_key_used', 'API Key Used'),
        ('api_key_invalid', 'API Key Invalid'),
        ('password_change', 'Password Changed'),
        ('password_reset', 'Password Reset'),
        ('token_refresh', 'Token Refreshed'),
        ('account_locked', 'Account Locked'),
    ], string='Event Type', required=True, index=True,
        help='Type of authentication event')

    success = fields.Boolean(
        string='Success',
        default=False,
        index=True,
        help='Whether the authentication was successful'
    )

    created_at = fields.DateTime(
        string='Timestamp',
        required=True,
        default=lambda self: datetime.utcnow(),
        index=True,
        help='When the event occurred'
    )

    ip_address = fields.Char(
        string='IP Address',
        index=True,
        help='Client IP address'
    )

    user_agent = fields.Char(
        string='User Agent',
        help='Client user agent string'
    )

    method = fields.Selection([
        ('password', 'Password'),
        ('api_key', 'API Key'),
        ('token', 'JWT Token'),
        ('oauth', 'OAuth'),
        ('saml', 'SAML'),
    ], string='Auth Method',
        help='Authentication method used')

    session_id = fields.Char(
        string='Session ID',
        help='Session identifier if applicable'
    )

    failure_reason = fields.Char(
        string='Failure Reason',
        help='Reason for authentication failure'
    )

    details = fields.Text(
        string='Details',
        help='Additional details about the event'
    )

    risk_score = fields.Integer(
        string='Risk Score',
        default=0,
        help='Calculated risk score for this event (0-100)'
    )

    country = fields.Char(
        string='Country',
        help='Country derived from IP address'
    )

    city = fields.Char(
        string='City',
        help='City derived from IP address'
    )

    @staticmethod
    async def log_event(
        event_type: str,
        login: str = None,
        user_id: int = None,
        success: bool = False,
        ip_address: str = None,
        user_agent: str = None,
        method: str = 'password',
        session_id: str = None,
        failure_reason: str = None,
        details: str = None,
        **kwargs
    ):
        """
        Log an authentication event

        Args:
            event_type: Type of event
            login: Login/username
            user_id: User ID
            success: Whether successful
            ip_address: Client IP
            user_agent: User agent
            method: Auth method
            session_id: Session ID
            failure_reason: Reason for failure
            details: Additional details
            **kwargs: Additional fields
        """
        # This would normally use the environment to create the record
        # For now, just print (would need proper async context)
        print(f"[AUTH LOG] {event_type}: {login} from {ip_address} - {'SUCCESS' if success else 'FAILED'}")

    async def get_failed_attempts(self, login: str, since_minutes: int = 15) -> int:
        """
        Get number of failed login attempts for a user

        Args:
            login: Login/username
            since_minutes: Time window in minutes

        Returns:
            Number of failed attempts
        """
        from datetime import timedelta
        since_time = datetime.utcnow() - timedelta(minutes=since_minutes)

        failed = await self.search_count([
            ('login', '=', login),
            ('event_type', '=', 'login_fail'),
            ('created_at', '>=', since_time),
        ])

        return failed

    async def get_recent_logins(self, user_id: int, limit: int = 10):
        """
        Get recent login events for a user

        Args:
            user_id: User ID
            limit: Number of events to retrieve

        Returns:
            RecordSet of recent login events
        """
        return await self.search(
            domain=[
                ('user_id', '=', user_id),
                ('event_type', 'in', ['login_success', 'login_fail']),
            ],
            limit=limit,
            order='created_at desc'
        )

    async def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Clean up old log entries

        Args:
            days: Keep logs newer than this many days

        Returns:
            Number of logs removed
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        old_logs = await self.search([
            ('created_at', '<', cutoff_date)
        ])

        count = len(old_logs._ids)
        await old_logs.unlink()
        return count

    def __repr__(self):
        return f"<AuthLog {self.event_type} for {self.login} at {self.created_at}>"
