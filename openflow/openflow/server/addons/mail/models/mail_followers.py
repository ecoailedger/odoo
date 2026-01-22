"""
mail.followers - Follower Management

Manages subscriptions to documents for notifications.
"""
from openflow.server.core.orm import Model, fields


class MailFollowers(Model):
    """
    Followers

    Tracks which partners are following which records.
    Followers receive notifications about updates to the records they follow.
    """
    _name = 'mail.followers'
    _description = 'Document Followers'
    _rec_name = 'partner_id'

    # Polymorphic link to any model
    res_model = fields.Char(
        string='Related Document Model',
        required=True,
        index=True,
        help='Model name of the followed document'
    )

    res_id = fields.Integer(
        string='Related Document ID',
        required=True,
        index=True,
        help='ID of the followed document'
    )

    # Follower
    partner_id = fields.Many2one(
        'res.partner',
        string='Related Partner',
        required=True,
        index=True,
        help='Partner following this document'
    )

    # Subscription Preferences
    subtype_ids = fields.Many2many(
        'mail.message.subtype',
        relation='mail_followers_mail_message_subtype_rel',
        column1='follower_id',
        column2='subtype_id',
        string='Subtypes',
        help='Message subtypes this follower is subscribed to'
    )

    # Related Fields
    name = fields.Char(
        string='Name',
        related='partner_id.name',
        readonly=True,
        help='Follower name'
    )

    email = fields.Char(
        string='Email',
        related='partner_id.email',
        readonly=True,
        help='Follower email'
    )

    is_active = fields.Boolean(
        string='Active',
        related='partner_id.active',
        readonly=True,
        help='Is follower active'
    )

    def __repr__(self):
        partner_name = self.partner_id.name if self.partner_id else 'N/A'
        return f"<MailFollowers {partner_name} follows {self.res_model}/{self.res_id}>"
