"""
repair.line and repair.fee - Repair Operations and Parts

Tracks labor, operations, parts, and fees for repair orders.
"""
from openflow.server.core.orm import Model, fields


class RepairLine(Model):
    """
    Repair Operations/Labor

    Tracks operations and labor performed during repair.
    """
    _name = 'repair.line'
    _description = 'Repair Operation Line'
    _order = 'repair_id, sequence, id'

    repair_id = fields.Many2one(
        'repair.order',
        string='Repair Order',
        required=True,
        index=True,
        help='Related repair order'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order'
    )

    name = fields.Text(
        string='Description',
        required=True,
        help='Operation description'
    )

    type = fields.Selection(
        selection=[
            ('add', 'Add'),
            ('remove', 'Remove'),
        ],
        string='Type',
        default='add',
        required=True,
        help='Add or remove component'
    )

    # Product (for standardized operations)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='Product for this operation (if standardized)'
    )

    # Quantity and UoM
    product_uom_qty = fields.Float(
        string='Quantity',
        default=1.0,
        required=True,
        help='Quantity'
    )

    product_uom = fields.Many2one(
        'product.uom',
        string='Unit of Measure',
        help='Unit of measure'
    )

    # Pricing
    price_unit = fields.Float(
        string='Unit Price',
        default=0.0,
        required=True,
        help='Price per unit'
    )

    discount = fields.Float(
        string='Discount (%)',
        default=0.0,
        help='Discount percentage'
    )

    tax_ids = fields.Many2many(
        'account.tax',
        relation='repair_line_tax_rel',
        column1='repair_line_id',
        column2='tax_id',
        string='Taxes',
        help='Taxes applied to this line'
    )

    # Computed Amounts
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_price',
        store=True,
        help='Subtotal without taxes'
    )

    price_tax = fields.Float(
        string='Tax',
        compute='_compute_price',
        store=True,
        help='Total tax amount'
    )

    price_total = fields.Float(
        string='Total',
        compute='_compute_price',
        store=True,
        help='Total with taxes'
    )

    # Stock
    location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        help='Location to take parts from'
    )

    location_dest_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        help='Destination location for parts'
    )

    move_id = fields.Many2one(
        'stock.move',
        string='Stock Move',
        help='Related stock move'
    )

    # Invoicing
    invoiced = fields.Boolean(
        string='Invoiced',
        default=False,
        help='Has this line been invoiced'
    )

    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='Invoice Line',
        help='Related invoice line'
    )

    # State
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        help='Operation status'
    )

    def _compute_price(self):
        """Compute line prices"""
        for line in self:
            # Calculate subtotal with discount
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.price_subtotal = price * line.product_uom_qty

            # Simple tax calculation (10% for demo)
            line.price_tax = line.price_subtotal * 0.1

            line.price_total = line.price_subtotal + line.price_tax

    def __repr__(self):
        return f"<RepairLine {self.name[:30]}>"


class RepairFee(Model):
    """
    Repair Parts and Fees

    Tracks parts used and additional fees for repairs.
    """
    _name = 'repair.fee'
    _description = 'Repair Fee/Part Line'
    _order = 'repair_id, sequence, id'

    repair_id = fields.Many2one(
        'repair.order',
        string='Repair Order',
        required=True,
        index=True,
        help='Related repair order'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order'
    )

    name = fields.Text(
        string='Description',
        required=True,
        help='Part or fee description'
    )

    # Product
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        help='Part or service'
    )

    # Quantity and UoM
    product_uom_qty = fields.Float(
        string='Quantity',
        default=1.0,
        required=True,
        help='Quantity'
    )

    product_uom = fields.Many2one(
        'product.uom',
        string='Unit of Measure',
        help='Unit of measure'
    )

    # Pricing
    price_unit = fields.Float(
        string='Unit Price',
        default=0.0,
        required=True,
        help='Price per unit'
    )

    discount = fields.Float(
        string='Discount (%)',
        default=0.0,
        help='Discount percentage'
    )

    tax_ids = fields.Many2many(
        'account.tax',
        relation='repair_fee_tax_rel',
        column1='repair_fee_id',
        column2='tax_id',
        string='Taxes',
        help='Taxes applied to this line'
    )

    # Computed Amounts
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_price',
        store=True,
        help='Subtotal without taxes'
    )

    price_tax = fields.Float(
        string='Tax',
        compute='_compute_price',
        store=True,
        help='Total tax amount'
    )

    price_total = fields.Float(
        string='Total',
        compute='_compute_price',
        store=True,
        help='Total with taxes'
    )

    # Invoicing
    invoiced = fields.Boolean(
        string='Invoiced',
        default=False,
        help='Has this fee been invoiced'
    )

    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='Invoice Line',
        help='Related invoice line'
    )

    def _compute_price(self):
        """Compute fee prices"""
        for fee in self:
            # Calculate subtotal with discount
            price = fee.price_unit * (1 - (fee.discount or 0.0) / 100.0)
            fee.price_subtotal = price * fee.product_uom_qty

            # Simple tax calculation (10% for demo)
            fee.price_tax = fee.price_subtotal * 0.1

            fee.price_total = fee.price_subtotal + fee.price_tax

    def __repr__(self):
        return f"<RepairFee {self.name[:30]}>"
