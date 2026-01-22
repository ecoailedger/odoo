# XML-Based View System

A comprehensive view system for defining UI layouts using XML, inspired by Odoo's view architecture.

## Overview

The view system provides a declarative way to define user interfaces using XML. Views are stored in the database and can be inherited and extended by other modules.

## Components

### 1. View Parser (`openflow.server.core.views.parser`)

Parses XML view definitions into Python dictionary structures.

```python
from openflow.server.core.views.parser import ViewParser

parser = ViewParser(env)
parsed_view = await parser.parse_view(view_record)
```

### 2. View Inheritance (`openflow.server.core.views.inheritance`)

Handles view inheritance using XPath expressions to locate and modify elements.

```python
from openflow.server.core.views.inheritance import ViewInheritance

inheritance = ViewInheritance()
modified_arch = await inheritance.apply_inheritance(base_arch, inherit_specs)
```

### 3. View Validator (`openflow.server.core.views.validator`)

Validates view definitions against model schemas to ensure fields exist and widgets are compatible.

```python
from openflow.server.core.views.validator import ViewValidator

validator = ViewValidator(env)
errors = await validator.validate_view(view_def)
```

### 4. View Renderer (`openflow.server.core.views.renderer`)

Renders view definitions to JSON for frontend consumption.

```python
from openflow.server.core.views.renderer import ViewRenderer

renderer = ViewRenderer(env)
json_view = renderer.render_to_json(parsed_view)
```

## View Types

### 1. Form View

Detail view for displaying and editing a single record.

```xml
<form string="Partner">
    <header>
        <button name="action_confirm" type="object" string="Confirm"/>
        <field name="state" widget="statusbar"/>
    </header>
    <sheet>
        <group>
            <field name="name" required="1"/>
            <field name="email" widget="email"/>
        </group>
        <notebook>
            <page string="Details">
                <field name="description"/>
            </page>
        </notebook>
    </sheet>
</form>
```

**Form Elements:**
- `<header>`: Action buttons and statusbar
- `<sheet>`: Main content area
- `<group>`: Layout container for fields (2 columns by default)
- `<notebook>`: Tabbed interface
- `<page>`: Tab within notebook
- `<field>`: Display/edit a model field
- `<button>`: Action button
- `<separator>`: Visual separator
- `<label>`: Text label

### 2. Tree/List View

Tabular view for displaying multiple records.

```xml
<tree string="Partners"
      editable="bottom"
      decoration-danger="state=='blocked'"
      decoration-success="state=='approved'">
    <field name="name"/>
    <field name="email"/>
    <field name="phone"/>
    <button name="action_approve" type="object" string="Approve"/>
</tree>
```

**Features:**
- `editable`: Make tree inline-editable ('top', 'bottom', or None)
- `decoration-*`: Conditional row styling (danger, success, info, warning, muted)
- Buttons for row actions
- Field-level attributes (invisible, readonly, required)

### 3. Kanban View

Card-based view for visual organization.

```xml
<kanban default_group_by="state" quick_create="true">
    <field name="name"/>
    <field name="state"/>
    <field name="color"/>
    <templates>
        <t t-name="kanban-box">
            <div class="oe_kanban_card">
                <strong><field name="name"/></strong>
                <div><field name="email"/></div>
            </div>
        </t>
    </templates>
</kanban>
```

**Features:**
- `default_group_by`: Field to group cards by
- `quick_create`: Enable quick card creation
- QWeb templates for card rendering
- Drag-and-drop support

### 4. Search View

Defines search fields, filters, and group-by options.

```xml
<search string="Search Partners">
    <field name="name" filter_domain="['|', ('name', 'ilike', self), ('email', 'ilike', self)]"/>
    <field name="email"/>
    <separator/>
    <filter name="customers" string="Customers" domain="[('is_customer', '=', True)]"/>
    <filter name="suppliers" string="Suppliers" domain="[('is_supplier', '=', True)]"/>
    <group expand="0" string="Group By">
        <filter name="group_country" string="Country" context="{'group_by': 'country_id'}"/>
    </group>
</search>
```

**Components:**
- `<field>`: Searchable field
- `<filter>`: Predefined filter with domain
- `<group>`: Group-by options
- `<separator>`: Visual separator

### 5. Calendar View

Calendar display for date-based records.

