"""
mail.thread - Mixin for Messaging/Chatter

Inherit from this mixin to add messaging capabilities to any model.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from openflow.server.core.orm import Model, fields


class MailThread(Model):
    """
    Mail Thread Mixin

    Inherit from this abstract model to add messaging/chatter functionality
    to any business model. Provides:
    - Message posting (comments, notes, emails)
    - Follower management (subscriptions)
    - Activity tracking
    - Automatic field change logging
    """
    _name = 'mail.thread'
    _description = 'Mail Thread'
    _inherit = []  # This is a mixin, no parent

    # This model is abstract and won't create a database table
    _abstract = True

    message_ids = fields.One2many(
        'mail.message',
        'res_id',
        string='Messages',
        domain=lambda self: [('model', '=', self._name)],
        help='Messages and communication history'
    )

    message_follower_ids = fields.One2many(
        'mail.followers',
        'res_id',
        string='Followers',
        domain=lambda self: [('res_model', '=', self._name)],
        help='Followers of this record'
    )

    activity_ids = fields.One2many(
        'mail.activity',
        'res_id',
        string='Activities',
        domain=lambda self: [('res_model', '=', self._name)],
        help='Scheduled activities for this record'
    )

    message_partner_ids = fields.Many2many(
        'res.partner',
        string='Followers (Partners)',
        compute='_compute_message_partner_ids',
        help='Partners following this record'
    )

    message_unread = fields.Boolean(
        string='Unread Messages',
        compute='_compute_message_unread',
        help='If checked, new messages require your attention'
    )

    message_unread_counter = fields.Integer(
        string='Unread Messages Counter',
        compute='_compute_message_unread',
        help='Number of unread messages'
    )

    def _compute_message_partner_ids(self):
        """Compute followers as partners"""
        for record in self:
            if record.message_follower_ids:
                record.message_partner_ids = [
                    f.partner_id for f in record.message_follower_ids
                    if hasattr(f, 'partner_id')
                ]
            else:
                record.message_partner_ids = []

    def _compute_message_unread(self):
        """Compute if there are unread messages"""
        # This would check against user's read messages in a full implementation
        for record in self:
            record.message_unread = False
            record.message_unread_counter = 0

    async def message_post(
        self,
        body: str = '',
        subject: Optional[str] = None,
        message_type: str = 'notification',
        subtype: Optional[str] = None,
        parent_id: Optional[int] = None,
        author_id: Optional[int] = None,
        partner_ids: Optional[List[int]] = None,
        attachment_ids: Optional[List[int]] = None,
        **kwargs
    ) -> 'Model':
        """
        Post a message on the record

        Args:
            body: Message content (HTML)
            subject: Message subject
            message_type: Type of message (notification, comment, email)
            subtype: Message subtype for categorization
            parent_id: Parent message for threading
            author_id: Author partner ID
            partner_ids: List of recipient partner IDs
            attachment_ids: List of attachment IDs
            **kwargs: Additional fields for mail.message

        Returns:
            Created mail.message record
        """
        self.ensure_one()

        if not author_id:
            # Get current user's partner
            user = self.env.user
            if hasattr(user, 'partner_id'):
                author_id = user.partner_id.id

        values = {
            'body': body,
            'subject': subject,
            'message_type': message_type,
            'subtype_id': subtype,
            'parent_id': parent_id,
            'model': self._name,
            'res_id': self.id,
            'author_id': author_id,
            'partner_ids': [(6, 0, partner_ids or [])],
            'attachment_ids': [(6, 0, attachment_ids or [])],
        }

        # Add any additional kwargs
        values.update(kwargs)

        # Create the message
        message = await self.env['mail.message'].create(values)

        # Notify followers
        await self._notify_followers(message)

        return message

    async def message_post_with_view(
        self,
        views_or_xmlid: str,
        **kwargs
    ) -> 'Model':
        """
        Post a message using a template view

        Args:
            views_or_xmlid: View XML ID or view name
            **kwargs: Additional arguments for message_post

        Returns:
            Created mail.message record
        """
        # This would render the view and post the result
        # Simplified version for now
        return await self.message_post(**kwargs)

    async def message_subscribe(
        self,
        partner_ids: Optional[List[int]] = None,
        subtype_ids: Optional[List[int]] = None
    ) -> bool:
        """
        Subscribe partners to this record

        Args:
            partner_ids: List of partner IDs to subscribe
            subtype_ids: List of subtype IDs for notifications

        Returns:
            True on success
        """
        if not partner_ids:
            return False

        for partner_id in partner_ids:
            # Check if already subscribed
            existing = await self.env['mail.followers'].search([
                ('res_model', '=', self._name),
                ('res_id', '=', self.id),
                ('partner_id', '=', partner_id),
            ], limit=1)

            if not existing:
                # Create new follower
                await self.env['mail.followers'].create({
                    'res_model': self._name,
                    'res_id': self.id,
                    'partner_id': partner_id,
                    'subtype_ids': [(6, 0, subtype_ids or [])],
                })

        return True

    async def message_unsubscribe(
        self,
        partner_ids: Optional[List[int]] = None
    ) -> bool:
        """
        Unsubscribe partners from this record

        Args:
            partner_ids: List of partner IDs to unsubscribe

        Returns:
            True on success
        """
        if not partner_ids:
            return False

        followers = await self.env['mail.followers'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('partner_id', 'in', partner_ids),
        ])

        if followers:
            await followers.unlink()

        return True

    async def _notify_followers(self, message: 'Model'):
        """
        Notify followers about a new message

        Args:
            message: The mail.message record
        """
        # Get followers
        followers = await self.env['mail.followers'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
        ])

        if not followers:
            return

        # Create notifications for each follower
        for follower in followers:
            if hasattr(follower, 'partner_id'):
                await self.env['mail.notification'].create({
                    'mail_message_id': message.id,
                    'res_partner_id': follower.partner_id.id,
                    'notification_type': 'inbox',
                    'notification_status': 'ready',
                })

    async def _message_auto_subscribe(self, partner_ids: Optional[List[int]] = None):
        """
        Auto-subscribe partners (called on create/write)

        Args:
            partner_ids: Partners to auto-subscribe
        """
        if partner_ids:
            await self.message_subscribe(partner_ids=partner_ids)

    async def _track_fields(self, fields_to_track: Optional[List[str]] = None):
        """
        Track field changes and post message

        This would be called automatically on write() to log changes.

        Args:
            fields_to_track: List of field names to track
        """
        # In a full implementation, this would:
        # 1. Compare old vs new values
        # 2. Generate human-readable change description
        # 3. Post message with changes
        pass

    async def activity_schedule(
        self,
        activity_type_id: int,
        summary: Optional[str] = None,
        note: Optional[str] = None,
        user_id: Optional[int] = None,
        date_deadline: Optional[datetime] = None
    ) -> 'Model':
        """
        Schedule an activity on this record

        Args:
            activity_type_id: Type of activity
            summary: Activity summary
            note: Activity notes
            user_id: User assigned to the activity
            date_deadline: Activity deadline

        Returns:
            Created mail.activity record
        """
        self.ensure_one()

        if not user_id:
            user_id = self.env.user.id

        if not date_deadline:
            date_deadline = datetime.now().date()

        return await self.env['mail.activity'].create({
            'res_model': self._name,
            'res_id': self.id,
            'activity_type_id': activity_type_id,
            'summary': summary,
            'note': note,
            'user_id': user_id,
            'date_deadline': date_deadline,
        })

    async def activity_feedback(
        self,
        activity_id: int,
        feedback: Optional[str] = None
    ):
        """
        Mark activity as done with feedback

        Args:
            activity_id: Activity to mark done
            feedback: Feedback message
        """
        activity = await self.env['mail.activity'].browse(activity_id)
        if activity:
            if feedback:
                await self.message_post(
                    body=feedback,
                    message_type='comment'
                )
            await activity.action_done()
