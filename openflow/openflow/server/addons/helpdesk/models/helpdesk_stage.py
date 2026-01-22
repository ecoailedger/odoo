"""
helpdesk.stage - Ticket Stages

Workflow stages for tickets (New, In Progress, Solved, etc.)
"""
from openflow.server.core.orm import Model, fields


class HelpdeskStage(Model):
    """
    Ticket Stages

    Defines workflow stages for tickets within a team.
    """
    _name = 'helpdesk.stage'
    _description = 'Helpdesk Stage'
    _order = 'sequence, name'

    name = fields.Char(
        string='Stage Name',
        required=True,
        translate=True,
        help='Name of this stage'
    )

    description = fields.Text(
        string='Description',
        translate=True,
        help='Stage description'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order in kanban'
    )

    team_id = fields.Many2one(
        'helpdesk.team',
        string='Team',
        help='Team this stage belongs to (empty for all teams)'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide this stage'
    )

    # Kanban
    fold = fields.Boolean(
        string='Folded in Kanban',
        default=False,
        help='Fold this stage in kanban view'
    )

    # Status
    is_close = fields.Boolean(
        string='Closing Stage',
        default=False,
        help='Mark ticket as closed when moved to this stage'
    )

    # Template
    template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        help='Auto-send email when ticket enters this stage'
    )

    # Legend
    legend_blocked = fields.Char(
        string='Kanban Blocked',
        default='Blocked',
        translate=True,
        help='Label for blocked status in kanban'
    )

    legend_done = fields.Char(
        string='Kanban Done',
        default='Ready',
        translate=True,
        help='Label for done status in kanban'
    )

    legend_normal = fields.Char(
        string='Kanban Ongoing',
        default='In Progress',
        translate=True,
        help='Label for normal status in kanban'
    )

    def __repr__(self):
        return f"<HelpdeskStage {self.name}>"
