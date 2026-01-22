# OpenFlow ORM

A custom ORM (Object-Relational Mapping) layer for the OpenFlow ERP system, inspired by Odoo's ORM design.

## Features

- **Model Definition**: Define database models as Python classes with field descriptors
- **Field Types**: Support for all common data types (Char, Text, Integer, Float, Boolean, Date, DateTime, Binary, Selection)
- **Relational Fields**: Many2one, One2many, and Many2many relationships
- **RecordSet API**: Powerful API for working with collections of records
- **Domain Expressions**: Flexible search language using Polish notation
- **CRUD Operations**: Create, read, update, delete operations with clean API
- **Field Features**: Default values, computed fields, related fields, required/optional validation
- **Model Inheritance**: Classical and prototype inheritance patterns

## Quick Start

### Defining a Model

```python
from openflow.server.core.orm import Model, fields

class Partner(Model):
    _name = 'res.partner'
    _description = 'Business Partner'
    _order = 'name'

    name = fields.Char(string='Name', required=True, index=True)
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    active = fields.Boolean(string='Active', default=True)
    company_type = fields.Selection(
        selection=[('person', 'Individual'), ('company', 'Company')],
        string='Type',
        default='person'
    )
    comment = fields.Text(string='Notes')

    # Relational fields
    country_id = fields.Many2one('res.country', string='Country')
    child_ids = fields.One2many('res.partner', 'parent_id', string='Contacts')
    parent_id = fields.Many2one('res.partner', string='Related Company')
```

### CRUD Operations

```python
# Get environment (with database session)
from openflow.server.core.orm import get_env

env = get_env(session=db_session, user=current_user)

# Create records
partner = await env['res.partner'].create({
    'name': 'John Doe',
    'email': 'john@example.com',
    'phone': '+1234567890',
    'active': True
})

# Read records
partner_data = await partner.read(['name', 'email', 'phone'])
print(partner_data)  # [{'id': 1, 'name': 'John Doe', 'email': 'john@example.com', ...}]

# Update records
await partner.write({
    'email': 'newemail@example.com',
    'phone': '+9876543210'
})

# Delete records
await partner.unlink()
```

### Searching Records

#### Simple Search

```python
# Find all active partners
partners = await env['res.partner'].search([('active', '=', True)])

# Find partners with name containing 'John'
partners = await env['res.partner'].search([('name', 'ilike', '%John%')])

# With limit and offset
partners = await env['res.partner'].search(
    [('active', '=', True)],
    limit=10,
    offset=0,
    order='name ASC'
)
```

#### Domain Expressions

The ORM uses Polish notation for complex queries:

```python
# AND: Find active partners named John
domain = ['&', ('active', '=', True), ('name', '=', 'John')]
partners = await env['res.partner'].search(domain)

# OR: Find partners in draft or open state
domain = ['|', ('state', '=', 'draft'), ('state', '=', 'open')]
partners = await env['res.partner'].search(domain)

# NOT: Find inactive partners
domain = ['!', ('active', '=', True)]
partners = await env['res.partner'].search(domain)

# Complex: Active partners named John OR with email ending in @example.com
domain = [
    '&',
    ('active', '=', True),
    '|',
    ('name', 'ilike', '%John%'),
    ('email', 'like', '%@example.com')
]
partners = await env['res.partner'].search(domain)

# Implicit AND (multiple conditions without operators)
domain = [('active', '=', True), ('company_type', '=', 'company')]
# Automatically converted to: ['&', ('active', '=', True), ('company_type', '=', 'company')]
```

#### Supported Operators

- `=`: Equal
- `!=`: Not equal
- `>`: Greater than
- `<`: Less than
- `>=`: Greater than or equal
- `<=`: Less than or equal
- `like`: SQL LIKE (case-sensitive)
- `ilike`: SQL ILIKE (case-insensitive)
- `in`: Value in list
- `not in`: Value not in list
- `child_of`: Hierarchical child lookup (coming soon)
- `parent_of`: Hierarchical parent lookup (coming soon)

### RecordSet Operations

RecordSets are immutable collections of records with powerful operations:

```python
# Get recordset
partners = await env['res.partner'].search([('active', '=', True)])

# Iteration
for partner in partners:
    print(partner.name)

# Indexing
first_partner = partners[0]
last_three = partners[-3:]

# Set operations
partners1 = await env['res.partner'].search([('country_id', '=', 1)])
partners2 = await env['res.partner'].search([('country_id', '=', 2)])

# Union
all_partners = partners1 + partners2  # or partners1 | partners2

# Difference
only_country1 = partners1 - partners2

# Intersection
common = partners1 & partners2

# Filtering
def is_company(partner):
    return partner.company_type == 'company'

companies = partners.filtered(is_company)

# Sorting
sorted_partners = partners.sorted(key=lambda p: p.name)
sorted_reverse = partners.sorted(key=lambda p: p.name, reverse=True)

# Mapping
names = partners.mapped('name')
emails = partners.mapped('email')

# Ensure single record
partner = partners[0].ensure_one()  # Raises error if not exactly one
```

### Field Types

#### Basic Fields

