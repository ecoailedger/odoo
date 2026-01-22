"""
Auth Module Manifest

Provides advanced authentication features including:
- Session management
- API key authentication
- Audit logging
- JWT token support
"""

{
    'name': 'Authentication',
    'version': '1.0.0',
    'category': 'Security',
    'summary': 'Advanced authentication and session management',
    'description': '''
    Authentication Module
    =====================

    This module extends the base authentication system with:

    Features:
    ---------
    * Session Management: Track active user sessions
    * API Key Authentication: Token-based authentication for external systems
    * Audit Logging: Track login attempts and authentication events
    * JWT Token Support: Modern token-based authentication
    * Session Security: IP tracking, user agent detection, session timeout

    Models:
    -------
    * auth.session: User session tracking
    * auth.api.key: API key management
    * auth.log: Authentication audit trail
    ''',
    'author': 'OpenFlow',
    'website': 'https://openflow.example.com',
    'depends': ['base'],
    'data': [
        'security/auth.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
