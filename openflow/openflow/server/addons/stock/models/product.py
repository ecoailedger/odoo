"""
Product Models - Products and Templates

Product catalog with inventory tracking.
"""
from openflow.server.core.orm import Model, fields


class ProductTemplate(Model):
    """Product Templates"""
    _name = 'product.template'
    _description = 'Product Template'
    _order = 'name'

    name = fields.Char(string='Product Name', required=True, index=True)
    description = fields.Text(string='Description')
    description_sale = fields.Text(string='Sales Description')

    type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),
        ('product', 'Storable Product'),
    ], string='Product Type', default='consu', required=True)

    categ_id = fields.Many2one('product.category', string='Category', required=True)

    list_price = fields.Float(string='Sales Price', default=0.0)
    standard_price = fields.Float(string='Cost', default=0.0)

    uom_id = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    uom_po_id = fields.Many2one('product.uom', string='Purchase UoM')

    tracking = fields.Selection([
        ('none', 'No Tracking'),
        ('lot', 'By Lots'),
        ('serial', 'By Unique Serial Number'),
    ], string='Tracking', default='none', required=True)

    active = fields.Boolean(string='Active', default=True)
    image = fields.Binary(string='Image', attachment=True)


class ProductProduct(Model):
    """Product Variants"""
    _name = 'product.product'
    _description = 'Product'
    _order = 'default_code, name'

    product_tmpl_id = fields.Many2one('product.template', string='Product Template', required=True)
    name = fields.Char(string='Name', related='product_tmpl_id.name', readonly=True)

    default_code = fields.Char(string='Internal Reference', index=True)
    barcode = fields.Char(string='Barcode', index=True)

    qty_available = fields.Float(string='Quantity On Hand', compute='_compute_quantities')
    virtual_available = fields.Float(string='Forecast Quantity', compute='_compute_quantities')

    active = fields.Boolean(string='Active', default=True)

    def _compute_quantities(self):
        """Compute stock quantities from quants"""
        for product in self:
            # Simplified - would query stock.quant in full implementation
            product.qty_available = 0.0
            product.virtual_available = 0.0


class ProductCategory(Model):
    """Product Categories"""
    _name = 'product.category'
    _description = 'Product Category'
    _order = 'complete_name'

    name = fields.Char(string='Category Name', required=True, index=True)
    parent_id = fields.Many2one('product.category', string='Parent Category', index=True)
    child_ids = fields.One2many('product.category', 'parent_id', string='Child Categories')

    complete_name = fields.Char(string='Complete Name', compute='_compute_complete_name', store=True)

    def _compute_complete_name(self):
        """Compute hierarchical name"""
        for category in self:
            if category.parent_id:
                category.complete_name = f"{category.parent_id.complete_name} / {category.name}"
            else:
                category.complete_name = category.name


class ProductUom(Model):
    """Units of Measure"""
    _name = 'product.uom'
    _description = 'Unit of Measure'
    _order = 'name'

    name = fields.Char(string='Unit of Measure', required=True, translate=True)
    category_id = fields.Many2one('product.uom.category', string='Category', required=True)
    factor = fields.Float(string='Ratio', default=1.0, required=True)
    rounding = fields.Float(string='Rounding Precision', default=0.01)
    active = fields.Boolean(string='Active', default=True)


class ProductUomCategory(Model):
    """UoM Categories"""
    _name = 'product.uom.category'
    _description = 'UoM Category'

    name = fields.Char(string='Category', required=True)
