"""
mail.message - Messages and Communications

Stores all messages, comments, emails, and notifications.
"""
from datetime import datetime
from openflow.server.core.orm import Model, fields


class MailMessage(Model):
    """
    Messages

    Stores all communications: comments, notes, emails, notifications.
    Messages are polymorphically linked to any record via model/res_id.
    """
    _name = 'mail.message'
    _description = 'Message'
    _order = 'id desc'
    _rec_name = 'subject'

    # Message Content
    subject = fields.Char(
        string='Subject',
        help='Message subject'
    )

    body = fields.Text(
        string='Contents',
        help='Message body (HTML content)'
    )

    # Message Type
    message_type = fields.Selection(
        selection=[
            ('email', 'Email'),
            ('comment', 'Comment'),
            ('notification', 'System Notification'),
            ('user_notification', 'User Notification'),
        ],
        string='Type',
        required=True,
        default='notification',
        help='Message type'
    )

    # Message Subtype
    subtype_id = fields.Many2one(
        'mail.message.subtype',
        string='Subtype',
        help='Message subtype for categorization'
    )

    # Tracking
    model = fields.Char(
        string='Related Document Model',
        index=True,
        help='Model name of the document this message is attached to'
    )

    res_id = fields.Integer(
        string='Related Document ID',
        index=True,
        help='ID of the document this message is attached to'
    )

    record_name = fields.Char(
        string='Document Name',
        help='Name of the related document'
    )

    # Threading
    parent_id = fields.Many2one(
        'mail.message',
        string='Parent Message',
        index=True,
        help='Parent message for threading'
    )

    child_ids = fields.One2many(
        'mail.message',
        'parent_id',
        string='Child Messages',
        help='Child messages (replies)'
    )

    # Author and Recipients
    author_id = fields.Many2one(
        'res.partner',
        string='Author',
        index=True,
        help='Author of the message'
    )

    partner_ids = fields.Many2many(
        'res.partner',
        relation='mail_message_res_partner_rel',
        column1='mail_message_id',
        column2='partner_id',
        string='Recipients',
        help='Partners that will receive this message'
    )

    # Notifications
    notification_ids = fields.One2many(
        'mail.notification',
        'mail_message_id',
        string='Notifications',
        help='Notification records for this message'
    )

    notified_partner_ids = fields.Many2many(
        'res.partner',
        string='Notified Partners',
        compute='_compute_notified_partner_ids',
        help='Partners that have been notified'
    )

    # Attachments
    attachment_ids = fields.Many2many(
        'ir.attachment',
        relation='message_attachment_rel',
        column1='message_id',
        column2='attachment_id',
        string='Attachments',
        help='Attached files'
    )

    # Email Specifics
    email_from = fields.Char(
        string='From',
        help='Email address of the sender (email messages only)'
    )

    email_to = fields.Char(
        string='To',
        help='Comma-separated email addresses (email messages only)'
    )

    email_cc = fields.Char(
        string='Cc',
        help='Carbon copy email addresses'
    )

    reply_to = fields.Char(
        string='Reply-To',
        help='Reply-to email address'
    )

    message_id = fields.Char(
        string='Message-Id',
        help='Email message ID for threading'
    )

    # Status
    starred_partner_ids = fields.Many2many(
        'res.partner',
        relation='mail_message_res_partner_starred_rel',
        column1='mail_message_id',
        column2='partner_id',
        string='Starred By',
        help='Partners who starred this message'
    )

    # Metadata
    date = fields.DateTime(
        string='Date',
        default=lambda self: datetime.now(),
        index=True,
        help='Message creation date'
    )

    # Additional Info
    tracking_value_ids = fields.One2many(
        'mail.tracking.value',
        'mail_message_id',
        string='Tracking Values',
        help='Tracked field changes for this message'
    )

    is_internal = fields.Boolean(
        string='Internal',
        default=False,
        help='Hide to external users'
    )

    def _compute_notified_partner_ids(self):
        """Compute partners that have been notified"""
        for message in self:
            if message.notification_ids:
                message.notified_partner_ids = [
                    n.res_partner_id for n in message.notification_ids
                    if hasattr(n, 'res_partner_id')
                ]
            else:
                message.notified_partner_ids = []

    def __repr__(self):
        return f"<MailMessage {self.id}: {self.subject or 'No Subject'}>"


