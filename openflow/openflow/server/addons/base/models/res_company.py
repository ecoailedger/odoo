"""
res.company - Company Management

Multi-company support and organization structure.
"""
from openflow.server.core.orm import Model, fields


class ResCompany(Model):
    """
    Companies

    Represents companies/organizations in a multi-company environment.
    Used for data segregation and multi-tenant support.
    """
    _name = 'res.company'
    _description = 'Companies'
    _order = 'sequence, name'

    name = fields.Char(
        string='Company Name',
        required=True,
        index=True,
        help='Official name of the company'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order'
    )

    parent_id = fields.Many2one(
        'res.company',
        string='Parent Company',
        index=True,
        help='Parent company for hierarchical organizations'
    )

    child_ids = fields.One2many(
        'res.company',
        'parent_id',
        string='Child Companies',
        help='Subsidiary companies'
    )

    # Company Information
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    city = fields.Char(string='City')
    state_id = fields.Many2one(
        'res.country.state',
        string='State'
    )
    zip = fields.Char(string='Zip')
    country_id = fields.Many2one(
        'res.country',
        string='Country'
    )

    email = fields.Char(
        string='Email',
        help='Company email address'
    )

    phone = fields.Char(
        string='Phone',
        help='Company phone number'
    )

    website = fields.Char(
        string='Website',
        help='Company website URL'
    )

    vat = fields.Char(
        string='Tax ID',
        help='Tax identification number'
    )

    company_registry = fields.Char(
        string='Company Registry',
        help='Official company registration number'
    )

    # Branding
    logo = fields.Binary(
        string='Company Logo',
        help='Logo displayed in reports and UI'
    )

    logo_web = fields.Binary(
        string='Website Logo',
        help='Logo for website/portal'
    )

    favicon = fields.Binary(
        string='Favicon',
        help='Website favicon (16x16 or 32x32 pixels)'
    )

    primary_color = fields.Char(
        string='Primary Color',
        default='#875A7B',
        help='Primary brand color (hex code)'
    )

    secondary_color = fields.Char(
        string='Secondary Color',
        default='#5A5A5A',
        help='Secondary brand color (hex code)'
    )

    # Currency and Localization
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        help='Default currency for this company'
    )

    # Report Configuration
    paperformat_id = fields.Many2one(
        'report.paperformat',
        string='Paper Format',
        help='Default paper format for reports'
    )

    external_report_layout_id = fields.Many2one(
        'ir.ui.view',
        string='Document Template',
        help='Header/footer template for PDF reports'
    )

    # Social Media
    social_twitter = fields.Char(string='Twitter Account')
    social_facebook = fields.Char(string='Facebook Account')
    social_github = fields.Char(string='GitHub Account')
    social_linkedin = fields.Char(string='LinkedIn Account')
    social_youtube = fields.Char(string='YouTube Account')

    # Multi-Company Rules
    user_ids = fields.Many2many(
        'res.users',
        relation='res_company_users_rel',
        column1='cid',
        column2='user_id',
        string='Accepted Users',
        help='Users that have access to this company'
    )

    # Bank Accounts
    bank_ids = fields.One2many(
        'res.partner.bank',
        'company_id',
        string='Bank Accounts',
        help='Company bank accounts'
    )

    # Technical
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, company is hidden'
    )

    def get_full_address(self) -> str:
        """
        Get formatted full address

        Returns:
            Formatted address string
        """
        parts = []
        if self.street:
            parts.append(self.street)
        if self.street2:
            parts.append(self.street2)

        city_parts = []
        if self.city:
            city_parts.append(self.city)
        if self.state_id and hasattr(self.state_id, 'name'):
            city_parts.append(self.state_id.name)
        if self.zip:
            city_parts.append(self.zip)
        if city_parts:
            parts.append(', '.join(city_parts))

        if self.country_id and hasattr(self.country_id, 'name'):
            parts.append(self.country_id.name)

        return '\n'.join(parts)

    def __repr__(self):
        return f"<ResCompany {self.name}>"
