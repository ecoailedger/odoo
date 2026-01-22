"""
ir.model.access - Model Access Control

Defines CRUD permissions at the model level for security groups.
"""
from openflow.server.core.orm import Model, fields


class IrModelAccess(Model):
    """
    Model Access Rights

    Defines Create, Read, Update, Delete permissions for models per security group.
    This is the first level of access control (model-level ACL).
    """
    _name = 'ir.model.access'
    _description = 'Model Access Rights'
    _order = 'model_id, group_id'

    name = fields.Char(
        string='Name',
        required=True,
        index=True,
        help='Unique identifier for this access rule'
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
        help='The model this access rule applies to'
    )

    group_id = fields.Many2one(
        'res.groups',
        string='Group',
        ondelete='cascade',
        index=True,
        help='The security group this rule applies to (empty = all users)'
    )

    perm_read = fields.Boolean(
        string='Read Access',
        default=True,
        help='Allow reading records of this model'
    )

    perm_write = fields.Boolean(
        string='Write Access',
        default=False,
        help='Allow updating records of this model'
    )

    perm_create = fields.Boolean(
        string='Create Access',
        default=False,
        help='Allow creating new records of this model'
    )

    perm_unlink = fields.Boolean(
        string='Delete Access',
        default=False,
        help='Allow deleting records of this model'
    )

    def check_access(self, operation: str) -> bool:
        """
        Check if this access rule grants the specified operation

        Args:
            operation: One of 'read', 'write', 'create', 'unlink'

        Returns:
            True if access is granted
        """
        perm_map = {
            'read': self.perm_read,
            'write': self.perm_write,
            'create': self.perm_create,
            'unlink': self.perm_unlink,
        }
        return perm_map.get(operation, False)

    def __repr__(self):
        return f"<IrModelAccess {self.name}>"
