"""
View Validator

Validates view definitions against model fields and schema.
"""
import logging
from typing import Dict, Any, List, Optional
from openflow.server.core.orm.registry import registry

logger = logging.getLogger(__name__)


class ViewValidator:
    """
    Validate view definitions against model schema
    """

    def __init__(self, env=None):
        """
        Initialize validator

        Args:
            env: Environment for model access
        """
        self.env = env

    async def validate_view(self, view_def: Dict[str, Any]) -> List[str]:
        """
        Validate a view definition

        Args:
            view_def: Parsed view definition

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        model_name = view_def.get('model')
        view_type = view_def.get('type')

        if not model_name:
            errors.append("View missing model name")
            return errors

        # Get model class
        model_class = registry.get(model_name)
        if not model_class:
            errors.append(f"Model '{model_name}' not found")
            return errors

        # Validate based on view type
        if view_type == 'form':
            errors.extend(self._validate_form_view(view_def, model_class))
        elif view_type == 'tree':
            errors.extend(self._validate_tree_view(view_def, model_class))
        elif view_type == 'kanban':
            errors.extend(self._validate_kanban_view(view_def, model_class))
        elif view_type == 'search':
            errors.extend(self._validate_search_view(view_def, model_class))
        elif view_type == 'calendar':
            errors.extend(self._validate_calendar_view(view_def, model_class))
        elif view_type == 'pivot':
            errors.extend(self._validate_pivot_view(view_def, model_class))
        elif view_type == 'graph':
            errors.extend(self._validate_graph_view(view_def, model_class))

        return errors

    def _validate_form_view(self, view_def: Dict[str, Any], model_class) -> List[str]:
        """Validate form view"""
        errors = []
        components = view_def.get('components', [])

        # Recursively validate components
        errors.extend(self._validate_components(components, model_class))

        return errors

    def _validate_tree_view(self, view_def: Dict[str, Any], model_class) -> List[str]:
        """Validate tree view"""
        errors = []
        fields = view_def.get('fields', [])

        # Validate fields
        for field in fields:
            if field.get('type') == 'field':
                field_name = field.get('name')
                if field_name and not self._field_exists(model_class, field_name):
                    errors.append(f"Field '{field_name}' not found in model '{model_class._name}'")

        return errors

    def _validate_kanban_view(self, view_def: Dict[str, Any], model_class) -> List[str]:
        """Validate kanban view"""
        errors = []
        fields = view_def.get('fields', [])

        # Validate fields
        for field in fields:
            if field.get('type') == 'field':
                field_name = field.get('name')
                if field_name and not self._field_exists(model_class, field_name):
                    errors.append(f"Field '{field_name}' not found in model '{model_class._name}'")

        # Validate default_group_by if specified
        default_group_by = view_def.get('default_group_by')
        if default_group_by and not self._field_exists(model_class, default_group_by):
            errors.append(f"default_group_by field '{default_group_by}' not found in model '{model_class._name}'")

        return errors

    def _validate_search_view(self, view_def: Dict[str, Any], model_class) -> List[str]:
        """Validate search view"""
        errors = []
        fields = view_def.get('fields', [])

        # Validate fields
        for field in fields:
            if field.get('type') == 'field':
                field_name = field.get('name')
                if field_name and not self._field_exists(model_class, field_name):
                    errors.append(f"Field '{field_name}' not found in model '{model_class._name}'")

        return errors

    def _validate_calendar_view(self, view_def: Dict[str, Any], model_class) -> List[str]:
        """Validate calendar view"""
        errors = []

        # Validate required date fields
        date_start = view_def.get('date_start')
        if not date_start:
            errors.append("Calendar view requires 'date_start' attribute")
        elif not self._field_exists(model_class, date_start):
            errors.append(f"date_start field '{date_start}' not found in model '{model_class._name}'")

        date_stop = view_def.get('date_stop')
        if date_stop and not self._field_exists(model_class, date_stop):
            errors.append(f"date_stop field '{date_stop}' not found in model '{model_class._name}'")

        date_delay = view_def.get('date_delay')
        if date_delay and not self._field_exists(model_class, date_delay):
            errors.append(f"date_delay field '{date_delay}' not found in model '{model_class._name}'")

        # Validate color field if specified
        color = view_def.get('color')
        if color and not self._field_exists(model_class, color):
            errors.append(f"color field '{color}' not found in model '{model_class._name}'")

        # Validate fields
        fields = view_def.get('fields', [])
        for field in fields:
            if field.get('type') == 'field':
                field_name = field.get('name')
                if field_name and not self._field_exists(model_class, field_name):
                    errors.append(f"Field '{field_name}' not found in model '{model_class._name}'")

        return errors

    def _validate_pivot_view(self, view_def: Dict[str, Any], model_class) -> List[str]:
        """Validate pivot view"""
        errors = []
        fields = view_def.get('fields', [])

        # Validate fields
        for field in fields:
            if field.get('type') == 'field':
                field_name = field.get('name')
                if field_name and not self._field_exists(model_class, field_name):
                    errors.append(f"Field '{field_name}' not found in model '{model_class._name}'")

        return errors

    def _validate_graph_view(self, view_def: Dict[str, Any], model_class) -> List[str]:
        """Validate graph view"""
        errors = []
        fields = view_def.get('fields', [])

        # Validate fields
        for field in fields:
            if field.get('type') == 'field':
                field_name = field.get('name')
                if field_name and not self._field_exists(model_class, field_name):
                    errors.append(f"Field '{field_name}' not found in model '{model_class._name}'")

        return errors

    def _validate_components(self, components: List[Dict[str, Any]], model_class) -> List[str]:
        """
        Recursively validate form components

        Args:
            components: List of components
            model_class: Model class

        Returns:
            List of validation errors
        """
        errors = []

        for component in components:
            comp_type = component.get('type')

            if comp_type == 'field':
                # Validate field exists
                field_name = component.get('name')
                if field_name and not self._field_exists(model_class, field_name):
                    errors.append(f"Field '{field_name}' not found in model '{model_class._name}'")

                # Validate nested view if present
                if 'view' in component:
                    nested_view = component['view']
                    # Get related model for o2m/m2m fields
                    if field_name and self._field_exists(model_class, field_name):
                        field_obj = model_class._fields[field_name]
                        if hasattr(field_obj, 'comodel_name'):
                            comodel = registry.get(field_obj.comodel_name)
                            if comodel:
                                errors.extend(self._validate_nested_view(nested_view, comodel))

            elif comp_type in ('group', 'header', 'sheet', 'div'):
                # Recursively validate children
                children = component.get('children', [])
                errors.extend(self._validate_components(children, model_class))

            elif comp_type == 'notebook':
                # Validate pages
                pages = component.get('pages', [])
                for page in pages:
                    children = page.get('children', [])
                    errors.extend(self._validate_components(children, model_class))

        return errors

    def _validate_nested_view(self, nested_view: Dict[str, Any], model_class) -> List[str]:
        """
        Validate a nested view (tree/form in o2m/m2m field)

        Args:
            nested_view: Nested view definition
            model_class: Comodel class

        Returns:
            List of validation errors
        """
        errors = []
        children = nested_view.get('children', [])

        # Validate children (typically field elements)
        for child in children:
            if child.get('type') == 'field':
                field_name = child.get('name')
                if field_name and not self._field_exists(model_class, field_name):
                    errors.append(f"Field '{field_name}' not found in model '{model_class._name}'")

        return errors

    def _field_exists(self, model_class, field_name: str) -> bool:
        """
        Check if field exists in model

        Args:
            model_class: Model class
            field_name: Field name

        Returns:
            True if field exists
        """
        return field_name in model_class._fields

    def validate_field_attributes(self, field_name: str, attrs: Dict[str, Any], model_class) -> List[str]:
        """
        Validate field attributes (widget, domain, etc.)

        Args:
            field_name: Field name
            attrs: Field attributes
            model_class: Model class

        Returns:
            List of validation errors
        """
        errors = []

        if not self._field_exists(model_class, field_name):
            errors.append(f"Field '{field_name}' not found in model '{model_class._name}'")
            return errors

        field = model_class._fields[field_name]

        # Validate widget compatibility
        widget = attrs.get('widget')
        if widget:
            valid_widgets = self._get_valid_widgets_for_field(field)
            if valid_widgets and widget not in valid_widgets:
                errors.append(f"Widget '{widget}' not valid for field type '{type(field).__name__}'")

        return errors

    def _get_valid_widgets_for_field(self, field) -> Optional[List[str]]:
        """
        Get list of valid widgets for a field type

        Args:
            field: Field object

        Returns:
            List of valid widget names or None for any
        """
        from openflow.server.core.orm.fields import (
            Char, Text, Integer, Float, Boolean, Date, DateTime,
            Many2one, One2many, Many2many, Selection, Binary
        )

        # Map field types to valid widgets
        if isinstance(field, Char):
            return ['char', 'email', 'phone', 'url', 'badge']
        elif isinstance(field, Text):
            return ['text', 'html']
        elif isinstance(field, (Integer, Float)):
            return ['integer', 'float', 'monetary', 'percentage', 'progressbar']
        elif isinstance(field, Boolean):
            return ['boolean', 'toggle']
        elif isinstance(field, (Date, DateTime)):
            return ['date', 'datetime', 'remaining_days']
        elif isinstance(field, Many2one):
            return ['many2one', 'selection', 'radio', 'badge']
        elif isinstance(field, (One2many, Many2many)):
            return ['one2many', 'many2many', 'many2many_tags', 'many2many_checkboxes']
        elif isinstance(field, Selection):
            return ['selection', 'radio', 'badge', 'statusbar']
        elif isinstance(field, Binary):
            return ['binary', 'image', 'pdf_viewer']

        return None  # Any widget allowed
