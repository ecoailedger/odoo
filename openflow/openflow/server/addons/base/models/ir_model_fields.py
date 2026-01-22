"""
ir.model.fields - Field Registry

Stores metadata about all fields in the system.
"""
from openflow.server.core.orm import Model, fields


class IrModelFields(Model):
    """
    Field Registry

    Stores information about all fields defined on models.
    """
    _name = 'ir.model.fields'
    _description = 'Model Fields'
    _order = 'model_id, name'

    name = fields.Char(
        string='Field Name',
        required=True,
        index=True,
        help='Technical name of the field'
    )

    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        depends=['model', 'name'],
        help='Full field name including model (model.field)'
    )

    model = fields.Char(
        string='Model Name',
        required=True,
        index=True,
        help='Technical name of the model this field belongs to'
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        index=True,
        help='The model this field is defined on'
    )

    field_description = fields.Char(
        string='Field Label',
        required=True,
        help='Human-readable label for the field'
    )

    help = fields.Text(
        string='Field Help',
        help='Help text shown to users'
    )

    ttype = fields.Selection([
        ('char', 'Char'),
        ('text', 'Text'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('binary', 'Binary'),
        ('selection', 'Selection'),
        ('many2one', 'Many2one'),
        ('one2many', 'One2many'),
        ('many2many', 'Many2many'),
    ], string='Field Type', required=True, index=True,
        help='Type of the field')

    relation = fields.Char(
        string='Relation Model',
        help='For relational fields, the target model name'
    )

    relation_field = fields.Char(
        string='Relation Field',
        help='For One2many, the inverse Many2one field name'
    )

    relation_table = fields.Char(
        string='Relation Table',
        help='For Many2many, the intermediate join table name'
    )

    required = fields.Boolean(
        string='Required',
        default=False,
        help='Whether this field is required (cannot be null)'
    )

    readonly = fields.Boolean(
        string='Readonly',
        default=False,
        help='Whether this field is readonly'
    )

    index = fields.Boolean(
        string='Index',
        default=False,
        help='Whether a database index exists on this field'
    )

    store = fields.Boolean(
        string='Stored',
        default=True,
        help='Whether this field is stored in database'
    )

    compute = fields.Char(
        string='Compute Method',
        help='Name of the method that computes this field'
    )

    depends = fields.Char(
        string='Dependencies',
        help='Comma-separated list of field dependencies for computed fields'
    )

    related = fields.Char(
        string='Related Field',
        help='Dot-notation path to related field'
    )

    selection = fields.Text(
        string='Selection Options',
        help='For selection fields, JSON array of [key, label] pairs'
    )

    size = fields.Integer(
        string='Size',
        help='Maximum size for char fields'
    )

    state = fields.Selection([
        ('manual', 'Custom'),
        ('base', 'Base'),
    ], string='Type', default='manual', required=True,
        help='Type of field: base (system) or manual (user-created)')

    modules = fields.Char(
        string='Modules',
        help='Modules that define or extend this field'
    )

    def _compute_complete_name(self):
        """Compute the complete field name"""
        for record in self:
            record.complete_name = f"{record.model}.{record.name}"

    def __repr__(self):
        return f"<IrModelFields {self.model}.{self.name}>"