```xml
<calendar string="Meetings"
          date_start="start_date"
          date_stop="end_date"
          color="partner_id"
          mode="month">
    <field name="name"/>
    <field name="partner_id"/>
</calendar>
```

**Attributes:**
- `date_start`: Required start date field
- `date_stop`: Optional end date field
- `date_delay`: Alternative to date_stop (duration field)
- `color`: Field for color coding
- `mode`: Default view mode (day, week, month)

### 6. Pivot View

Pivot table for data analysis and aggregation.

```xml
<pivot string="Sales Analysis" display_quantity="true">
    <field name="partner_id" type="row"/>
    <field name="state" type="col"/>
    <field name="amount_total" type="measure"/>
</pivot>
```

**Field Types:**
- `type="row"`: Row dimension
- `type="col"`: Column dimension
- `type="measure"`: Aggregated measure

### 7. Graph View

Charts and visualizations.

```xml
<graph string="Sales Chart" type="bar" stacked="True">
    <field name="date_order" type="row" interval="month"/>
    <field name="amount_total" type="measure"/>
</graph>
```

**Chart Types:**
- `bar`: Bar chart
- `line`: Line chart
- `pie`: Pie chart

**Attributes:**
- `stacked`: Stack bars/lines
- `interval`: Time grouping (day, week, month, quarter, year)

## View Inheritance

Views can inherit from other views using XPath expressions.

```xml
<record id="view_partner_form_inherit" model="ir.ui.view">
    <field name="name">res.partner.form.inherit</field>
    <field name="model">res.partner</field>
    <field name="inherit_id" ref="view_partner_form"/>
    <field name="arch" type="xml">
        <!-- Add field after email -->
        <xpath expr="//field[@name='email']" position="after">
            <field name="vat"/>
        </xpath>

        <!-- Add new page to notebook -->
        <xpath expr="//notebook" position="inside">
            <page string="Extra Info">
                <field name="extra_field"/>
            </page>
        </xpath>

        <!-- Modify field attributes -->
        <xpath expr="//field[@name='phone']" position="attributes">
            <attribute name="required">1</attribute>
        </xpath>

        <!-- Replace field -->
        <xpath expr="//field[@name='category_id']" position="replace">
            <field name="category_id" widget="many2many_checkboxes"/>
        </xpath>
    </field>
</record>
```

### XPath Positions

- `before`: Insert before matched element
- `after`: Insert after matched element
- `inside`: Insert inside matched element (default)
- `replace`: Replace matched element
- `attributes`: Modify attributes of matched element

### Common XPath Expressions

```xml
<!-- Find field by name -->
//field[@name='email']

<!-- Find all fields -->
//field

<!-- Find group elements -->
//group

<!-- Find page by string -->
//page[@string='Details']

<!-- Find notebook -->
//notebook
```

## Field Widgets

Different widgets for field display:

### Char Field Widgets
- `char`: Default text input
- `email`: Email input with validation
- `phone`: Phone number input
- `url`: URL input with validation
- `badge`: Display as badge/tag

### Text Field Widgets
- `text`: Plain text area
- `html`: Rich text editor

### Numeric Field Widgets
- `integer`: Integer input
- `float`: Float input
- `monetary`: Currency display
- `percentage`: Percentage display
- `progressbar`: Progress bar

### Boolean Field Widgets
- `boolean`: Checkbox
- `toggle`: Toggle switch

### Date Field Widgets
- `date`: Date picker
- `datetime`: Date and time picker
- `remaining_days`: Show remaining days

### Relational Field Widgets
- `many2one`: Dropdown with search
- `selection`: Simple dropdown
- `radio`: Radio buttons
- `many2many`: Multiple selection
- `many2many_tags`: Tag-style display
- `many2many_checkboxes`: Checkbox list

### Selection Field Widgets
- `selection`: Dropdown
- `radio`: Radio buttons
- `badge`: Badge display
- `statusbar`: Workflow status bar

### Binary Field Widgets
- `binary`: File download/upload
- `image`: Image display/upload
- `pdf_viewer`: PDF viewer

## Field Attributes

Common field attributes:

```xml
<field name="email"
       widget="email"
       required="1"
       readonly="1"
       invisible="state != 'draft'"
       domain="[('active', '=', True)]"
       context="{'default_country_id': country_id}"
       help="Contact email address"
       placeholder="email@example.com"
       class="oe_inline"
       string="Email Address"/>
```

