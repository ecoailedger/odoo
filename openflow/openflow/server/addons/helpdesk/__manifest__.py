{
    'name': 'Helpdesk',
    'version': '1.0.0',
    'category': 'Services',
    'summary': 'Helpdesk and Ticketing System',
    'description': '''
Helpdesk Module - Support Ticket Management
============================================

Full-featured helpdesk and ticketing system:

Features:
- **Teams**: Organize support staff into teams
- **Tickets**: Track customer support requests
- **Stages**: Customizable ticket workflow stages
- **SLA**: Service Level Agreement tracking with deadlines
- **Assignment**: Auto-assignment rules and manual assignment
- **Email Integration**: Create tickets from emails
- **Customer Portal**: Customers can view ticket status
- **Analytics**: Reporting and pivot views

Components:
- helpdesk.team: Support teams
- helpdesk.stage: Workflow stages
- helpdesk.ticket: Support tickets (with chatter)
- helpdesk.sla: SLA definitions
- helpdesk.tag: Ticket categorization tags
    ''',
    'author': 'OpenFlow',
    'website': 'https://github.com/openflow/openflow',
    'depends': ['base', 'mail'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
