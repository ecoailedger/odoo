"""
account.move.line - Invoice Lines

Line items on invoices and bills.
"""
from openflow.server.core.orm import Model, fields


class AccountMoveLine(Model):
    """
    Invoice Lines

    Individual line items on invoices with product, quantity, and price.
    """
    _name = 'account.move.line'
    _description = 'Invoice Line'
    _order = 'move_id, sequence, id'

    move_id = fields.Many2one(
        'account.move',
        string='Invoice',
        required=True,
        index=True,
        help='Related invoice'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order'
    )

    # Product
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='Product for this line'
    )

    name = fields.Text(
        string='Description',
        required=True,
        help='Line item description'
    )

    # Quantity and UoM
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        required=True,
        help='Quantity'
    )

    product_uom_id = fields.Many2one(
        'product.uom',
        string='Unit of Measure',
        help='Unit of measure'
    )

    # Pricing
    price_unit = fields.Float(
        string='Unit Price',
        required=True,
        default=0.0,
        help='Price per unit'
    )

    discount = fields.Float(
        string='Discount (%)',
        default=0.0,
        help='Discount percentage'
    )

    # Taxes
    tax_ids = fields.Many2many(
        'account.tax',
        relation='account_move_line_tax_rel',
        column1='line_id',
        column2='tax_id',
        string='Taxes',
        help='Taxes applied to this line'
    )

    # Computed Amounts
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_amounts',
        store=True,
        help='Subtotal without taxes'
    )

    price_tax = fields.Float(
        string='Tax Amount',
        compute='_compute_amounts',
        store=True,
        help='Total tax for this line'
    )

    price_total = fields.Float(
        string='Total',
        compute='_compute_amounts',
        store=True,
        help='Total with taxes'
    )

    # Currency
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='move_id.currency_id',
        readonly=True,
        help='Currency'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='move_id.company_id',
        readonly=True,
        help='Company'
    )

    def _compute_amounts(self):
        """Compute line amounts"""
        for line in self:
            # Calculate price with discount
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.price_subtotal = price * line.quantity

            # Calculate taxes
            tax_amount = 0.0
            if line.tax_ids:
                for tax in line.tax_ids:
                    if hasattr(tax, 'amount'):
                        tax_amount += line.price_subtotal * (tax.amount / 100.0)

            line.price_tax = tax_amount
            line.price_total = line.price_subtotal + tax_amount

    def __repr__(self):
        return f"<AccountMoveLine {self.name[:30]}>"