- `name`: Field name (required)
- `widget`: Widget type
- `required`: Make field required
- `readonly`: Make field read-only
- `invisible`: Hide field (domain expression)
- `domain`: Filter domain for relational fields
- `context`: Context values for relational fields
- `help`: Help tooltip text
- `placeholder`: Placeholder text
- `class`: CSS classes
- `string`: Override field label

## Tree View Decorations

Conditional row styling:

```xml
<tree decoration-danger="state=='blocked'"
      decoration-success="state=='approved'"
      decoration-info="state=='pending'"
      decoration-warning="amount > 1000"
      decoration-muted="active==False">
    ...
</tree>
```

Available decorations:
- `decoration-danger`: Red (errors, blocked)
- `decoration-success`: Green (approved, done)
- `decoration-info`: Blue (information)
- `decoration-warning`: Orange (warnings)
- `decoration-muted`: Gray (inactive)

## Usage Example

### 1. Define View in XML

```xml
<record id="view_sale_order_form" model="ir.ui.view">
    <field name="name">sale.order.form</field>
    <field name="model">sale.order</field>
    <field name="type">form</field>
    <field name="arch" type="xml">
        <form string="Sales Order">
            <header>
                <button name="action_confirm" type="object" string="Confirm"
                        class="oe_highlight" attrs="{'invisible': [('state', '!=', 'draft')]}"/>
                <field name="state" widget="statusbar" statusbar_visible="draft,sent,sale,done"/>
            </header>
            <sheet>
                <div class="oe_title">
                    <h1><field name="name"/></h1>
                </div>
                <group>
                    <group>
                        <field name="partner_id"/>
                        <field name="date_order"/>
                    </group>
                    <group>
                        <field name="user_id"/>
                        <field name="company_id"/>
                    </group>
                </group>
                <notebook>
                    <page string="Order Lines">
                        <field name="order_line">
                            <tree editable="bottom">
                                <field name="product_id"/>
                                <field name="quantity"/>
                                <field name="price_unit"/>
                                <field name="price_subtotal"/>
                            </tree>
                        </field>
                    </page>
                </notebook>
            </sheet>
        </form>
    </field>
</record>
```

### 2. Load and Parse View

```python
from openflow.server.core.views.parser import ViewParser

# Get view from database
view = await env['ir.ui.view'].search([
    ('model', '=', 'sale.order'),
    ('type', '=', 'form')
], limit=1)

# Parse view
parser = ViewParser(env)
parsed = await parser.parse_view(view)
```

### 3. Validate View

```python
from openflow.server.core.views.validator import ViewValidator

validator = ViewValidator(env)
errors = await validator.validate_view(parsed)

if errors:
    print("Validation errors:")
    for error in errors:
        print(f"  - {error}")
```

### 4. Render to JSON

```python
from openflow.server.core.views.renderer import ViewRenderer

renderer = ViewRenderer(env)
json_view = renderer.render_to_json(parsed)

# Send to frontend
return json_view
```

## Best Practices

1. **Keep views simple**: Don't over-complicate view structures
2. **Use inheritance**: Extend existing views instead of duplicating
3. **Validate early**: Validate views during module installation
4. **Use appropriate widgets**: Choose widgets that match field types
5. **Group related fields**: Use groups and notebooks for organization
6. **Add help text**: Provide help attributes for complex fields
7. **Consider mobile**: Keep form layouts responsive
8. **Test inheritance**: Verify XPath expressions work correctly
9. **Use semantic names**: Name views descriptively
10. **Document complex views**: Add comments for complex structures

## Testing

Run the test suite:

```bash
pytest openflow/tests/test_views.py -v
```

Run the demo:

```bash
python openflow/examples/view_system_demo.py
```

## Architecture

```
openflow/server/core/views/
├── __init__.py          # Package exports
├── parser.py            # XML parsing
├── inheritance.py       # XPath inheritance
├── validator.py         # View validation
└── renderer.py          # JSON rendering

openflow/server/addons/base/
├── models/
│   └── ir_ui_view.py    # View model
└── views/
    └── *.xml            # View definitions
```

## Future Enhancements

- [ ] QWeb template engine integration
- [ ] Advanced XPath with lxml
- [ ] View caching for performance
- [ ] Dynamic view generation
- [ ] View editor UI
- [ ] View version control
- [ ] View analytics and usage tracking
- [ ] Mobile-optimized views
- [ ] View themes and styling
- [ ] Collaborative view editing
