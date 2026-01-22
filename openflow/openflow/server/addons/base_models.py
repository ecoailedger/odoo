"""
Base models demonstrating ORM usage

This module contains example models showing how to use the OpenFlow ORM:
- Basic fields
- Relational fields
- Computed fields
- Model inheritance
- Business logic methods
"""
from datetime import datetime, date
from typing import List

from openflow.server.core.orm import Model, fields


class Country(Model):
    """Country model - simple model with basic fields"""

    _name = 'res.country'
    _description = 'Country'
    _order = 'name'

    name = fields.Char(string='Name', required=True, index=True)
    code = fields.Char(string='Code', size=2, required=True, index=True)
    phone_code = fields.Integer(string='Phone Code')
    active = fields.Boolean(string='Active', default=True)


class PartnerCategory(Model):
    """Partner category for many2many relationships"""

    _name = 'res.partner.category'
    _description = 'Partner Category'
    _order = 'name'

    name = fields.Char(string='Name', required=True, index=True)
    color = fields.Integer(string='Color Index')
    parent_id = fields.Many2one('res.partner.category', string='Parent Category')
    child_ids = fields.One2many('res.partner.category', 'parent_id', string='Child Categories')
    active = fields.Boolean(string='Active', default=True)


class Partner(Model):
    """
    Business Partner model

    Demonstrates:
    - All field types
    - Relational fields
    - Computed fields
    - Default values
    - Business methods
    """

    _name = 'res.partner'
    _description = 'Business Partner'
    _order = 'name'
    _rec_name = 'name'

    # Basic fields
    name = fields.Char(string='Name', required=True, index=True)
    ref = fields.Char(string='Reference', index=True)
    active = fields.Boolean(string='Active', default=True)

    # Contact information
    email = fields.Char(string='Email', index=True)
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    website = fields.Char(string='Website')

    # Address fields
    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street 2')
    city = fields.Char(string='City')
    state = fields.Char(string='State')
    zip = fields.Char(string='ZIP')
    country_id = fields.Many2one('res.country', string='Country')

    # Type and classification
    company_type = fields.Selection(
        selection=[
            ('person', 'Individual'),
            ('company', 'Company'),
        ],
        string='Company Type',
        default='person',
        required=True
    )

    # Additional info
    comment = fields.Text(string='Notes')
    image = fields.Binary(string='Image', attachment=True)

    # Dates
    date = fields.Date(string='Date')
    created_at = fields.DateTime(string='Created At', default=lambda self: datetime.now())

    # Relational fields
    parent_id = fields.Many2one('res.partner', string='Related Company', index=True)
    child_ids = fields.One2many('res.partner', 'parent_id', string='Contacts')

    category_ids = fields.Many2many(
        'res.partner.category',
        relation='res_partner_category_rel',
        column1='partner_id',
        column2='category_id',
        string='Tags'
    )

    # Computed fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        depends=['name', 'ref']
    )

    is_company = fields.Boolean(
        string='Is a Company',
        compute='_compute_is_company',
        store=True,
        depends=['company_type']
    )

    # Related fields
    parent_name = fields.Char(
        string='Parent Company Name',
        related='parent_id.name',
        readonly=True
    )

    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            if record.ref:
                record.display_name = f"[{record.ref}] {record.name}"
            else:
                record.display_name = record.name

    def _compute_is_company(self):
        """Compute is_company flag"""
        for record in self:
            record.is_company = record.company_type == 'company'


class Product(Model):
    """
    Product model

    Demonstrates:
    - Numeric fields
    - Selection fields
    - Constraints
    """

    _name = 'product.product'
    _description = 'Product'
    _order = 'name'

    name = fields.Char(string='Product Name', required=True, index=True)
    code = fields.Char(string='Internal Reference', index=True)
    active = fields.Boolean(string='Active', default=True)

    # Product type
    type = fields.Selection(
        selection=[
            ('product', 'Storable Product'),
            ('consu', 'Consumable'),
            ('service', 'Service'),
        ],
        string='Product Type',
        default='product',
        required=True
    )

    # Pricing
    list_price = fields.Float(
        string='Sales Price',
        digits=(10, 2),
        default=0.0,
        required=True
    )

    standard_price = fields.Float(
        string='Cost',
        digits=(10, 2),
        default=0.0
    )

    # Inventory
    qty_available = fields.Float(
        string='Quantity On Hand',
        digits=(10, 2),
        default=0.0
    )

    # Description
    description = fields.Text(string='Description')
    description_sale = fields.Text(string='Sales Description')

    # Image
    image = fields.Binary(string='Image', attachment=True)

    # Relational
    category_id = fields.Many2one('product.category', string='Category', required=True)

    # Computed
    margin = fields.Float(
        string='Margin',
        compute='_compute_margin',
        store=True,
        depends=['list_price', 'standard_price']
    )

    def _compute_margin(self):
        """Compute product margin"""
        for record in self:
            if record.list_price:
                record.margin = ((record.list_price - record.standard_price) /
                                record.list_price * 100)
            else:
                record.margin = 0.0


