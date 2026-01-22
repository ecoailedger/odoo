"""
ir.ui.view model

Stores UI view definitions (form, tree, kanban, etc.)
"""
from typing import Dict, Any, Optional
from openflow.server.core.orm.models import Model
from openflow.server.core.orm.fields import Char, Text, Many2one, Boolean, Selection, Integer


class IrUiView(Model):
    """
    Views define how records are displayed in the UI.

    Views can be:
    - form: Detail view for a single record
    - tree/list: Table view for multiple records
    - kanban: Card-based view
    - search: Search filters and group by
    - calendar: Calendar view
    - pivot: Pivot table for analytics
    - graph: Charts and visualizations
    """

    _name = 'ir.ui.view'
    _description = 'View'
    _order = 'priority,name,id'

    name = Char(string='View Name', required=True, index=True)
    model = Char(string='Model', required=True, index=True)
    type = Selection(
        selection=[
            ('form', 'Form'),
            ('tree', 'Tree'),
            ('kanban', 'Kanban'),
            ('search', 'Search'),
            ('calendar', 'Calendar'),
            ('pivot', 'Pivot'),
            ('graph', 'Graph'),
            ('qweb', 'QWeb'),
        ],
        string='View Type',
        required=True,
        default='form'
    )
    priority = Integer(string='Priority', default=16)
    arch = Text(string='View Architecture', required=True)
    arch_db = Text(string='Arch Blob')  # Processed architecture

    # Inheritance
    inherit_id = Many2one('ir.ui.view', string='Inherited View', ondelete='cascade')
    mode = Selection(
        selection=[
            ('primary', 'Base view'),
            ('extension', 'Extension View'),
        ],
        string='Mode',
        default='primary',
        required=True
    )

    # Additional settings
    active = Boolean(string='Active', default=True)
    field_parent = Char(string='Child Field')  # For hierarchical views
    groups_id = Many2one('res.groups', string='Groups')  # Access restriction

    async def get_view(self, view_id: Optional[int] = None, view_type: str = 'form') -> Dict[str, Any]:
        """
        Get view definition for a model

        Args:
            view_id: Specific view ID (optional)
            view_type: Type of view to get

        Returns:
            Dict with view definition
        """
        from openflow.server.core.views.parser import ViewParser

        # Find view
        if view_id:
            view = await self.browse(view_id, self._env).read(['name', 'model', 'type', 'arch', 'inherit_id'])
            if not view:
                raise ValueError(f"View {view_id} not found")
            view = view[0]
        else:
            # Search for view by model and type
            domain = [
                ('model', '=', self._env.model),
                ('type', '=', view_type),
                ('mode', '=', 'primary')
            ]
            views = await self.search(domain, limit=1)
            if not views._ids:
                raise ValueError(f"No {view_type} view found for model {self._env.model}")
            view = (await views.read(['name', 'model', 'type', 'arch', 'inherit_id']))[0]

        # Parse view
        parser = ViewParser(self._env)
        view_def = await parser.parse_view(view)

        return view_def

    async def apply_inheritance(self, arch: str, inherit_specs: list) -> str:
        """
        Apply view inheritance modifications

        Args:
            arch: Base view architecture XML
            inherit_specs: List of inheritance specifications

        Returns:
            Modified architecture XML
        """
        from openflow.server.core.views.inheritance import ViewInheritance

        inheritance = ViewInheritance()
        return await inheritance.apply_inheritance(arch, inherit_specs)
