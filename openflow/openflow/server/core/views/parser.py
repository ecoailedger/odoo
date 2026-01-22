"""
View Parser

Parses XML view definitions into Python dictionary structures.
"""
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class ViewParser:
    """
    Parse XML view definitions into structured dictionaries
    """

    def __init__(self, env=None):
        """
        Initialize view parser

        Args:
            env: Environment for model access
        """
        self.env = env

    async def parse_view(self, view: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a view definition

        Args:
            view: View record dict with 'arch', 'type', 'model', etc.

        Returns:
            Parsed view definition
        """
        view_type = view.get('type', 'form')
        arch_xml = view.get('arch', '')
        model = view.get('model')

        # Parse XML
        try:
            root = ET.fromstring(arch_xml)
        except ET.ParseError as e:
            logger.error(f"Failed to parse view XML: {e}")
            raise ValueError(f"Invalid XML in view: {e}")

        # Apply inheritance if needed
        if view.get('inherit_id'):
            # TODO: Load and apply parent view
            pass

        # Parse based on view type
        parser_method = getattr(self, f'_parse_{view_type}_view', None)
        if not parser_method:
            logger.warning(f"No parser for view type: {view_type}, using generic parser")
            parser_method = self._parse_generic_view

        parsed = parser_method(root, model)

        # Add metadata
        parsed['view_id'] = view.get('id')
        parsed['name'] = view.get('name')
        parsed['type'] = view_type
        parsed['model'] = model

        return parsed

    def _parse_generic_view(self, root: ET.Element, model: str) -> Dict[str, Any]:
        """
        Generic XML parser that converts any element tree to dict

        Args:
            root: XML root element
            model: Model name

        Returns:
            Parsed view structure
        """
        return {
            'tag': root.tag,
            'attrs': dict(root.attrib),
            'children': [self._element_to_dict(child) for child in root]
        }

    def _parse_form_view(self, root: ET.Element, model: str) -> Dict[str, Any]:
        """
        Parse form view

        Args:
            root: XML root element (should be <form>)
            model: Model name

        Returns:
            Parsed form view structure
        """
        if root.tag != 'form':
            raise ValueError(f"Expected <form> root element, got <{root.tag}>")

        form_def = {
            'type': 'form',
            'model': model,
            'attrs': dict(root.attrib),
            'components': []
        }

        # Parse form components
        for child in root:
            component = self._parse_form_element(child)
            if component:
                form_def['components'].append(component)

        return form_def

    def _parse_form_element(self, element: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Parse a form element (field, group, notebook, etc.)

        Args:
            element: XML element

        Returns:
            Parsed element structure
        """
        tag = element.tag
        attrs = dict(element.attrib)

        if tag == 'field':
            return self._parse_field(element)
        elif tag == 'group':
            return self._parse_group(element)
        elif tag == 'notebook':
            return self._parse_notebook(element)
        elif tag == 'page':
            return self._parse_page(element)
        elif tag == 'header':
            return self._parse_header(element)
        elif tag == 'sheet':
            return self._parse_sheet(element)
        elif tag == 'div':
            return self._parse_div(element)
        elif tag == 'button':
            return self._parse_button(element)
        elif tag == 'separator':
            return {'type': 'separator', 'attrs': attrs}
        elif tag == 'label':
            return {'type': 'label', 'attrs': attrs, 'text': element.text}
        else:
            # Generic element
            return {
                'type': tag,
                'attrs': attrs,
                'text': element.text,
                'children': [self._parse_form_element(child) for child in element]
            }

    def _parse_field(self, element: ET.Element) -> Dict[str, Any]:
        """Parse field element"""
        attrs = dict(element.attrib)
        field_name = attrs.get('name')

        field_def = {
            'type': 'field',
            'name': field_name,
            'attrs': attrs,
            'widget': attrs.get('widget'),
            'readonly': attrs.get('readonly') == '1',
            'required': attrs.get('required') == '1',
            'invisible': attrs.get('invisible'),
            'domain': attrs.get('domain'),
            'context': attrs.get('context'),
        }

        # Check for nested view (tree, form in o2m/m2m fields)
        if len(element) > 0:
            nested_view = self._element_to_dict(element[0])
            field_def['view'] = nested_view

        return field_def

    def _parse_group(self, element: ET.Element) -> Dict[str, Any]:
        """Parse group element"""
        return {
            'type': 'group',
            'attrs': dict(element.attrib),
            'children': [self._parse_form_element(child) for child in element]
        }

    def _parse_notebook(self, element: ET.Element) -> Dict[str, Any]:
        """Parse notebook element"""
        pages = []
        for child in element:
            if child.tag == 'page':
                pages.append(self._parse_page(child))

        return {
            'type': 'notebook',
            'attrs': dict(element.attrib),
            'pages': pages
        }

    def _parse_page(self, element: ET.Element) -> Dict[str, Any]:
        """Parse notebook page element"""
        return {
            'type': 'page',
            'attrs': dict(element.attrib),
            'string': element.get('string', ''),
            'children': [self._parse_form_element(child) for child in element]
        }

    def _parse_header(self, element: ET.Element) -> Dict[str, Any]:
        """Parse form header element"""
        return {
            'type': 'header',
            'attrs': dict(element.attrib),
            'children': [self._parse_form_element(child) for child in element]
        }

    def _parse_sheet(self, element: ET.Element) -> Dict[str, Any]:
        """Parse form sheet element"""
        return {
            'type': 'sheet',
            'attrs': dict(element.attrib),
            'children': [self._parse_form_element(child) for child in element]
        }

    def _parse_div(self, element: ET.Element) -> Dict[str, Any]:
        """Parse div element"""
        return {
            'type': 'div',
            'attrs': dict(element.attrib),
            'text': element.text,
            'children': [self._parse_form_element(child) for child in element]
        }

    def _parse_button(self, element: ET.Element) -> Dict[str, Any]:
        """Parse button element"""
        attrs = dict(element.attrib)
        return {
            'type': 'button',
            'attrs': attrs,
            'name': attrs.get('name'),
            'string': attrs.get('string'),
            'button_type': attrs.get('type', 'object'),
            'icon': attrs.get('icon'),
            'class': attrs.get('class'),
        }

    def _parse_tree_view(self, root: ET.Element, model: str) -> Dict[str, Any]:
        """
        Parse tree/list view

        Args:
            root: XML root element (should be <tree>)
            model: Model name

        Returns:
            Parsed tree view structure
        """
        if root.tag not in ('tree', 'list'):
            raise ValueError(f"Expected <tree> or <list> root element, got <{root.tag}>")

        tree_def = {
            'type': 'tree',
            'model': model,
            'attrs': dict(root.attrib),
            'editable': root.get('editable'),  # 'top', 'bottom', or None
            'decoration': self._extract_decorations(root),
            'fields': []
        }

        # Parse fields
        for child in root:
            if child.tag == 'field':
                field_def = self._parse_field(child)
                tree_def['fields'].append(field_def)
            elif child.tag == 'button':
                button_def = self._parse_button(child)
                tree_def['fields'].append(button_def)

        return tree_def

    def _parse_kanban_view(self, root: ET.Element, model: str) -> Dict[str, Any]:
        """
        Parse kanban view

        Args:
            root: XML root element (should be <kanban>)
            model: Model name

        Returns:
            Parsed kanban view structure
        """
        if root.tag != 'kanban':
            raise ValueError(f"Expected <kanban> root element, got <{root.tag}>")

        kanban_def = {
            'type': 'kanban',
            'model': model,
            'attrs': dict(root.attrib),
            'default_group_by': root.get('default_group_by'),
            'quick_create': root.get('quick_create') != 'false',
            'fields': [],
            'templates': {}
        }

        # Parse kanban components
        for child in root:
            if child.tag == 'field':
                field_def = self._parse_field(child)
                kanban_def['fields'].append(field_def)
            elif child.tag == 'templates':
                # Parse templates (t-name elements)
                for template in child:
                    if template.get('t-name'):
                        template_name = template.get('t-name')
                        kanban_def['templates'][template_name] = self._element_to_dict(template)

        return kanban_def

    def _parse_search_view(self, root: ET.Element, model: str) -> Dict[str, Any]:
        """
        Parse search view

        Args:
            root: XML root element (should be <search>)
            model: Model name

        Returns:
            Parsed search view structure
        """
        if root.tag != 'search':
            raise ValueError(f"Expected <search> root element, got <{root.tag}>")

        search_def = {
            'type': 'search',
            'model': model,
            'attrs': dict(root.attrib),
            'fields': [],
            'filters': [],
            'group_by': []
        }

        # Parse search components
        for child in root:
            if child.tag == 'field':
                field_def = self._parse_field(child)
                search_def['fields'].append(field_def)
            elif child.tag == 'filter':
                filter_def = {
                    'type': 'filter',
                    'name': child.get('name'),
                    'string': child.get('string'),
                    'domain': child.get('domain'),
                    'context': child.get('context'),
                }
                search_def['filters'].append(filter_def)
            elif child.tag == 'group':
                # Group by options
                for group_child in child:
                    if group_child.tag == 'filter':
                        group_def = {
                            'type': 'group_by',
                            'name': group_child.get('name'),
                            'string': group_child.get('string'),
                            'context': group_child.get('context'),
                        }
                        search_def['group_by'].append(group_def)

        return search_def

    def _parse_calendar_view(self, root: ET.Element, model: str) -> Dict[str, Any]:
        """
        Parse calendar view

        Args:
            root: XML root element (should be <calendar>)
            model: Model name

        Returns:
            Parsed calendar view structure
        """
        if root.tag != 'calendar':
            raise ValueError(f"Expected <calendar> root element, got <{root.tag}>")

        calendar_def = {
            'type': 'calendar',
            'model': model,
            'attrs': dict(root.attrib),
            'date_start': root.get('date_start'),
            'date_stop': root.get('date_stop'),
            'date_delay': root.get('date_delay'),
            'color': root.get('color'),
            'mode': root.get('mode', 'month'),
            'fields': []
        }

        # Parse fields
        for child in root:
            if child.tag == 'field':
                field_def = self._parse_field(child)
                calendar_def['fields'].append(field_def)

        return calendar_def

    def _parse_pivot_view(self, root: ET.Element, model: str) -> Dict[str, Any]:
        """
        Parse pivot view

        Args:
            root: XML root element (should be <pivot>)
            model: Model name

        Returns:
            Parsed pivot view structure
        """
        if root.tag != 'pivot':
            raise ValueError(f"Expected <pivot> root element, got <{root.tag}>")

        pivot_def = {
            'type': 'pivot',
            'model': model,
            'attrs': dict(root.attrib),
            'disable_linking': root.get('disable_linking') == 'true',
            'display_quantity': root.get('display_quantity') != 'false',
            'fields': []
        }

        # Parse fields
        for child in root:
            if child.tag == 'field':
                field_def = self._parse_field(child)
                field_def['type_attr'] = child.get('type')  # row, col, measure
                pivot_def['fields'].append(field_def)

        return pivot_def

    def _parse_graph_view(self, root: ET.Element, model: str) -> Dict[str, Any]:
        """
        Parse graph view

        Args:
            root: XML root element (should be <graph>)
            model: Model name

        Returns:
            Parsed graph view structure
        """
        if root.tag != 'graph':
            raise ValueError(f"Expected <graph> root element, got <{root.tag}>")

        graph_def = {
            'type': 'graph',
            'model': model,
            'attrs': dict(root.attrib),
            'graph_type': root.get('type', 'bar'),  # bar, line, pie
            'stacked': root.get('stacked') == 'True',
            'fields': []
        }

        # Parse fields
        for child in root:
            if child.tag == 'field':
                field_def = self._parse_field(child)
                field_def['type_attr'] = child.get('type')  # row, measure
                graph_def['fields'].append(field_def)

        return graph_def

    def _extract_decorations(self, element: ET.Element) -> Dict[str, str]:
        """
        Extract decoration attributes from element

        Args:
            element: XML element

        Returns:
            Dict of decoration attributes
        """
        decorations = {}
        for attr, value in element.attrib.items():
            if attr.startswith('decoration-'):
                decoration_type = attr.replace('decoration-', '')
                decorations[decoration_type] = value
        return decorations

    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """
        Convert XML element to dictionary recursively

        Args:
            element: XML element

        Returns:
            Dictionary representation
        """
        result = {
            'tag': element.tag,
            'attrs': dict(element.attrib),
            'text': element.text.strip() if element.text else None,
            'children': []
        }

        for child in element:
            result['children'].append(self._element_to_dict(child))

        return result
