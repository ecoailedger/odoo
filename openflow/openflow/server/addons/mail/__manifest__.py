{
    'name': 'Mail',
    'version': '1.0.0',
    'category': 'Discuss',
    'summary': 'Messaging and Activity Management',
    'description': '''
Mail Module - Messaging and Collaboration
==========================================

This module provides messaging and activity management functionality:

Core Features:
- **Chatter/Mail Thread**: Discussion and history on any business document
- **Messages**: Comments, notes, emails, notifications
- **Followers**: Subscribe users/partners to documents for notifications
- **Activities**: Scheduled tasks and to-dos
- **Notifications**: In-app and email notifications
- **Tracking**: Automatic logging of field changes

Components:
- mail.thread: Mixin for adding messaging to any model
- mail.message: Message model for all communications
- mail.followers: Follower subscription management
- mail.activity: Activity/task management
- mail.activity.type: Activity type definitions
- mail.notification: Notification tracking

This module enables collaboration by adding discussion and activity
tracking to business documents.
    ''',
    'author': 'OpenFlow',
    'website': 'https://github.com/openflow/openflow',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'auto_install': True,
    'application': False,
    'license': 'LGPL-3',
}
