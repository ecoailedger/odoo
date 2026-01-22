"""
View System Demo

Demonstrates the XML-based view system capabilities.
"""
import asyncio
import xml.etree.ElementTree as ET
from openflow.server.core.views.parser import ViewParser
from openflow.server.core.views.inheritance import ViewInheritance
from openflow.server.core.views.validator import ViewValidator
from openflow.server.core.views.renderer import ViewRenderer


def demo_form_view():
    """Demonstrate form view parsing"""
    print("\n=== Form View Demo ===")

    view_xml = """
    <form string="Partner">
        <header>
            <button name="action_confirm" type="object" string="Confirm"/>
            <field name="state" widget="statusbar"/>
        </header>
        <sheet>
            <group>
                <field name="name" required="1"/>
                <field name="email" widget="email"/>
                <field name="phone" widget="phone"/>
            </group>
            <notebook>
                <page string="Details">
                    <field name="description"/>
                </page>
                <page string="Address">
                    <group>
                        <field name="street"/>
                        <field name="city"/>
                    </group>
                </page>
            </notebook>
        </sheet>
    </form>
    """

    parser = ViewParser()
    root = ET.fromstring(view_xml)

    print(f"View type: {root.tag}")
    print(f"String: {root.get('string')}")
    print(f"Has header: {len(root.findall('.//header')) > 0}")
    print(f"Has notebook: {len(root.findall('.//notebook')) > 0}")
    print(f"Number of pages: {len(root.findall('.//page'))}")


def demo_tree_view():
    """Demonstrate tree view parsing"""
    print("\n=== Tree View Demo ===")

    view_xml = """
    <tree string="Partners"
          editable="bottom"
          decoration-danger="state=='blocked'"
          decoration-success="state=='approved'">
        <field name="name"/>
        <field name="email"/>
        <field name="phone"/>
        <field name="state" invisible="1"/>
        <button name="action_approve" type="object" string="Approve"/>
    </tree>
    """

    root = ET.fromstring(view_xml)

    print(f"View type: {root.tag}")
    print(f"Editable: {root.get('editable')}")
    print(f"Number of fields: {len(root.findall('.//field'))}")
    print(f"Has buttons: {len(root.findall('.//button')) > 0}")

    # Extract decorations
    decorations = {}
    for attr, value in root.attrib.items():
        if attr.startswith('decoration-'):
            decorations[attr] = value
    print(f"Decorations: {decorations}")


def demo_kanban_view():
    """Demonstrate kanban view parsing"""
    print("\n=== Kanban View Demo ===")

    view_xml = """
    <kanban default_group_by="state" quick_create="true">
        <field name="name"/>
        <field name="email"/>
        <field name="state"/>
        <field name="color"/>
        <templates>
            <t t-name="kanban-box">
                <div class="oe_kanban_card">
                    <strong><field name="name"/></strong>
                    <div>
                        <field name="email"/>
                    </div>
                </div>
            </t>
        </templates>
    </kanban>
    """

    root = ET.fromstring(view_xml)

    print(f"View type: {root.tag}")
    print(f"Default group by: {root.get('default_group_by')}")
    print(f"Quick create: {root.get('quick_create')}")
    print(f"Number of fields: {len(root.findall('.//field'))}")
    print(f"Has templates: {len(root.findall('.//templates')) > 0}")


def demo_search_view():
    """Demonstrate search view parsing"""
    print("\n=== Search View Demo ===")

    view_xml = """
    <search string="Search Partners">
        <field name="name"/>
        <field name="email"/>
        <separator/>
        <filter name="customers" string="Customers" domain="[('is_customer', '=', True)]"/>
        <filter name="suppliers" string="Suppliers" domain="[('is_supplier', '=', True)]"/>
        <group expand="0" string="Group By">
            <filter name="group_country" string="Country" context="{'group_by': 'country_id'}"/>
            <filter name="group_state" string="State" context="{'group_by': 'state'}"/>
        </group>
    </search>
    """

    root = ET.fromstring(view_xml)

    print(f"View type: {root.tag}")
    print(f"Number of searchable fields: {len(root.findall('./field'))}")
    print(f"Number of filters: {len(root.findall('.//filter'))}")

    # Count group by filters
    group_by_filters = 0
    for group in root.findall('.//group'):
        group_by_filters += len(group.findall('.//filter'))
    print(f"Number of group by options: {group_by_filters}")


def demo_calendar_view():
    """Demonstrate calendar view parsing"""
    print("\n=== Calendar View Demo ===")

    view_xml = """
    <calendar string="Meetings"
              date_start="start_date"
              date_stop="end_date"
              color="partner_id"
              mode="month">
        <field name="name"/>
        <field name="partner_id"/>
        <field name="location"/>
    </calendar>
    """

    root = ET.fromstring(view_xml)

    print(f"View type: {root.tag}")
    print(f"Date start field: {root.get('date_start')}")
    print(f"Date stop field: {root.get('date_stop')}")
    print(f"Color field: {root.get('color')}")
    print(f"Default mode: {root.get('mode')}")


