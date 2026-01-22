{
    'name': 'Repairs',
    'version': '1.0.0',
    'category': 'Services',
    'summary': 'Repair Order and RMA Management',
    'description': '''
Repair Module - Repair Orders and RMA
======================================

Complete repair order management system:

Features:
- **Repair Orders**: Track item repairs from receipt to delivery
- **State Workflow**: Draft → Confirmed → Under Repair → Repaired → Done
- **Operations**: Track labor and operations performed
- **Parts/Fees**: Track parts used and additional fees
- **Invoicing**: Generate invoices before or after repair
- **Warranty**: Track warranty information and expiry
- **Stock Integration**: Move parts from inventory
- **Helpdesk Integration**: Create repairs from helpdesk tickets
- **Chatter**: Full messaging and activity tracking

Components:
- repair.order: Main repair order document
- repair.line: Labor/operations on the repair
- repair.fee: Parts and additional fees

Workflow:
1. Customer brings item for repair
2. Create repair order with quotation
3. Customer approves quotation
4. Perform repairs (track operations and parts)
5. Complete repair and invoice customer
6. Deliver repaired item
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
