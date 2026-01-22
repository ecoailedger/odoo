"""
res.groups - Security Groups

Defines security groups for role-based access control.
"""
from openflow.server.core.orm import Model, fields


class ResGroups(Model):
    """
    Security Groups

    Defines security groups that users can belong to.
    Groups are used to control access via ir.model.access and ir.rule.
    """
    _name = 'res.groups'
    _description = 'Access Groups'
    _order = 'name'

    name = fields.Char(
        string='Group Name',
        required=True,
        index=True,
        help='Name of the security group'
    )

    category_id = fields.Many2one(
        'ir.module.category',
        string='Application',
        index=True,
        help='Module category this group belongs to'
    )

    implied_ids = fields.Many2many(
        'res.groups',
        relation='res_groups_implied_rel',
        column1='gid',
        column2='hid',
        string='Inherits',
        help='Groups that are automatically granted when this group is granted'
    )

    users = fields.Many2many(
        'res.users',
        relation='res_groups_users_rel',
        column1='gid',
        column2='uid',
        string='Users',
        help='Users belonging to this group'
    )

    model_access = fields.One2many(
        'ir.model.access',
        'group_id',
        string='Access Controls',
        help='Model-level access rights for this group'
    )

    rule_groups = fields.Many2many(
        'ir.rule',
        relation='rule_group_rel',
        column1='group_id',
        column2='rule_id',
        string='Rules',
        help='Record-level security rules for this group'
    )

    comment = fields.Text(
        string='Comment',
        help='Description and notes about this group'
    )

    color = fields.Integer(
        string='Color',
        help='Color index for UI display'
    )

    share = fields.Boolean(
        string='Share Group',
        default=False,
        help='Group for external portal/website users (limited access)'
    )

    def get_application_groups(self, domain=None):
        """
        Get groups organized by application category

        Args:
            domain: Optional domain to filter groups

        Returns:
            Dictionary mapping categories to groups
        """
        # TODO: Implement once we have proper search
        pass

    def __repr__(self):
        return f"<ResGroups {self.name}>"
