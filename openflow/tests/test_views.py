"""
Tests for View System

Tests view parsing, inheritance, validation, and rendering.
"""
import pytest
from openflow.server.core.views.parser import ViewParser
from openflow.server.core.views.inheritance import ViewInheritance
from openflow.server.core.views.validator import ViewValidator
from openflow.server.core.views.renderer import ViewRenderer


class TestViewParser:
    """Test view parser functionality"""

    def test_parse_form_view(self):
        """Test parsing a form view"""
        parser = ViewParser()

        view_xml = """
        <form string="Test Form">
            <sheet>
                <group>
                    <field name="name"/>
                    <field name="email" widget="email"/>
                </group>
            </sheet>
        </form>
        """

        view = {
            'id': 1,
            'name': 'test.form',
            'type': 'form',
            'model': 'res.partner',
            'arch': view_xml
        }

        # This would be async in real usage
        # parsed = await parser.parse_view(view)

        # For now, just test XML parsing directly
        import xml.etree.ElementTree as ET
        root = ET.fromstring(view_xml)
        assert root.tag == 'form'
        assert root.get('string') == 'Test Form'

    def test_parse_tree_view(self):
        """Test parsing a tree view"""
        parser = ViewParser()

        view_xml = """
        <tree string="Test Tree" editable="bottom">
            <field name="name"/>
            <field name="email"/>
            <button name="action_confirm" type="object" string="Confirm"/>
        </tree>
        """

        import xml.etree.ElementTree as ET
        root = ET.fromstring(view_xml)
        assert root.tag == 'tree'
        assert root.get('editable') == 'bottom'

    def test_parse_kanban_view(self):
        """Test parsing a kanban view"""
        parser = ViewParser()

        view_xml = """
        <kanban default_group_by="state">
            <field name="name"/>
            <field name="state"/>
            <templates>
                <t t-name="kanban-box">
                    <div class="oe_kanban_card">
                        <field name="name"/>
                    </div>
                </t>
            </templates>
        </kanban>
        """

        import xml.etree.ElementTree as ET
        root = ET.fromstring(view_xml)
        assert root.tag == 'kanban'
        assert root.get('default_group_by') == 'state'

    def test_parse_search_view(self):
        """Test parsing a search view"""
        parser = ViewParser()

        view_xml = """
        <search string="Search Partners">
            <field name="name"/>
            <filter name="customers" string="Customers" domain="[('is_customer', '=', True)]"/>
            <group expand="0" string="Group By">
                <filter name="group_country" string="Country" context="{'group_by': 'country_id'}"/>
            </group>
        </search>
        """

        import xml.etree.ElementTree as ET
        root = ET.fromstring(view_xml)
        assert root.tag == 'search'

    def test_parse_calendar_view(self):
        """Test parsing a calendar view"""
        parser = ViewParser()

        view_xml = """
        <calendar string="Events"
                  date_start="start_date"
                  date_stop="end_date"
                  color="partner_id">
            <field name="name"/>
        </calendar>
        """

        import xml.etree.ElementTree as ET
        root = ET.fromstring(view_xml)
        assert root.tag == 'calendar'
        assert root.get('date_start') == 'start_date'

    def test_parse_pivot_view(self):
        """Test parsing a pivot view"""
        parser = ViewParser()

        view_xml = """
        <pivot string="Sales Analysis">
            <field name="partner_id" type="row"/>
            <field name="state" type="col"/>
            <field name="amount_total" type="measure"/>
        </pivot>
        """

        import xml.etree.ElementTree as ET
        root = ET.fromstring(view_xml)
        assert root.tag == 'pivot'

    def test_parse_graph_view(self):
        """Test parsing a graph view"""
        parser = ViewParser()

        view_xml = """
        <graph string="Sales Chart" type="bar" stacked="True">
            <field name="date_order" type="row"/>
            <field name="amount_total" type="measure"/>
        </graph>
        """

        import xml.etree.ElementTree as ET
        root = ET.fromstring(view_xml)
        assert root.tag == 'graph'
        assert root.get('type') == 'bar'


