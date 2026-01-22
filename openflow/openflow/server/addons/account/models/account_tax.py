"""
account.tax - Tax Definitions

Tax rates and configurations.
"""
from openflow.server.core.orm import Model, fields


class AccountTax(Model):
    """
    Taxes

    Defines tax rates for sales and purchases.
    """
    _name = 'account.tax'
    _description = 'Tax'
    _order = 'sequence, name'

    name = fields.Char(
        string='Tax Name',
        required=True,
        translate=True,
        help='Tax name'
    )

    description = fields.Char(
        string='Label on Invoices',
        translate=True,
        help='Description shown on invoices'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order'
    )

    # Tax Configuration
    amount_type = fields.Selection(
        selection=[
            ('percent', 'Percentage'),
            ('fixed', 'Fixed'),
            ('group', 'Group of Taxes'),
        ],
        string='Tax Computation',
        default='percent',
        required=True,
        help='How tax amount is computed'
    )

    amount = fields.Float(
        string='Amount',
        default=0.0,
        required=True,
        help='Tax percentage or fixed amount'
    )

    # Tax Type
    type_tax_use = fields.Selection(
        selection=[
            ('sale', 'Sales'),
            ('purchase', 'Purchases'),
            ('none', 'None'),
        ],
        string='Tax Scope',
        default='sale',
        required=True,
        help='Where this tax applies'
    )

    # Price Include
    price_include = fields.Boolean(
        string='Included in Price',
        default=False,
        help='Tax is included in the price'
    )

    # Group
    children_tax_ids = fields.Many2many(
        'account.tax',
        relation='account_tax_group_rel',
        column1='parent_id',
        column2='child_id',
        string='Children Taxes',
        help='Taxes in this group (if tax is a group)'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        help='Company this tax belongs to'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide this tax'
    )

    def compute_all(self, price_unit: float, quantity: float = 1.0) -> dict:
        """
        Compute tax amounts

        Args:
            price_unit: Unit price
            quantity: Quantity

        Returns:
            Dictionary with total_excluded, total_included, taxes
        """
        self.ensure_one()

        base = price_unit * quantity
        taxes = []

        if self.amount_type == 'percent':
            tax_amount = base * (self.amount / 100.0)
            taxes.append({
                'id': self.id,
                'name': self.name,
                'amount': tax_amount,
                'base': base,
            })
        elif self.amount_type == 'fixed':
            tax_amount = self.amount * quantity
            taxes.append({
                'id': self.id,
                'name': self.name,
                'amount': tax_amount,
                'base': base,
            })

        total_tax = sum(t['amount'] for t in taxes)

        return {
            'total_excluded': base,
            'total_included': base + total_tax,
            'taxes': taxes,
        }

    def __repr__(self):
        return f"<AccountTax {self.name} ({self.amount}%)>"


class AccountJournal(Model):
    """
    Accounting Journals

    Journals organize accounting entries by type (sales, purchases, etc.)
    """
    _name = 'account.journal'
    _description = 'Journal'
    _order = 'sequence, name'

    name = fields.Char(
        string='Journal Name',
        required=True,
        help='Journal name'
    )

    code = fields.Char(
        string='Short Code',
        size=5,
        required=True,
        help='Short code for the journal'
    )

    type = fields.Selection(
        selection=[
            ('sale', 'Sales'),
            ('purchase', 'Purchase'),
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('general', 'Miscellaneous'),
        ],
        string='Type',
        required=True,
        default='general',
        help='Journal type'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide this journal'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        help='Company this journal belongs to'
    )

    # Currency
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        help='Journal currency (leave empty for company currency)'
    )

    def __repr__(self):
        return f"<AccountJournal {self.code}: {self.name}>"