class MailMessageSubtype(Model):
    """
    Message Subtypes

    Categorizes messages for filtering and subscription preferences.
    """
    _name = 'mail.message.subtype'
    _description = 'Message Subtype'
    _order = 'sequence, name'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        help='Subtype name'
    )

    description = fields.Text(
        string='Description',
        translate=True,
        help='Subtype description'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order'
    )

    internal = fields.Boolean(
        string='Internal Only',
        default=False,
        help='Internal messages, not visible to external users'
    )

    parent_id = fields.Many2one(
        'mail.message.subtype',
        string='Parent',
        help='Parent subtype for hierarchical organization'
    )

    relation_field = fields.Char(
        string='Relation Field',
        help='Field used for automatic subscription (e.g., user_id, partner_id)'
    )

    res_model = fields.Char(
        string='Model',
        help='Model this subtype applies to (if specific to a model)'
    )

    default = fields.Boolean(
        string='Default',
        default=True,
        help='Followers are subscribed to this subtype by default'
    )

    hidden = fields.Boolean(
        string='Hidden',
        default=False,
        help='Hide this subtype in the follower options'
    )

    def __repr__(self):
        return f"<MailMessageSubtype {self.name}>"


class MailTracking Value(Model):
    """
    Mail Tracking Values

    Stores individual field changes for tracking messages.
    """
    _name = 'mail.tracking.value'
    _description = 'Mail Tracking Value'
    _order = 'id'

    mail_message_id = fields.Many2one(
        'mail.message',
        string='Message',
        required=True,
        index=True,
        help='Message this tracking value belongs to'
    )

    field = fields.Char(
        string='Field',
        required=True,
        help='Technical field name'
    )

    field_desc = fields.Char(
        string='Field Description',
        required=True,
        help='Human-readable field name'
    )

    field_type = fields.Char(
        string='Field Type',
        help='Technical field type'
    )

    old_value_integer = fields.Integer(
        string='Old Value Integer',
        help='Old value for integer fields'
    )

    old_value_float = fields.Float(
        string='Old Value Float',
        help='Old value for float fields'
    )

    old_value_char = fields.Char(
        string='Old Value Char',
        help='Old value for char/text fields'
    )

    old_value_text = fields.Text(
        string='Old Value Text',
        help='Old value for text fields'
    )

    old_value_datetime = fields.DateTime(
        string='Old Value DateTime',
        help='Old value for datetime fields'
    )

    new_value_integer = fields.Integer(
        string='New Value Integer',
        help='New value for integer fields'
    )

    new_value_float = fields.Float(
        string='New Value Float',
        help='New value for float fields'
    )

    new_value_char = fields.Char(
        string='New Value Char',
        help='New value for char/text fields'
    )

    new_value_text = fields.Text(
        string='New Value Text',
        help='New value for text fields'
    )

    new_value_datetime = fields.DateTime(
        string='New Value DateTime',
        help='New value for datetime fields'
    )

    def __repr__(self):
        return f"<MailTrackingValue {self.field_desc}: {self.old_value_char} → {self.new_value_char}>"


class MailNotification(Model):
    """
    Mail Notifications

    Tracks notification delivery status for each recipient.
    """
    _name = 'mail.notification'
    _description = 'Mail Notification'
    _order = 'id desc'

    mail_message_id = fields.Many2one(
        'mail.message',
        string='Message',
        required=True,
        index=True,
        help='Message to notify about'
    )

    res_partner_id = fields.Many2one(
        'res.partner',
        string='Recipient',
        required=True,
        index=True,
        help='Recipient partner'
    )

    notification_type = fields.Selection(
        selection=[
            ('inbox', 'Inbox'),
            ('email', 'Email'),
        ],
        string='Notification Type',
        default='inbox',
        required=True,
        help='Type of notification'
    )

    notification_status = fields.Selection(
        selection=[
            ('ready', 'Ready to Send'),
            ('sent', 'Sent'),
            ('bounce', 'Bounced'),
            ('exception', 'Exception'),
            ('canceled', 'Canceled'),
        ],
        string='Status',
        default='ready',
        required=True,
        help='Notification delivery status'
    )

    is_read = fields.Boolean(
        string='Is Read',
        default=False,
        help='Has the recipient read this notification'
    )

    read_date = fields.DateTime(
        string='Read Date',
        help='Date when notification was read'
    )

    failure_type = fields.Selection(
        selection=[
            ('unknown', 'Unknown'),
            ('mail_missing', 'Missing Email'),
            ('mail_smtp', 'SMTP Error'),
            ('mail_bounce', 'Bounced Email'),
        ],
        string='Failure Type',
        help='Type of failure if notification failed'
    )

    failure_reason = fields.Text(
        string='Failure Reason',
        help='Technical reason for failure'
    )

    def __repr__(self):
        partner_name = self.res_partner_id.name if self.res_partner_id else 'N/A'
        return f"<MailNotification {self.notification_type} to {partner_name}: {self.notification_status}>"
