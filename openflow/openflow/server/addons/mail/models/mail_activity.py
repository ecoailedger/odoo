"""
mail.activity - Activity Management

Manages scheduled tasks and to-dos on documents.
"""
from datetime import datetime, timedelta
from openflow.server.core.orm import Model, fields


class MailActivity(Model):
    """
    Activities

    Scheduled tasks and to-dos linked to any document.
    Activities have types (call, email, meeting, to-do) and deadlines.
    """
    _name = 'mail.activity'
    _description = 'Activity'
    _order = 'date_deadline asc, id desc'
    _rec_name = 'summary'

    # Polymorphic link to any model
    res_model = fields.Char(
        string='Related Document Model',
        required=True,
        index=True,
        help='Model name of the document this activity is attached to'
    )

    res_id = fields.Integer(
        string='Related Document ID',
        required=True,
        index=True,
        help='ID of the document this activity is attached to'
    )

    res_name = fields.Char(
        string='Document Name',
        compute='_compute_res_name',
        store=True,
        help='Display name of the related document'
    )

    # Activity Details
    activity_type_id = fields.Many2one(
        'mail.activity.type',
        string='Activity Type',
        required=True,
        help='Type of activity (call, email, meeting, to-do, etc.)'
    )

    summary = fields.Char(
        string='Summary',
        help='Short summary of the activity'
    )

    note = fields.Text(
        string='Note',
        help='Detailed notes about the activity'
    )

    # Assignment
    user_id = fields.Many2one(
        'res.users',
        string='Assigned to',
        required=True,
        default=lambda self: self.env.user,
        index=True,
        help='User responsible for this activity'
    )

    # Dates
    date_deadline = fields.Date(
        string='Due Date',
        required=True,
        default=lambda self: datetime.now().date(),
        index=True,
        help='Activity deadline'
    )

    create_date = fields.DateTime(
        string='Created',
        default=lambda self: datetime.now(),
        help='Activity creation date'
    )

    # Creator
    create_uid = fields.Many2one(
        'res.users',
        string='Created by',
        help='User who created this activity'
    )

    # State
    state = fields.Selection(
        selection=[
            ('overdue', 'Overdue'),
            ('today', 'Today'),
            ('planned', 'Planned'),
            ('done', 'Done'),
        ],
        string='State',
        compute='_compute_state',
        help='Activity state based on deadline'
    )

    # Feedback
    feedback = fields.Text(
        string='Feedback',
        help='Feedback when marking activity as done'
    )

    date_done = fields.DateTime(
        string='Completed',
        help='Date when activity was marked as done'
    )

    # Related Fields
    activity_category = fields.Selection(
        string='Activity Category',
        related='activity_type_id.category',
        readonly=True,
        help='Category of activity type'
    )

    icon = fields.Char(
        string='Icon',
        related='activity_type_id.icon',
        readonly=True,
        help='Icon for the activity type'
    )

    def _compute_res_name(self):
        """Compute display name of related document"""
        for activity in self:
            if activity.res_model and activity.res_id:
                try:
                    record = self.env[activity.res_model].browse(activity.res_id)
                    if record:
                        activity.res_name = (
                            record.display_name
                            if hasattr(record, 'display_name')
                            else record.name if hasattr(record, 'name')
                            else f'{activity.res_model}/{activity.res_id}'
                        )
                    else:
                        activity.res_name = f'{activity.res_model}/{activity.res_id}'
                except Exception:
                    activity.res_name = f'{activity.res_model}/{activity.res_id}'
            else:
                activity.res_name = ''

    def _compute_state(self):
        """Compute activity state based on deadline"""
        today = datetime.now().date()

        for activity in self:
            if activity.date_done:
                activity.state = 'done'
            elif activity.date_deadline < today:
                activity.state = 'overdue'
            elif activity.date_deadline == today:
                activity.state = 'today'
            else:
                activity.state = 'planned'

    async def action_done(self, feedback: str = None):
        """
        Mark activity as done

        Args:
            feedback: Optional feedback message
        """
        values = {
            'date_done': datetime.now(),
        }
        if feedback:
            values['feedback'] = feedback

        await self.write(values)

        # Post message on the related record
        for activity in self:
            if activity.res_model and activity.res_id:
                record = self.env[activity.res_model].browse(activity.res_id)
                if record and hasattr(record, 'message_post'):
                    body = f"Activity '{activity.summary or activity.activity_type_id.name}' marked as done"
                    if feedback:
                        body += f"<br/>Feedback: {feedback}"
                    await record.message_post(
                        body=body,
                        message_type='notification'
                    )

    async def action_done_schedule_next(self):
        """Mark activity as done and schedule next one"""
        await self.action_done()

        # Create next activity
        for activity in self:
            await self.create({
                'res_model': activity.res_model,
                'res_id': activity.res_id,
                'activity_type_id': activity.activity_type_id.id,
                'summary': activity.summary,
                'note': activity.note,
                'user_id': activity.user_id.id,
                'date_deadline': datetime.now().date() + timedelta(
                    days=activity.activity_type_id.delay_count or 1
                ),
            })

    def __repr__(self):
        return f"<MailActivity {self.activity_type_id.name if self.activity_type_id else 'Activity'}: {self.summary}>"


