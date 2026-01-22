"""
ir.rule - Record Rules

Defines row-level security rules using domain expressions.
"""
from openflow.server.core.orm import Model, fields


class IrRule(Model):
    """
    Record Rules

    Defines record-level access control using domain expressions.
    This is the second level of access control (row-level security).

    Example:
        A rule that limits users to see only their own records:
        domain_force: [('user_id', '=', user.id)]
    """
    _name = 'ir.rule'
    _description = 'Record Rules'
    _order = 'model_id, name'

    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help='Human-readable name for this rule'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='If disabled, this rule will not be applied'
    )

    model_id = fields.Many2one(
        'ir.model',
        string='Model',
        required=True,
        ondelete='cascade',
        index=True,
        help='The model this rule applies to'
    )

    groups = fields.Many2many(
        'res.groups',
        relation='rule_group_rel',
        column1='rule_id',
        column2='group_id',
        string='Groups',
        help='Security groups this rule applies to (empty = global rule for all users)'
    )

    domain_force = fields.Text(
        string='Domain',
        help='Domain expression that filters records (Python list format)'
    )

    perm_read = fields.Boolean(
        string='Apply for Read',
        default=True,
        help='Apply this rule when reading records'
    )

    perm_write = fields.Boolean(
        string='Apply for Write',
        default=True,
        help='Apply this rule when writing records'
    )

    perm_create = fields.Boolean(
        string='Apply for Create',
        default=True,
        help='Apply this rule when creating records'
    )

    perm_unlink = fields.Boolean(
        string='Apply for Delete',
        default=True,
        help='Apply this rule when deleting records'
    )

    global_rule = fields.Boolean(
        string='Global',
        default=False,
        compute='_compute_global_rule',
        depends=['groups'],
        store=True,
        help='If True, this rule applies to all users (no groups specified)'
    )

    def _compute_global_rule(self):
        """Compute whether this is a global rule"""
        for record in self:
            record.global_rule = not bool(record.groups)

    def applies_to_operation(self, operation: str) -> bool:
        """
        Check if this rule applies to the specified operation

        Args:
            operation: One of 'read', 'write', 'create', 'unlink'

        Returns:
            True if rule should be applied
        """
        perm_map = {
            'read': self.perm_read,
            'write': self.perm_write,
            'create': self.perm_create,
            'unlink': self.perm_unlink,
        }
        return perm_map.get(operation, False)

    def __repr__(self):
        return f"<IrRule {self.name}>"
