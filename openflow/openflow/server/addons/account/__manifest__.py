{
    'name': 'Accounting',
    'version': '1.0.0',
    'category': 'Accounting',
    'summary': 'Basic Invoicing and Accounting',
    'description': '''
Account Module - Basic Invoicing
=================================

Simplified invoicing for repairs and sales:

Features:
- **Invoices**: Customer and vendor invoices
- **Invoice Lines**: Line items with products and taxes
- **Taxes**: Tax definitions with automatic calculation
- **Journals**: Accounting journals (sales, purchase)
- **Payment States**: Track invoice payment status
- **Credit Notes**: Create refunds/credit notes
- **Email**: Send invoices by email

Components:
- account.move: Invoices and bills
- account.move.line: Invoice line items
- account.tax: Tax definitions
- account.journal: Accounting journals
- account.payment: Payment registration

This is a simplified version focused on invoicing for
repairs and sales orders.
    ''',
    'author': 'OpenFlow',
    'website': 'https://github.com/openflow/openflow',
    'depends': ['base'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