class MailActivityType(Model):
    """
    Activity Types

    Predefined types of activities (call, email, meeting, to-do).
    """
    _name = 'mail.activity.type'
    _description = 'Activity Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Name',
        required=True,
        translate=True,
        help='Activity type name'
    )

    summary = fields.Char(
        string='Default Summary',
        translate=True,
        help='Default summary for this activity type'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide this activity type'
    )

    # Category
    category = fields.Selection(
        selection=[
            ('default', 'Default'),
            ('call', 'Call'),
            ('email', 'Email'),
            ('meeting', 'Meeting'),
            ('todo', 'To-Do'),
            ('upload', 'Upload Document'),
        ],
        string='Category',
        default='default',
        help='Activity category'
    )

    # Appearance
    icon = fields.Char(
        string='Icon',
        default='fa-tasks',
        help='Font Awesome icon class'
    )

    decoration_type = fields.Selection(
        selection=[
            ('warning', 'Warning'),
            ('danger', 'Danger'),
            ('info', 'Info'),
            ('success', 'Success'),
        ],
        string='Decoration Type',
        help='Color for display'
    )

    # Scheduling
    delay_count = fields.Integer(
        string='Schedule',
        default=0,
        help='Number of days/weeks/months to schedule in the future'
    )

    delay_unit = fields.Selection(
        selection=[
            ('days', 'Days'),
            ('weeks', 'Weeks'),
            ('months', 'Months'),
        ],
        string='Delay Unit',
        default='days',
        help='Unit for delay count'
    )

    delay_from = fields.Selection(
        selection=[
            ('current_date', 'Current Date'),
            ('previous_activity', 'Previous Activity Deadline'),
        ],
        string='Delay From',
        default='current_date',
        help='What date to calculate delay from'
    )

    # Automation
    chaining_type = fields.Selection(
        selection=[
            ('suggest', 'Suggest Next Activity'),
            ('trigger', 'Trigger Next Activity'),
        ],
        string='Chaining Type',
        default='suggest',
        help='What happens after marking this activity as done'
    )

    suggested_next_type_id = fields.Many2one(
        'mail.activity.type',
        string='Suggest',
        help='Suggest this activity type as the next one'
    )

    # Default values
    default_user_id = fields.Many2one(
        'res.users',
        string='Default User',
        help='Default user for this activity type'
    )

    default_note = fields.Text(
        string='Default Note',
        translate=True,
        help='Default note template'
    )

    # Model restriction
    res_model = fields.Char(
        string='Model',
        help='Limit this activity type to a specific model'
    )

    def __repr__(self):
        return f"<MailActivityType {self.name}>"
