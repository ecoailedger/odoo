"""
helpdesk.ticket - Support Tickets

Main model for support tickets with full chatter integration.
"""
from datetime import datetime
from openflow.server.core.orm import Model, fields


class HelpdeskTicket(Model):
    """
    Support Tickets

    Tracks customer support requests with workflow, SLA, and messaging.
    Inherits from mail.thread for full chatter functionality.
    """
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread']
    _order = 'priority desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Subject',
        required=True,
        index=True,
        help='Ticket subject/title'
    )

    description = fields.Text(
        string='Description',
        help='Detailed description of the issue'
    )

    ticket_ref = fields.Char(
        string='Ticket Number',
        default='New',
        index=True,
        help='Unique ticket reference number'
    )

    # Customer
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        index=True,
        help='Customer who reported this issue'
    )

    partner_name = fields.Char(
        string='Customer Name',
        related='partner_id.name',
        readonly=True,
        help='Customer name'
    )

    partner_email = fields.Char(
        string='Customer Email',
        related='partner_id.email',
        readonly=True,
        help='Customer email'
    )

    # Team and Assignment
    team_id = fields.Many2one(
        'helpdesk.team',
        string='Support Team',
        required=True,
        index=True,
        help='Team handling this ticket'
    )

    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        index=True,
        help='User assigned to this ticket'
    )

    # Stage
    stage_id = fields.Many2one(
        'helpdesk.stage',
        string='Stage',
        required=True,
        group_expand='_read_group_stage_ids',
        help='Current stage of the ticket'
    )

    # Priority
    priority = fields.Selection(
        selection=[
            ('0', 'Low'),
            ('1', 'Normal'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority',
        default='1',
        index=True,
        help='Ticket priority'
    )

    # Kanban State
    kanban_state = fields.Selection(
        selection=[
            ('normal', 'In Progress'),
            ('done', 'Ready'),
            ('blocked', 'Blocked'),
        ],
        string='Kanban State',
        default='normal',
        help='Ticket status in kanban view'
    )

    # Type
    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket Type',
        help='Type/category of this ticket'
    )

    # Tags
    tag_ids = fields.Many2many(
        'helpdesk.tag',
        relation='helpdesk_ticket_tag_rel',
        column1='ticket_id',
        column2='tag_id',
        string='Tags',
        help='Tags for categorization'
    )

    # SLA
    sla_deadline = fields.Datetime(
        string='SLA Deadline',
        compute='_compute_sla_deadline',
        store=True,
        help='Deadline based on SLA policy'
    )

    sla_status = fields.Selection(
        selection=[
            ('on_track', 'On Track'),
            ('at_risk', 'At Risk'),
            ('failed', 'Failed'),
        ],
        string='SLA Status',
        compute='_compute_sla_status',
        help='SLA compliance status'
    )

    sla_active = fields.Boolean(
        string='SLA Active',
        related='team_id.use_sla',
        readonly=True,
        help='Is SLA tracking enabled for this team'
    )

    # Dates
    create_date = fields.DateTime(
        string='Created',
        default=lambda self: datetime.now(),
        help='Ticket creation date'
    )

    close_date = fields.Datetime(
        string='Closed',
        help='Date when ticket was closed'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help='Company this ticket belongs to'
    )

    # Color for kanban
    color = fields.Integer(
        string='Color Index',
        help='Color for kanban card'
    )

    # Active
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to archive'
    )

    def _compute_sla_deadline(self):
        """Compute SLA deadline based on SLA policies"""
        for ticket in self:
            if not ticket.team_id or not ticket.team_id.use_sla:
                ticket.sla_deadline = None
                continue

            # Find matching SLA policy
            sla = self.env['helpdesk.sla'].search([
                ('team_id', '=', ticket.team_id.id),
                ('stage_id', '=', ticket.stage_id.id),
                '|',
                ('priority', '=', ticket.priority),
                ('priority', '=', False),
            ], order='priority desc', limit=1)

            if sla and hasattr(sla, 'time'):
                # Calculate deadline
                from datetime import timedelta
                ticket.sla_deadline = ticket.create_date + timedelta(hours=sla.time)
            else:
                ticket.sla_deadline = None

    def _compute_sla_status(self):
        """Compute SLA compliance status"""
        now = datetime.now()

        for ticket in self:
            if not ticket.sla_deadline:
                ticket.sla_status = False
                continue

            if ticket.stage_id and ticket.stage_id.is_close:
                # Ticket is closed
                if ticket.close_date and ticket.close_date <= ticket.sla_deadline:
                    ticket.sla_status = 'on_track'
                else:
                    ticket.sla_status = 'failed'
            else:
                # Ticket is open
                time_remaining = (ticket.sla_deadline - now).total_seconds()
                sla_hours = (ticket.sla_deadline - ticket.create_date).total_seconds() / 3600

                if time_remaining < 0:
                    ticket.sla_status = 'failed'
                elif time_remaining < (sla_hours * 3600 * 0.2):  # Less than 20% time remaining
                    ticket.sla_status = 'at_risk'
                else:
                    ticket.sla_status = 'on_track'

    @classmethod
    def _read_group_stage_ids(cls, stages, domain, order):
        """Define stage ordering for group_by in kanban"""
        # Return all stages for the team
        return stages.search([], order=order)

    async def create(self, vals):
        """Override create to generate ticket reference and auto-assign"""
        # Generate ticket reference if not provided
        if vals.get('ticket_ref', 'New') == 'New':
            sequence = await self.env['ir.sequence'].search([
                ('code', '=', 'helpdesk.ticket')
            ], limit=1)

            if sequence:
                vals['ticket_ref'] = await sequence.next_by_id()
            else:
                vals['ticket_ref'] = f"TICKET-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create ticket
        ticket = await super().create(vals)

        # Auto-assign if team has auto-assignment
        if ticket.team_id and ticket.team_id.assignment_method != 'manual':
            assigned_user = await ticket.team_id.assign_ticket(ticket)
            if assigned_user:
                await ticket.write({'user_id': assigned_user.id})

        # Auto-subscribe customer
        if ticket.partner_id:
            await ticket.message_subscribe(partner_ids=[ticket.partner_id.id])

        return ticket

    async def write(self, vals):
        """Override write to track stage changes"""
        result = await super().write(vals)

        # Check if stage changed to closing stage
        if 'stage_id' in vals:
            for ticket in self:
                if ticket.stage_id and ticket.stage_id.is_close and not ticket.close_date:
                    await ticket.write({'close_date': datetime.now()})

        return result

    async def action_assign_to_me(self):
        """Assign ticket to current user"""
        await self.write({'user_id': self.env.user.id})

    def __repr__(self):
        return f"<HelpdeskTicket {self.ticket_ref}: {self.name}>"


class HelpdeskTicketType(Model):
    """Ticket Types for categorization"""
    _name = 'helpdesk.ticket.type'
    _description = 'Ticket Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Type Name',
        required=True,
        translate=True,
        help='Ticket type name'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide'
    )

    def __repr__(self):
        return f"<HelpdeskTicketType {self.name}>"


class HelpdeskTag(Model):
    """Tags for ticket categorization"""
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tag'
    _order = 'name'

    name = fields.Char(
        string='Tag Name',
        required=True,
        translate=True,
        help='Tag name'
    )

    color = fields.Integer(
        string='Color Index',
        help='Color for display'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide'
    )

    def __repr__(self):
        return f"<HelpdeskTag {self.name}>"
