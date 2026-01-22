"""
res.country - Countries and States

Geographic data for countries and their states/provinces.
"""
from openflow.server.core.orm import Model, fields


class ResCountry(Model):
    """
    Countries

    Standard country data with ISO codes and phone codes.
    """
    _name = 'res.country'
    _description = 'Country'
    _order = 'name'

    name = fields.Char(
        string='Country Name',
        required=True,
        index=True,
        translate=True,
        help='Full country name'
    )

    code = fields.Char(
        string='Country Code',
        size=2,
        required=True,
        index=True,
        help='ISO 3166-1 alpha-2 country code (2 letters)'
    )

    iso3 = fields.Char(
        string='ISO Code (3 Letters)',
        size=3,
        help='ISO 3166-1 alpha-3 country code'
    )

    phone_code = fields.Integer(
        string='Country Calling Code',
        help='International calling code (e.g., 1 for USA, 44 for UK)'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        help='Default currency for this country'
    )

    address_format = fields.Text(
        string='Address Format',
        help='Layout for printing addresses. Available variables:\n'
             '%(street)s, %(street2)s, %(city)s, %(state_code)s, '
             '%(state_name)s, %(zip)s, %(country_name)s, %(country_code)s'
    )

    address_view_id = fields.Many2one(
        'ir.ui.view',
        string='Address View',
        help='Custom view for address fields for this country'
    )

    state_ids = fields.One2many(
        'res.country.state',
        'country_id',
        string='States',
        help='States/provinces in this country'
    )

    state_required = fields.Boolean(
        string='State Required',
        default=False,
        help='Check if state field is required for addresses in this country'
    )

    zip_required = fields.Boolean(
        string='ZIP Required',
        default=True,
        help='Check if ZIP/postal code is required for addresses'
    )

    vat_label = fields.Char(
        string='VAT Label',
        default='Tax ID',
        translate=True,
        help='Label to use for VAT/tax ID field'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide the country'
    )

    name_position = fields.Selection(
        selection=[
            ('before', 'Before Address'),
            ('after', 'After Address'),
        ],
        string='Customer Name Position',
        default='before',
        help='Position of customer name in address format'
    )

    def __repr__(self):
        return f"<ResCountry {self.name} ({self.code})>"


class ResCountryState(Model):
    """
    Country States/Provinces

    States, provinces, regions, or other administrative subdivisions.
    """
    _name = 'res.country.state'
    _description = 'Country State'
    _order = 'country_id, name'

    name = fields.Char(
        string='State Name',
        required=True,
        index=True,
        translate=True,
        help='Full state/province name'
    )

    code = fields.Char(
        string='State Code',
        required=True,
        size=3,
        help='State abbreviation or code (e.g., CA for California)'
    )

    country_id = fields.Many2one(
        'res.country',
        string='Country',
        required=True,
        index=True,
        help='Country this state belongs to'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide the state'
    )

    def __repr__(self):
        country_name = self.country_id.name if self.country_id else 'No Country'
        return f"<ResCountryState {self.name} ({self.code}) - {country_name}>"
