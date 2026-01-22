"""
helpdesk.team - Support Teams

Organize support staff into teams with specific configurations.
"""
from openflow.server.core.orm import Model, fields


class HelpdeskTeam(Model):
    """
    Helpdesk Teams

    Teams organize support staff and define workflow, SLA, and settings.
    """
    _name = 'helpdesk.team'
    _description = 'Helpdesk Team'
    _order = 'sequence, name'

    name = fields.Char(
        string='Team Name',
        required=True,
        translate=True,
        help='Name of the support team'
    )

    description = fields.Text(
        string='Description',
        translate=True,
        help='Team description'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to archive this team'
    )

    # Team Members
    member_ids = fields.Many2many(
        'res.users',
        relation='helpdesk_team_members_rel',
        column1='team_id',
        column2='user_id',
        string='Team Members',
        help='Users who are part of this team'
    )

    user_id = fields.Many2one(
        'res.users',
        string='Team Leader',
        help='Team leader/manager'
    )

    # Configuration
    use_alias = fields.Boolean(
        string='Use Email Alias',
        default=False,
        help='Create tickets from emails sent to alias'
    )

    alias_name = fields.Char(
        string='Alias Name',
        help='Email alias name (e.g., support, help)'
    )

    alias_domain = fields.Char(
        string='Alias Domain',
        help='Email domain (e.g., company.com)'
    )

    # SLA
    use_sla = fields.Boolean(
        string='Use SLA',
        default=False,
        help='Enable Service Level Agreement tracking'
    )

    sla_ids = fields.One2many(
        'helpdesk.sla',
        'team_id',
        string='SLA Policies',
        help='SLA policies for this team'
    )

    # Stages
    stage_ids = fields.One2many(
        'helpdesk.stage',
        'team_id',
        string='Stages',
        help='Stages for ticket workflow'
    )

    # Assignment
    assignment_method = fields.Selection(
        selection=[
            ('manual', 'Manual'),
            ('balanced', 'Balanced'),
            ('random', 'Random'),
        ],
        string='Assignment Method',
        default='manual',
        help='How to auto-assign tickets'
    )

    # Statistics
    ticket_ids = fields.One2many(
        'helpdesk.ticket',
        'team_id',
        string='Tickets',
        help='Tickets for this team'
    )

    ticket_count = fields.Integer(
        string='Ticket Count',
        compute='_compute_ticket_count',
        help='Total number of tickets'
    )

    open_ticket_count = fields.Integer(
        string='Open Tickets',
        compute='_compute_ticket_count',
        help='Number of open tickets'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help='Company this team belongs to'
    )

    # Colors
    color = fields.Integer(
        string='Color Index',
        help='Color for kanban display'
    )

    def _compute_ticket_count(self):
        """Compute ticket statistics"""
        for team in self:
            team.ticket_count = len(team.ticket_ids)
            team.open_ticket_count = len([
                t for t in team.ticket_ids
                if hasattr(t, 'stage_id') and t.stage_id and not t.stage_id.is_close
            ])

    async def assign_ticket(self, ticket):
        """
        Auto-assign a ticket based on assignment method

        Args:
            ticket: Ticket to assign

        Returns:
            Assigned user or None
        """
        self.ensure_one()

        if not self.member_ids or self.assignment_method == 'manual':
            return None

        if self.assignment_method == 'random':
            import random
            return random.choice(self.member_ids)

        elif self.assignment_method == 'balanced':
            # Find member with least tickets
            member_tickets = {}
            for member in self.member_ids:
                count = await self.env['helpdesk.ticket'].search_count([
                    ('team_id', '=', self.id),
                    ('user_id', '=', member.id),
                    ('stage_id.is_close', '=', False),
                ])
                member_tickets[member.id] = count

            # Return member with minimum tickets
            min_user_id = min(member_tickets, key=member_tickets.get)
            return self.env['res.users'].browse(min_user_id)

        return None

    def __repr__(self):
        return f"<HelpdeskTeam {self.name}>"