```python
name = fields.Char(string='Name', size=100, required=True)
description = fields.Text(string='Description')
age = fields.Integer(string='Age', default=0)
price = fields.Float(string='Price', digits=(10, 2))
active = fields.Boolean(string='Active', default=True)
birth_date = fields.Date(string='Birth Date')
created_at = fields.DateTime(string='Created At')
attachment = fields.Binary(string='Attachment')
state = fields.Selection(
    selection=[('draft', 'Draft'), ('done', 'Done')],
    string='State'
)
```

#### Relational Fields

```python
# Many2one (many records can link to one)
country_id = fields.Many2one(
    'res.country',
    string='Country',
    ondelete='restrict'  # 'set null', 'restrict', 'cascade'
)

# One2many (inverse of Many2one)
child_ids = fields.One2many(
    'res.partner',
    'parent_id',  # The Many2one field on res.partner
    string='Contacts'
)

# Many2many (many-to-many relationship)
category_ids = fields.Many2many(
    'res.partner.category',
    relation='partner_category_rel',  # Junction table name
    column1='partner_id',
    column2='category_id',
    string='Categories'
)
```

### Field Properties

#### Default Values

```python
# Static default
active = fields.Boolean(default=True)

# Callable default
def _default_date():
    return datetime.now()

created_at = fields.DateTime(default=_default_date)
```

#### Computed Fields

```python
class Partner(Model):
    _name = 'res.partner'

    first_name = fields.Char()
    last_name = fields.Char()

    # Computed field
    full_name = fields.Char(
        string='Full Name',
        compute='_compute_full_name',
        store=True,  # Store in database
        depends=['first_name', 'last_name']  # Recompute when these change
    )

    def _compute_full_name(self):
        for record in self:
            record.full_name = f"{record.first_name} {record.last_name}"
```

#### Related Fields

```python
class Order(Model):
    _name = 'sale.order'

    partner_id = fields.Many2one('res.partner', string='Customer')

    # Related field - automatically computed
    partner_email = fields.Char(
        string='Customer Email',
        related='partner_id.email',
        readonly=True
    )
```

#### Field Validation

```python
email = fields.Char(
    string='Email',
    required=True,  # Must have value
    readonly=False,  # Can be written
    index=True,  # Create database index
    copy=True,  # Include when copying record
    help='Email address for notifications'
)
```

### Model Inheritance

#### Classical Inheritance

```python
class BaseModel(Model):
    _name = 'base.model'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

class ExtendedModel(BaseModel):
    _name = 'extended.model'

    # Inherits fields from BaseModel
    description = fields.Text()
```

#### Prototype Inheritance (Extension)

```python
# Extend existing model
class PartnerExtension(Model):
    _name = 'res.partner'  # Same name as original
    _inherit = 'res.partner'  # Specify parent

    # Add new fields to res.partner
    tax_id = fields.Char(string='Tax ID')
    credit_limit = fields.Float(string='Credit Limit')
```

### Model Configuration

```python
class MyModel(Model):
    _name = 'my.model'  # Unique model identifier (required)
    _table = 'custom_table_name'  # Database table name (optional, auto-generated)
    _description = 'My Model'  # Human-readable description
    _order = 'name, id desc'  # Default ordering for searches
    _rec_name = 'name'  # Field to use for record display name
    _inherit = 'base.model'  # Parent model(s) for inheritance
    _inherits = {'res.partner': 'partner_id'}  # Delegation inheritance
```

## Architecture

### Components

1. **Fields** (`fields.py`): Field descriptors for model attributes
2. **Models** (`models.py`): Base Model class with metaclass
3. **RecordSet** (`recordset.py`): Collection wrapper for records
4. **Registry** (`registry.py`): Model registration and environment
5. **Domain** (`domain.py`): Search expression parser

### Database Integration

The ORM integrates with SQLAlchemy's async engine:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from openflow.server.core.orm import get_env

async def example(session: AsyncSession):
    env = get_env(session=session, user=current_user)

    # All ORM operations use this session
    partner = await env['res.partner'].create({'name': 'Test'})
    await session.commit()  # Handled automatically by environment
```

## Testing

Comprehensive tests are provided:

```bash
# Run all ORM tests
pytest openflow/tests/test_orm_*.py -v

# Run specific test modules
pytest openflow/tests/test_orm_fields.py -v
pytest openflow/tests/test_orm_domain.py -v
pytest openflow/tests/test_orm_models.py -v
```

## Best Practices

1. **Model Names**: Use dotted notation (e.g., `res.partner`, `sale.order`)
2. **Field Names**: Use snake_case (e.g., `email_address`, `phone_number`)
3. **Required Fields**: Mark essential fields as `required=True`
4. **Indexes**: Add indexes to frequently searched fields
5. **Defaults**: Provide sensible defaults for boolean and selection fields
6. **Computed Fields**: Use `store=True` for frequently accessed computed values
7. **Validation**: Implement validation in model methods
8. **Transactions**: Use environment's session for transaction management

## Roadmap

- [ ] Automatic database migration
- [ ] Model constraints (SQL and Python)
- [ ] Field access control (field-level security)
- [ ] Hierarchical queries (child_of, parent_of operators)
- [ ] External ID support (XML IDs)
- [ ] Record rules (row-level security)
- [ ] Audit trail (tracking field changes)
- [ ] Multi-company support
- [ ] Translations for translatable fields

## Examples

See `openflow/server/addons/` for example models demonstrating ORM usage.
