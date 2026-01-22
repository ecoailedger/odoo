{
    'name': 'Inventory',
    'version': '1.0.0',
    'category': 'Inventory',
    'summary': 'Inventory and Stock Management',
    'description': '''
Stock/Inventory Module - Basic Inventory Management
====================================================

Simplified inventory management for repairs integration:

Features:
- **Products**: Product catalog with tracking options
- **Locations**: Warehouse locations for stock organization
- **Warehouses**: Physical warehouse management
- **Stock Moves**: Track product movements
- **Pickings**: Grouped stock operations (receipts, deliveries)
- **Quants**: Real-time stock levels
- **Serial Numbers**: Lot/serial number tracking

Components:
- product.template: Product templates
- product.product: Product variants
- product.uom: Units of measure
- stock.location: Storage locations
- stock.warehouse: Warehouses
- stock.move: Stock movements
- stock.picking: Grouped operations
- stock.quant: Stock quantities
- stock.production.lot: Serial/lot numbers

This is a simplified version focused on supporting repair operations.
    ''',
    'author': 'OpenFlow',
    'website': 'https://github.com/openflow/openflow',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
