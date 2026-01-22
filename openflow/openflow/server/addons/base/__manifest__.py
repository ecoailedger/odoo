{
    'name': 'Base',
    'version': '1.0.0',
    'category': 'Hidden',
    'summary': 'Core models and infrastructure for OpenFlow ERP',
    'description': '''
Base Module for OpenFlow ERP
=============================

This module provides the core infrastructure and models required by all other modules:

Core Models (ir.* - Internal Registry):
- ir.model: Model registry and metadata
- ir.model.fields: Field definitions and metadata
- ir.model.access: Model-level access control (CRUD permissions)
- ir.rule: Record-level access rules (row-level security)

Resource Models (res.* - Resources):
- res.users: User accounts and authentication
- res.groups: Security groups for role-based access control
- res.company: Multi-company support and organization structure

This module is automatically installed and cannot be uninstalled.
    ''',
    'author': 'OpenFlow',
    'website': 'https://github.com/openflow/openflow',
    'depends': [],
    'data': [
        'security/ir.model.access.csv',
        'data/res.groups.xml',
        'views/ir_model_views.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'auto_install': True,
    'application': False,
    'license': 'LGPL-3',
}