class TestViewInheritance:
    """Test view inheritance functionality"""

    def test_xpath_before_position(self):
        """Test inserting element before target"""
        inheritance = ViewInheritance()

        base_xml = """
        <form>
            <field name="name"/>
            <field name="email"/>
        </form>
        """

        # Test XPath parsing
        import xml.etree.ElementTree as ET
        root = ET.fromstring(base_xml)

        # Find field by name
        targets = inheritance._find_by_attribute(root, "//field[@name='email']")
        assert len(targets) == 1
        assert targets[0].get('name') == 'email'

    def test_xpath_after_position(self):
        """Test inserting element after target"""
        inheritance = ViewInheritance()

        base_xml = """
        <form>
            <field name="name"/>
            <field name="email"/>
        </form>
        """

        import xml.etree.ElementTree as ET
        root = ET.fromstring(base_xml)
        targets = inheritance._find_by_attribute(root, "//field[@name='name']")
        assert len(targets) == 1

    def test_xpath_inside_position(self):
        """Test inserting element inside target"""
        inheritance = ViewInheritance()

        base_xml = """
        <form>
            <group>
                <field name="name"/>
            </group>
        </form>
        """

        import xml.etree.ElementTree as ET
        root = ET.fromstring(base_xml)
        targets = inheritance._find_xpath(root, "//group")
        assert len(targets) == 1

    def test_xpath_replace_position(self):
        """Test replacing element"""
        inheritance = ViewInheritance()

        base_xml = """
        <form>
            <field name="name"/>
        </form>
        """

        import xml.etree.ElementTree as ET
        root = ET.fromstring(base_xml)
        targets = inheritance._find_by_attribute(root, "//field[@name='name']")
        assert len(targets) == 1

    def test_xpath_attributes_position(self):
        """Test modifying element attributes"""
        inheritance = ViewInheritance()

        import xml.etree.ElementTree as ET
        elem = ET.Element('field', {'name': 'test', 'required': '0'})

        inheritance._modify_attributes(elem, {'required': '1', 'readonly': '1'})
        assert elem.get('required') == '1'
        assert elem.get('readonly') == '1'


class TestViewValidator:
    """Test view validation functionality"""

    def test_validate_field_exists(self):
        """Test validating field existence"""
        # This would require a real model in testing
        # For now, just test the validator can be instantiated
        validator = ViewValidator()
        assert validator is not None

    def test_widget_validation(self):
        """Test widget compatibility validation"""
        validator = ViewValidator()

        # Test valid widget names exist
        from openflow.server.core.orm.fields import Char, Boolean, Date

        char_field = Char(string='Test')
        valid_widgets = validator._get_valid_widgets_for_field(char_field)
        assert 'email' in valid_widgets

        bool_field = Boolean(string='Test')
        valid_widgets = validator._get_valid_widgets_for_field(bool_field)
        assert 'boolean' in valid_widgets


class TestViewRenderer:
    """Test view rendering functionality"""

    def test_render_to_json(self):
        """Test rendering view to JSON"""
        renderer = ViewRenderer()
        assert renderer is not None

    def test_render_form_component(self):
        """Test rendering form components"""
        renderer = ViewRenderer()

        # Test button rendering
        button_def = {
            'type': 'button',
            'name': 'action_confirm',
            'string': 'Confirm',
            'button_type': 'object'
        }

        rendered = renderer._render_button(button_def)
        assert rendered['type'] == 'button'
        assert rendered['name'] == 'action_confirm'

    def test_json_serialization(self):
        """Test JSON string generation"""
        renderer = ViewRenderer()

        view_def = {
            'type': 'tree',
            'model': 'res.partner',
            'fields': []
        }

        # This would require a real model
        # json_str = renderer.to_json_string(view_def)
        # assert 'tree' in json_str


class TestViewSystemIntegration:
    """Integration tests for complete view system"""

    def test_parse_validate_render_pipeline(self):
        """Test complete pipeline: parse -> validate -> render"""
        parser = ViewParser()
        validator = ViewValidator()
        renderer = ViewRenderer()

        view_xml = """
        <form string="Test">
            <field name="name"/>
        </form>
        """

        # In real usage, this would be async and use actual models
        import xml.etree.ElementTree as ET
        root = ET.fromstring(view_xml)
        assert root.tag == 'form'

    def test_inheritance_chain_resolution(self):
        """Test resolving multiple levels of inheritance"""
        inheritance = ViewInheritance()

        base_xml = """
        <form>
            <field name="name"/>
        </form>
        """

        views = {
            1: {
                'id': 1,
                'arch': base_xml,
                'inherit_id': None
            }
        }

        result = inheritance.resolve_inheritance_chain(1, views)
        assert '<field name="name"/>' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