def demo_pivot_view():
    """Demonstrate pivot view parsing"""
    print("\n=== Pivot View Demo ===")

    view_xml = """
    <pivot string="Sales Analysis" display_quantity="true">
        <field name="partner_id" type="row"/>
        <field name="state" type="col"/>
        <field name="amount_total" type="measure"/>
        <field name="product_qty" type="measure"/>
    </pivot>
    """

    root = ET.fromstring(view_xml)

    print(f"View type: {root.tag}")
    print(f"Display quantity: {root.get('display_quantity')}")

    # Categorize fields by type
    rows = []
    cols = []
    measures = []

    for field in root.findall('.//field'):
        field_type = field.get('type')
        field_name = field.get('name')
        if field_type == 'row':
            rows.append(field_name)
        elif field_type == 'col':
            cols.append(field_name)
        elif field_type == 'measure':
            measures.append(field_name)

    print(f"Row fields: {rows}")
    print(f"Column fields: {cols}")
    print(f"Measure fields: {measures}")


def demo_graph_view():
    """Demonstrate graph view parsing"""
    print("\n=== Graph View Demo ===")

    view_xml = """
    <graph string="Sales Chart" type="bar" stacked="True">
        <field name="date_order" type="row" interval="month"/>
        <field name="amount_total" type="measure"/>
    </graph>
    """

    root = ET.fromstring(view_xml)

    print(f"View type: {root.tag}")
    print(f"Graph type: {root.get('type')}")
    print(f"Stacked: {root.get('stacked')}")

    # Categorize fields
    rows = []
    measures = []

    for field in root.findall('.//field'):
        field_type = field.get('type')
        field_name = field.get('name')
        if field_type == 'row':
            rows.append(field_name)
        elif field_type == 'measure':
            measures.append(field_name)

    print(f"Row fields: {rows}")
    print(f"Measure fields: {measures}")


def demo_view_inheritance():
    """Demonstrate view inheritance with XPath"""
    print("\n=== View Inheritance Demo ===")

    base_xml = """
    <form string="Partner">
        <sheet>
            <group>
                <field name="name"/>
                <field name="email"/>
            </group>
        </sheet>
    </form>
    """

    print("Base view:")
    print(base_xml)

    # Example inheritance modifications
    inheritance_examples = [
        {
            'description': 'Add field after email',
            'xpath': "//field[@name='email']",
            'position': 'after',
            'arch': '<field name="phone"/>'
        },
        {
            'description': 'Add field before name',
            'xpath': "//field[@name='name']",
            'position': 'before',
            'arch': '<field name="ref"/>'
        },
        {
            'description': 'Replace email field',
            'xpath': "//field[@name='email']",
            'position': 'replace',
            'arch': '<field name="email" widget="email" required="1"/>'
        },
        {
            'description': 'Modify field attributes',
            'xpath': "//field[@name='name']",
            'position': 'attributes',
            'attrs': {'required': '1', 'readonly': '0'}
        }
    ]

    print("\nInheritance examples:")
    for example in inheritance_examples:
        print(f"\n- {example['description']}")
        print(f"  XPath: {example['xpath']}")
        print(f"  Position: {example['position']}")


def demo_field_widgets():
    """Demonstrate different field widgets"""
    print("\n=== Field Widget Demo ===")

    widgets_by_type = {
        'Char fields': ['char', 'email', 'phone', 'url', 'badge'],
        'Text fields': ['text', 'html'],
        'Numeric fields': ['integer', 'float', 'monetary', 'percentage', 'progressbar'],
        'Boolean fields': ['boolean', 'toggle'],
        'Date fields': ['date', 'datetime', 'remaining_days'],
        'Many2one fields': ['many2one', 'selection', 'radio', 'badge'],
        'Many2many fields': ['many2many', 'many2many_tags', 'many2many_checkboxes'],
        'Selection fields': ['selection', 'radio', 'badge', 'statusbar'],
        'Binary fields': ['binary', 'image', 'pdf_viewer']
    }

    for field_type, widgets in widgets_by_type.items():
        print(f"\n{field_type}:")
        for widget in widgets:
            print(f"  - {widget}")


def main():
    """Run all demos"""
    print("=" * 60)
    print("XML-Based View System Demo")
    print("=" * 60)

    demo_form_view()
    demo_tree_view()
    demo_kanban_view()
    demo_search_view()
    demo_calendar_view()
    demo_pivot_view()
    demo_graph_view()
    demo_view_inheritance()
    demo_field_widgets()

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
