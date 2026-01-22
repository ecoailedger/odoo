"""
OpenFlow ORM - Custom ORM layer for ERP system

This ORM provides:
- Model definition with field descriptors
- RecordSet API for record manipulation
- Domain expression language for queries
- Automatic schema management
- Model inheritance support

Example usage:

    from openflow.server.core.orm import Model, fields

    class Partner(Model):
        _name = 'res.partner'
        _description = 'Business Partner'

        name = fields.Char(string='Name', required=True)
        email = fields.Char(string='Email')
        active = fields.Boolean(string='Active', default=True)
        phone = fields.Char(string='Phone')
        country_id = fields.Many2one('res.country', string='Country')
        child_ids = fields.One2many('res.partner', 'parent_id', string='Contacts')

    # Usage with environment
    env = get_env(session, user)
    partner = env['res.partner'].search([('name', '=', 'John')])[0]
    partner.write({'email': 'john@example.com'})
"""

# Field types
from .fields import (
    Field,
    Char,
    Text,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    Binary,
    Selection,
    Many2one,
    One2many,
    Many2many,
    FIELD_TYPES,
)

# Model and RecordSet
from .models import Model, ModelMetaclass
from .recordset import RecordSet

# Registry and Environment
from .registry import ModelRegistry, Environment, registry, get_env

# Domain expressions
from .domain import (
    Domain,
    DomainLeaf,
    DomainOperator,
    LogicalOperator,
    DomainParser,
    DomainNode,
    normalize_domain,
    domain_to_sql,
)


# Convenience namespace for fields
class fields:
    """Namespace for field types (similar to Odoo's fields module)"""
    Char = Char
    Text = Text
    Integer = Integer
    Float = Float
    Boolean = Boolean
    Date = Date
    DateTime = DateTime
    Binary = Binary
    Selection = Selection
    Many2one = Many2one
    One2many = One2many
    Many2many = Many2many


__all__ = [
    # Field types
    'Field',
    'Char',
    'Text',
    'Integer',
    'Float',
    'Boolean',
    'Date',
    'DateTime',
    'Binary',
    'Selection',
    'Many2one',
    'One2many',
    'Many2many',
    'FIELD_TYPES',
    'fields',
    # Model classes
    'Model',
    'ModelMetaclass',
    'RecordSet',
    # Registry
    'ModelRegistry',
    'Environment',
    'registry',
    'get_env',
    # Domain
    'Domain',
    'DomainLeaf',
    'DomainOperator',
    'LogicalOperator',
    'DomainParser',
    'DomainNode',
    'normalize_domain',
    'domain_to_sql',
]
