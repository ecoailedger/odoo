"""
helpdesk.sla - Service Level Agreement

Defines SLA policies for ticket response times.
"""
from openflow.server.core.orm import Model, fields


class HelpdeskSLA(Model):
    """
    Service Level Agreement

    Defines time targets for reaching specific stages based on priority.
    """
    _name = 'helpdesk.sla'
    _description = 'Helpdesk SLA'
    _order = 'team_id, priority desc, time'

    name = fields.Char(
        string='SLA Policy Name',
        required=True,
        help='Name of this SLA policy'
    )

    description = fields.Text(
        string='Description',
        help='SLA policy description'
    )

    team_id = fields.Many2one(
        'helpdesk.team',
        string='Team',
        required=True,
        help='Team this SLA applies to'
    )

    stage_id = fields.Many2one(
        'helpdesk.stage',
        string='Target Stage',
        required=True,
        help='Stage that must be reached within the time limit'
    )

    time = fields.Float(
        string='Time (Hours)',
        required=True,
        default=8.0,
        help='Number of hours to reach the target stage'
    )

    priority = fields.Selection(
        selection=[
            ('0', 'Low'),
            ('1', 'Normal'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Minimum Priority',
        help='Minimum priority for this SLA to apply (leave empty for all)'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to disable this SLA'
    )

    exclude_weekends = fields.Boolean(
        string='Exclude Weekends',
        default=False,
        help='Exclude weekends from SLA time calculation'
    )

    exclude_holidays = fields.Boolean(
        string='Exclude Holidays',
        default=False,
        help='Exclude holidays from SLA time calculation'
    )

    def __repr__(self):
        return f"<HelpdeskSLA {self.name}: {self.time}h>"
