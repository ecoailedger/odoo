"""
View Renderer

Renders view definitions to JSON for frontend consumption.
"""
import json
import logging
from typing import Dict, Any, List, Optional
from openflow.server.core.orm.registry import registry

logger = logging.getLogger(__name__)


class ViewRenderer:
    """
    Render view definitions to JSON for frontend
    """

    def __init__(self, env=None):
        """
        Initialize renderer

        Args:
            env: Environment for model access
        """
        self.env = env

    def render_to_json(self, view_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render view definition to JSON

        Args:
            view_def: Parsed view definition

        Returns:
            JSON-serializable dict for frontend
        """
        view_type = view_def.get('type')
        model_name = view_def.get('model')

        # Get model metadata
        model_class = registry.get(model_name)
        if not model_class:
            raise ValueError(f"Model '{model_name}' not found")

        # Render based on view type
        if view_type == 'form':
            return self._render_form_view(view_def, model_class)
        elif view_type == 'tree':
            return self._render_tree_view(view_def, model_class)
        elif view_type == 'kanban':
            return self._render_kanban_view(view_def, model_class)
        elif view_type == 'search':
            return self._render_search_view(view_def, model_class)
        elif view_type == 'calendar':
            return self._render_calendar_view(view_def, model_class)
        elif view_type == 'pivot':
            return self._render_pivot_view(view_def, model_class)
        elif view_type == 'graph':
            return self._render_graph_view(view_def, model_class)
        else:
            # Generic rendering
            return view_def

    def _render_form_view(self, view_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """
        Render form view to JSON

        Args:
            view_def: Parsed form view
            model_class: Model class

        Returns:
            JSON for frontend
        """
        result = {
            'type': 'form',
            'model': model_class._name,
            'view_id': view_def.get('view_id'),
            'name': view_def.get('name'),
            'attrs': view_def.get('attrs', {}),
            'components': []
        }

        # Render components
        components = view_def.get('components', [])
        for component in components:
            rendered = self._render_component(component, model_class)
            if rendered:
                result['components'].append(rendered)

        return result

    def _render_component(self, component: Dict[str, Any], model_class) -> Optional[Dict[str, Any]]:
        """
        Render a form component

        Args:
            component: Component definition
            model_class: Model class

        Returns:
            Rendered component
        """
        comp_type = component.get('type')

        if comp_type == 'field':
            return self._render_field(component, model_class)
        elif comp_type == 'group':
            return self._render_group(component, model_class)
        elif comp_type == 'notebook':
            return self._render_notebook(component, model_class)
        elif comp_type == 'header':
            return self._render_header(component, model_class)
        elif comp_type == 'sheet':
            return self._render_sheet(component, model_class)
        elif comp_type == 'button':
            return self._render_button(component)
        else:
            # Generic component
            result = {
                'type': comp_type,
                'attrs': component.get('attrs', {}),
                'text': component.get('text')
            }

            # Render children if present
            if 'children' in component:
                result['children'] = [
                    self._render_component(child, model_class)
                    for child in component['children']
                ]

            return result

    def _render_field(self, field_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """
        Render field component

        Args:
            field_def: Field definition
            model_class: Model class

        Returns:
            Rendered field
        """
        field_name = field_def.get('name')
        field_obj = model_class._fields.get(field_name)

        result = {
            'type': 'field',
            'name': field_name,
            'attrs': field_def.get('attrs', {}),
        }

        # Add field metadata
        if field_obj:
            result['field_type'] = type(field_obj).__name__
            result['string'] = field_obj.string
            result['required'] = field_obj.required
            result['readonly'] = field_obj.readonly
            result['help'] = getattr(field_obj, 'help', None)

            # Add relational field info
            if hasattr(field_obj, 'comodel_name'):
                result['comodel'] = field_obj.comodel_name

            # Add selection options
            if hasattr(field_obj, 'selection'):
                result['selection'] = field_obj.selection

        # Add view-specific overrides
        if field_def.get('widget'):
            result['widget'] = field_def['widget']
        if field_def.get('readonly') is not None:
            result['readonly'] = field_def['readonly']
        if field_def.get('required') is not None:
            result['required'] = field_def['required']
        if field_def.get('invisible'):
            result['invisible'] = field_def['invisible']
        if field_def.get('domain'):
            result['domain'] = field_def['domain']
        if field_def.get('context'):
            result['context'] = field_def['context']

        # Nested view for o2m/m2m
        if 'view' in field_def:
            result['nested_view'] = field_def['view']

        return result

    def _render_group(self, group_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """Render group component"""
        return {
            'type': 'group',
            'attrs': group_def.get('attrs', {}),
            'children': [
                self._render_component(child, model_class)
                for child in group_def.get('children', [])
            ]
        }

    def _render_notebook(self, notebook_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """Render notebook component"""
        return {
            'type': 'notebook',
            'attrs': notebook_def.get('attrs', {}),
            'pages': [
                self._render_page(page, model_class)
                for page in notebook_def.get('pages', [])
            ]
        }

    def _render_page(self, page_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """Render notebook page"""
        return {
            'type': 'page',
            'attrs': page_def.get('attrs', {}),
            'string': page_def.get('string', ''),
            'children': [
                self._render_component(child, model_class)
                for child in page_def.get('children', [])
            ]
        }

    def _render_header(self, header_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """Render form header"""
        return {
            'type': 'header',
            'attrs': header_def.get('attrs', {}),
            'children': [
                self._render_component(child, model_class)
                for child in header_def.get('children', [])
            ]
        }

    def _render_sheet(self, sheet_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """Render form sheet"""
        return {
            'type': 'sheet',
            'attrs': sheet_def.get('attrs', {}),
            'children': [
                self._render_component(child, model_class)
                for child in sheet_def.get('children', [])
            ]
        }

    def _render_button(self, button_def: Dict[str, Any]) -> Dict[str, Any]:
        """Render button"""
        return {
            'type': 'button',
            'name': button_def.get('name'),
            'string': button_def.get('string'),
            'button_type': button_def.get('button_type'),
            'icon': button_def.get('icon'),
            'class': button_def.get('class'),
            'attrs': button_def.get('attrs', {}),
        }

    def _render_tree_view(self, view_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """
        Render tree view to JSON

        Args:
            view_def: Parsed tree view
            model_class: Model class

        Returns:
            JSON for frontend
        """
        result = {
            'type': 'tree',
            'model': model_class._name,
            'view_id': view_def.get('view_id'),
            'name': view_def.get('name'),
            'attrs': view_def.get('attrs', {}),
            'editable': view_def.get('editable'),
            'decoration': view_def.get('decoration', {}),
            'fields': []
        }

        # Render fields
        for field in view_def.get('fields', []):
            if field.get('type') == 'field':
                rendered = self._render_field(field, model_class)
            elif field.get('type') == 'button':
                rendered = self._render_button(field)
            else:
                rendered = field

            result['fields'].append(rendered)

        return result

    def _render_kanban_view(self, view_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """
        Render kanban view to JSON

        Args:
            view_def: Parsed kanban view
            model_class: Model class

        Returns:
            JSON for frontend
        """
        result = {
            'type': 'kanban',
            'model': model_class._name,
            'view_id': view_def.get('view_id'),
            'name': view_def.get('name'),
            'attrs': view_def.get('attrs', {}),
            'default_group_by': view_def.get('default_group_by'),
            'quick_create': view_def.get('quick_create', True),
            'fields': [],
            'templates': view_def.get('templates', {})
        }

        # Render fields
        for field in view_def.get('fields', []):
            rendered = self._render_field(field, model_class)
            result['fields'].append(rendered)

        return result

    def _render_search_view(self, view_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """
        Render search view to JSON

        Args:
            view_def: Parsed search view
            model_class: Model class

        Returns:
            JSON for frontend
        """
        result = {
            'type': 'search',
            'model': model_class._name,
            'view_id': view_def.get('view_id'),
            'name': view_def.get('name'),
            'attrs': view_def.get('attrs', {}),
            'fields': [],
            'filters': view_def.get('filters', []),
            'group_by': view_def.get('group_by', [])
        }

        # Render fields
        for field in view_def.get('fields', []):
            rendered = self._render_field(field, model_class)
            result['fields'].append(rendered)

        return result

    def _render_calendar_view(self, view_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """
        Render calendar view to JSON

        Args:
            view_def: Parsed calendar view
            model_class: Model class

        Returns:
            JSON for frontend
        """
        result = {
            'type': 'calendar',
            'model': model_class._name,
            'view_id': view_def.get('view_id'),
            'name': view_def.get('name'),
            'attrs': view_def.get('attrs', {}),
            'date_start': view_def.get('date_start'),
            'date_stop': view_def.get('date_stop'),
            'date_delay': view_def.get('date_delay'),
            'color': view_def.get('color'),
            'mode': view_def.get('mode', 'month'),
            'fields': []
        }

        # Render fields
        for field in view_def.get('fields', []):
            rendered = self._render_field(field, model_class)
            result['fields'].append(rendered)

        return result

    def _render_pivot_view(self, view_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """
        Render pivot view to JSON

        Args:
            view_def: Parsed pivot view
            model_class: Model class

        Returns:
            JSON for frontend
        """
        result = {
            'type': 'pivot',
            'model': model_class._name,
            'view_id': view_def.get('view_id'),
            'name': view_def.get('name'),
            'attrs': view_def.get('attrs', {}),
            'disable_linking': view_def.get('disable_linking', False),
            'display_quantity': view_def.get('display_quantity', True),
            'fields': []
        }

        # Render fields with pivot-specific attributes
        for field in view_def.get('fields', []):
            rendered = self._render_field(field, model_class)
            rendered['pivot_type'] = field.get('type_attr')  # row, col, measure
            result['fields'].append(rendered)

        return result

    def _render_graph_view(self, view_def: Dict[str, Any], model_class) -> Dict[str, Any]:
        """
        Render graph view to JSON

        Args:
            view_def: Parsed graph view
            model_class: Model class

        Returns:
            JSON for frontend
        """
        result = {
            'type': 'graph',
            'model': model_class._name,
            'view_id': view_def.get('view_id'),
            'name': view_def.get('name'),
            'attrs': view_def.get('attrs', {}),
            'graph_type': view_def.get('graph_type', 'bar'),
            'stacked': view_def.get('stacked', False),
            'fields': []
        }

        # Render fields with graph-specific attributes
        for field in view_def.get('fields', []):
            rendered = self._render_field(field, model_class)
            rendered['graph_type'] = field.get('type_attr')  # row, measure
            result['fields'].append(rendered)

        return result

    def to_json_string(self, view_def: Dict[str, Any], indent: int = 2) -> str:
        """
        Convert view definition to JSON string

        Args:
            view_def: View definition
            indent: JSON indent level

        Returns:
            JSON string
        """
        rendered = self.render_to_json(view_def)
        return json.dumps(rendered, indent=indent)
