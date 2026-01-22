"""
ir.model - Model Registry

Stores metadata about all models in the system.
"""
from openflow.server.core.orm import Model, fields


class IrModel(Model):
    """
    Model Registry

    Stores information about all models registered in the system.
    This is the meta-model that describes other models.
    """
    _name = 'ir.model'
    _description = 'Models'
    _order = 'name'

    name = fields.Char(
        string='Model Description',
        required=True,
        index=True,
        help='Human-readable name of the model'
    )

    model = fields.Char(
        string='Model Name',
        required=True,
        index=True,
        help='Technical name of the model (e.g., res.partner, sale.order)'
    )

    info = fields.Text(
        string='Information',
        help='Long description and documentation about the model'
    )

    field_ids = fields.One2many(
        'ir.model.fields',
        'model_id',
        string='Fields',
        help='Fields defined on this model'
    )

    access_ids = fields.One2many(
        'ir.model.access',
        'model_id',
        string='Access Rights',
        help='Access control rules for this model'
    )

    state = fields.Selection([
        ('manual', 'Custom'),
        ('base', 'Base'),
    ], string='Type', default='manual', required=True,
        help='Type of model: base (system) or manual (user-created)')

    transient = fields.Boolean(
        string='Transient Model',
        default=False,
        help='Whether this is a transient model (wizard)'
    )

    modules = fields.Char(
        string='Modules',
        help='Modules that define or extend this model'
    )

    def __repr__(self):
        return f"<IrModel {self.model}>"
