"""
res.users - User Management

User accounts and authentication.
"""
from datetime import datetime
from openflow.server.core.orm import Model, fields


class ResUsers(Model):
    """
    Users

    Represents user accounts in the system.
    Users can belong to multiple security groups and companies.
    """
    _name = 'res.users'
    _description = 'Users'
    _order = 'name, login'

    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help='Full name of the user'
    )

    login = fields.Char(
        string='Login',
        required=True,
        index=True,
        help='Used to log into the system'
    )

    password = fields.Char(
        string='Password',
        help='Encrypted password (never store in plain text!)'
    )

    email = fields.Char(
        string='Email',
        index=True,
        help='Email address'
    )

    phone = fields.Char(
        string='Phone',
        help='Phone number'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, the user cannot log in'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        help='Main company for this user'
    )

    company_ids = fields.Many2many(
        'res.company',
        relation='res_company_users_rel',
        column1='user_id',
        column2='cid',
        string='Companies',
        help='Companies the user has access to'
    )

    groups_id = fields.Many2many(
        'res.groups',
        relation='res_groups_users_rel',
        column1='uid',
        column2='gid',
        string='Groups',
        help='Security groups the user belongs to'
    )

    lang = fields.Selection([
        ('en_US', 'English'),
        ('fr_FR', 'French'),
        ('es_ES', 'Spanish'),
        ('de_DE', 'German'),
        ('pt_PT', 'Portuguese'),
        ('zh_CN', 'Chinese (Simplified)'),
    ], string='Language', default='en_US',
        help='User interface language')

    tz = fields.Selection([
        ('UTC', 'UTC'),
        ('America/New_York', 'US/Eastern'),
        ('America/Chicago', 'US/Central'),
        ('America/Denver', 'US/Mountain'),
        ('America/Los_Angeles', 'US/Pacific'),
        ('Europe/London', 'Europe/London'),
        ('Europe/Paris', 'Europe/Paris'),
        ('Asia/Shanghai', 'Asia/Shanghai'),
        ('Asia/Tokyo', 'Asia/Tokyo'),
    ], string='Timezone', default='UTC',
        help='Timezone for displaying dates and times')

    signature = fields.Text(
        string='Email Signature',
        help='Email signature for outgoing messages'
    )

    action_id = fields.Many2one(
        'ir.actions.act_window',
        string='Home Action',
        help='Default action to open when user logs in'
    )

    share = fields.Boolean(
        string='Share User',
        default=False,
        help='External user with limited access (portal/website)'
    )

    login_date = fields.DateTime(
        string='Latest Login',
        readonly=True,
        help='Last successful login date'
    )

    notification_type = fields.Selection([
        ('email', 'Handle by Emails'),
        ('inbox', 'Handle in OpenFlow'),
    ], string='Notification', default='email',
        help='How to receive notifications')

    image = fields.Binary(
        string='Avatar',
        help='User avatar image'
    )

    # Computed fields
    im_status = fields.Char(
        string='IM Status',
        compute='_compute_im_status',
        store=False,
        help='Instant messaging status'
    )

    def _compute_im_status(self):
        """Compute instant messaging status"""
        for user in self:
            # Simple implementation - can be enhanced with real presence detection
            user.im_status = 'online' if user.active else 'offline'

    def has_group(self, group_ext_id: str) -> bool:
        """
        Check if user belongs to a specific group

        Args:
            group_ext_id: External ID of the group (e.g., 'base.group_user')

        Returns:
            True if user has the group
        """
        # TODO: Implement external ID resolution
        # For now, just check by group name
        for group in self.groups_id:
            if group.name == group_ext_id:
                return True
        return False

    def get_company(self):
        """Get the user's current company"""
        return self.company_id

    def authenticate(self, password: str) -> bool:
        """
        Authenticate user with password

        Args:
            password: Plain text password to verify

        Returns:
            True if authentication successful
        """
        # TODO: Implement proper password hashing with passlib
        # This is a placeholder
        return self.password == password

    def update_login_date(self):
        """Update the last login date"""
        self.write({'login_date': datetime.now()})

    def __repr__(self):
        return f"<ResUsers {self.login}>"