class ProductCategory(Model):
    """Product category with hierarchy"""

    _name = 'product.category'
    _description = 'Product Category'
    _order = 'name'

    name = fields.Char(string='Name', required=True, index=True)
    parent_id = fields.Many2one('product.category', string='Parent Category', index=True)
    child_ids = fields.One2many('product.category', 'parent_id', string='Child Categories')

    # Computed full path
    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        store=True,
        depends=['name', 'parent_id', 'parent_id.complete_name']
    )

    def _compute_complete_name(self):
        """Compute full hierarchical name"""
        for record in self:
            if record.parent_id:
                record.complete_name = f"{record.parent_id.complete_name} / {record.name}"
            else:
                record.complete_name = record.name


class SaleOrder(Model):
    """
    Sales Order model

    Demonstrates:
    - Document workflow
    - One2many relationships (order lines)
    - Computed totals
    - Business methods
    """

    _name = 'sale.order'
    _description = 'Sales Order'
    _order = 'date_order desc, id desc'

    name = fields.Char(string='Order Reference', required=True, index=True, default='New')

    # Dates
    date_order = fields.DateTime(
        string='Order Date',
        required=True,
        default=lambda self: datetime.now(),
        index=True
    )

    # Customer
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        index=True
    )

    # Related customer fields
    partner_email = fields.Char(
        string='Customer Email',
        related='partner_id.email',
        readonly=True
    )

    # Workflow state
    state = fields.Selection(
        selection=[
            ('draft', 'Quotation'),
            ('sent', 'Quotation Sent'),
            ('sale', 'Sales Order'),
            ('done', 'Locked'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        index=True
    )

    # Order lines
    order_line_ids = fields.One2many(
        'sale.order.line',
        'order_id',
        string='Order Lines'
    )

    # Notes
    note = fields.Text(string='Terms and Conditions')

    # Computed amounts
    amount_untaxed = fields.Float(
        string='Untaxed Amount',
        compute='_compute_amounts',
        store=True,
        depends=['order_line_ids', 'order_line_ids.price_subtotal']
    )

    amount_tax = fields.Float(
        string='Taxes',
        compute='_compute_amounts',
        store=True,
        depends=['order_line_ids', 'order_line_ids.price_tax']
    )

    amount_total = fields.Float(
        string='Total',
        compute='_compute_amounts',
        store=True,
        depends=['amount_untaxed', 'amount_tax']
    )

    def _compute_amounts(self):
        """Compute order amounts"""
        for order in self:
            amount_untaxed = 0.0
            amount_tax = 0.0

            for line in order.order_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = amount_untaxed + amount_tax


class SaleOrderLine(Model):
    """Sales Order Line"""

    _name = 'sale.order.line'
    _description = 'Sales Order Line'
    _order = 'order_id, sequence, id'

    order_id = fields.Many2one('sale.order', string='Order', required=True, index=True)
    sequence = fields.Integer(string='Sequence', default=10)

    # Product
    product_id = fields.Many2one('product.product', string='Product', required=True)

    # Description
    name = fields.Text(string='Description', required=True)

    # Quantities and pricing
    product_uom_qty = fields.Float(
        string='Quantity',
        digits=(10, 2),
        default=1.0,
        required=True
    )

    price_unit = fields.Float(
        string='Unit Price',
        digits=(10, 2),
        default=0.0,
        required=True
    )

    discount = fields.Float(
        string='Discount (%)',
        digits=(10, 2),
        default=0.0
    )

    # Computed amounts
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_amount',
        store=True,
        depends=['product_uom_qty', 'price_unit', 'discount']
    )

    price_tax = fields.Float(
        string='Tax',
        compute='_compute_amount',
        store=True,
        depends=['price_subtotal']
    )

    price_total = fields.Float(
        string='Total',
        compute='_compute_amount',
        store=True,
        depends=['price_subtotal', 'price_tax']
    )

    def _compute_amount(self):
        """Compute line amounts"""
        for line in self:
            # Compute subtotal with discount
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.price_subtotal = price * line.product_uom_qty

            # Simple tax computation (would be more complex in real system)
            line.price_tax = line.price_subtotal * 0.1  # 10% tax

            line.price_total = line.price_subtotal + line.price_tax
