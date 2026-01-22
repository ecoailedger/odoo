"""
Stock Models - Locations, Warehouses, Moves, Pickings

Core inventory management models.
"""
from datetime import datetime
from openflow.server.core.orm import Model, fields


class StockLocation(Model):
    """Storage Locations"""
    _name = 'stock.location'
    _description = 'Stock Location'
    _order = 'complete_name'

    name = fields.Char(string='Location Name', required=True, index=True)
    complete_name = fields.Char(string='Full Location Name', compute='_compute_complete_name', store=True)

    location_id = fields.Many2one('stock.location', string='Parent Location', index=True)
    child_ids = fields.One2many('stock.location', 'location_id', string='Contains')

    usage = fields.Selection([
        ('supplier', 'Vendor Location'),
        ('view', 'View'),
        ('internal', 'Internal Location'),
        ('customer', 'Customer Location'),
        ('inventory', 'Inventory Loss'),
        ('production', 'Production'),
        ('transit', 'Transit Location'),
    ], string='Location Type', default='internal', required=True, index=True)

    company_id = fields.Many2one('res.company', string='Company')
    active = fields.Boolean(string='Active', default=True)

    def _compute_complete_name(self):
        """Compute full hierarchical name"""
        for location in self:
            if location.location_id:
                location.complete_name = f"{location.location_id.complete_name}/{location.name}"
            else:
                location.complete_name = location.name


class StockWarehouse(Model):
    """Warehouses"""
    _name = 'stock.warehouse'
    _description = 'Warehouse'
    _order = 'name'

    name = fields.Char(string='Warehouse', required=True, index=True)
    code = fields.Char(string='Short Name', required=True, size=5)

    lot_stock_id = fields.Many2one('stock.location', string='Location Stock', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
    active = fields.Boolean(string='Active', default=True)


class StockMove(Model):
    """Stock Movements"""
    _name = 'stock.move'
    _description = 'Stock Move'
    _order = 'date desc, id desc'

    name = fields.Char(string='Description', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, index=True)
    product_uom_qty = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)

    location_id = fields.Many2one('stock.location', string='Source Location', required=True, index=True)
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', required=True, index=True)

    picking_id = fields.Many2one('stock.picking', string='Transfer', index=True)
    repair_id = fields.Many2one('repair.order', string='Repair Order')

    state = fields.Selection([
        ('draft', 'New'),
        ('waiting', 'Waiting'),
        ('confirmed', 'Waiting Availability'),
        ('assigned', 'Available'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, index=True)

    date = fields.Datetime(string='Date', default=lambda self: datetime.now(), index=True)
    date_done = fields.Datetime(string='Date Done')

    company_id = fields.Many2one('res.company', string='Company')


class StockPicking(Model):
    """Transfer Orders (Pickings)"""
    _name = 'stock.picking'
    _description = 'Transfer'
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', required=True, default='New', index=True)
    partner_id = fields.Many2one('res.partner', string='Partner')

    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type', required=True)
    location_id = fields.Many2one('stock.location', string='Source Location', required=True)
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', required=True)

    move_ids = fields.One2many('stock.move', 'picking_id', string='Stock Moves')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', required=True, index=True)

    date = fields.Datetime(string='Scheduled Date', default=lambda self: datetime.now())
    date_done = fields.Datetime(string='Date of Transfer')

    company_id = fields.Many2one('res.company', string='Company')


class StockPickingType(Model):
    """Picking Types (Receipt, Delivery, Internal)"""
    _name = 'stock.picking.type'
    _description = 'Picking Type'
    _order = 'sequence, name'

    name = fields.Char(string='Operation Type', required=True, translate=True)
    code = fields.Selection([
        ('incoming', 'Receipt'),
        ('outgoing', 'Delivery'),
        ('internal', 'Internal Transfer'),
    ], string='Type of Operation', required=True)

    sequence = fields.Integer(string='Sequence', default=10)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    company_id = fields.Many2one('res.company', string='Company')
    active = fields.Boolean(string='Active', default=True)


class StockQuant(Model):
    """Stock Quantities (Real-time inventory)"""
    _name = 'stock.quant'
    _description = 'Stock Quant'

    product_id = fields.Many2one('product.product', string='Product', required=True, index=True)
    location_id = fields.Many2one('stock.location', string='Location', required=True, index=True)
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial Number')

    quantity = fields.Float(string='Quantity', default=0.0, required=True)
    reserved_quantity = fields.Float(string='Reserved Quantity', default=0.0)

    company_id = fields.Many2one('res.company', string='Company')


class StockProductionLot(Model):
    """Serial Numbers / Lot Numbers"""
    _name = 'stock.production.lot'
    _description = 'Lot/Serial Number'
    _order = 'name desc'

    name = fields.Char(string='Lot/Serial Number', required=True, index=True)
    ref = fields.Char(string='Internal Reference')

    product_id = fields.Many2one('product.product', string='Product', required=True, index=True)
    company_id = fields.Many2one('res.company', string='Company')
