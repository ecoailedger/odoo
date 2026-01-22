"""
res.partner - Business Partners (Contacts/Companies)

Partners represent individuals or companies that the business interacts with:
customers, suppliers, employees, etc.
"""
from openflow.server.core.orm import Model, fields


class ResPartner(Model):
    """
    Business Partners

    Represents contacts, companies, customers, suppliers, and any
    other third-party entity the business interacts with.
    """
    _name = 'res.partner'
    _description = 'Contact'
    _order = 'display_name'
    _rec_name = 'display_name'

    # Basic Information
    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help='Contact or company name'
    )

    ref = fields.Char(
        string='Reference',
        index=True,
        help='Internal reference code'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to archive the contact'
    )

    # Contact Information
    email = fields.Char(
        string='Email',
        index=True,
        help='Email address'
    )

    phone = fields.Char(
        string='Phone',
        help='Phone number'
    )

    mobile = fields.Char(
        string='Mobile',
        help='Mobile phone number'
    )

    website = fields.Char(
        string='Website',
        help='Website URL'
    )

    # Address Fields
    street = fields.Char(
        string='Street',
        help='Street address'
    )

    street2 = fields.Char(
        string='Street 2',
        help='Additional address line'
    )

    city = fields.Char(
        string='City',
        help='City name'
    )

    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        help='State/Province/Region'
    )

    zip = fields.Char(
        string='ZIP',
        help='Postal/ZIP code'
    )

    country_id = fields.Many2one(
        'res.country',
        string='Country',
        help='Country'
    )

    # Type and Classification
    company_type = fields.Selection(
        selection=[
            ('person', 'Individual'),
            ('company', 'Company'),
        ],
        string='Company Type',
        default='person',
        required=True,
        help='Type of contact'
    )

    is_company = fields.Boolean(
        string='Is a Company',
        compute='_compute_is_company',
        store=True,
        depends=['company_type'],
        help='Check if the partner is a company, otherwise it is a person'
    )

    # Company/Contact Hierarchy
    parent_id = fields.Many2one(
        'res.partner',
        string='Related Company',
        index=True,
        help='Company this contact works for'
    )

    child_ids = fields.One2many(
        'res.partner',
        'parent_id',
        string='Contacts',
        help='Contact persons for this company'
    )

    # Tax Information
    vat = fields.Char(
        string='Tax ID',
        index=True,
        help='Tax identification number (VAT/EIN/etc.)'
    )

    # Customer/Supplier Rankings
    customer_rank = fields.Integer(
        string='Customer Rank',
        default=0,
        help='Number of customer transactions. Automatically computed.'
    )

    supplier_rank = fields.Integer(
        string='Supplier Rank',
        default=0,
        help='Number of supplier transactions. Automatically computed.'
    )

    # Additional Information
    comment = fields.Text(
        string='Notes',
        help='Internal notes'
    )

    image = fields.Binary(
        string='Image',
        attachment=True,
        help='Contact photo or company logo'
    )

    # Category Tags
    category_ids = fields.Many2many(
        'res.partner.category',
        relation='res_partner_category_rel',
        column1='partner_id',
        column2='category_id',
        string='Tags',
        help='Tags for categorizing partners'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help='Company this partner belongs to (for multi-company setups)'
    )

    # User Link
    user_ids = fields.One2many(
        'res.users',
        'partner_id',
        string='Users',
        help='System users linked to this partner'
    )

    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        depends=['name', 'ref', 'parent_id', 'parent_id.name'],
        help='Full display name including reference and parent company'
    )

    contact_address = fields.Char(
        string='Complete Address',
        compute='_compute_contact_address',
        help='Full formatted address'
    )

    # Related Fields
    parent_name = fields.Char(
        string='Parent Company Name',
        related='parent_id.name',
        readonly=True,
        help='Name of the parent company'
    )

    country_code = fields.Char(
        string='Country Code',
        related='country_id.code',
        readonly=True,
        help='ISO country code'
    )

    def _compute_is_company(self):
        """Compute is_company flag based on company_type"""
        for record in self:
            record.is_company = record.company_type == 'company'

    def _compute_display_name(self):
        """Compute full display name"""
        for record in self:
            name = record.name or ''

            # Add reference if exists
            if record.ref:
                name = f"[{record.ref}] {name}"

            # Add parent company name for contacts
            if record.parent_id and record.company_type == 'person':
                name = f"{name}, {record.parent_id.name}"

            record.display_name = name

    def _compute_contact_address(self):
        """Compute full formatted address"""
        for record in self:
            address_parts = []

            if record.street:
                address_parts.append(record.street)
            if record.street2:
                address_parts.append(record.street2)

            city_line = []
            if record.city:
                city_line.append(record.city)
            if record.state_id and hasattr(record.state_id, 'name'):
                city_line.append(record.state_id.name)
            if record.zip:
                city_line.append(record.zip)

            if city_line:
                address_parts.append(', '.join(city_line))

            if record.country_id and hasattr(record.country_id, 'name'):
                address_parts.append(record.country_id.name)

            record.contact_address = '\n'.join(address_parts)

    def get_formatted_address(self) -> str:
        """
        Get formatted address as string

        Returns:
            Formatted address string
        """
        return self.contact_address

    def increment_customer_rank(self):
        """Increment customer rank (called when customer transaction is created)"""
        self.write({'customer_rank': self.customer_rank + 1})

    def increment_supplier_rank(self):
        """Increment supplier rank (called when supplier transaction is created)"""
        self.write({'supplier_rank': self.supplier_rank + 1})

    def __repr__(self):
        return f"<ResPartner {self.display_name}>"


class ResPartnerCategory(Model):
    """
    Partner Categories/Tags

    Used to categorize partners for filtering and reporting.
    """
    _name = 'res.partner.category'
    _description = 'Partner Tags'
    _order = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
        index=True,
        translate=True,
        help='Category name'
    )

    color = fields.Integer(
        string='Color Index',
        help='Color for display in UI'
    )

    parent_id = fields.Many2one(
        'res.partner.category',
        string='Parent Category',
        index=True,
        help='Parent category for hierarchical organization'
    )

    child_ids = fields.One2many(
        'res.partner.category',
        'parent_id',
        string='Child Categories',
        help='Child categories'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide the category'
    )

    partner_ids = fields.Many2many(
        'res.partner',
        relation='res_partner_category_rel',
        column1='category_id',
        column2='partner_id',
        string='Partners',
        help='Partners with this category'
    )

    def __repr__(self):
        return f"<ResPartnerCategory {self.name}>"
