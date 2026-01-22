"""
account.move - Invoices and Bills

Main accounting document for invoices and vendor bills.
"""
from datetime import datetime
from openflow.server.core.orm import Model, fields


class AccountMove(Model):
    """
    Account Moves (Invoices/Bills)

    Represents customer invoices, vendor bills, and credit notes.
    """
    _name = 'account.move'
    _description = 'Invoice'
    _inherit = ['mail.thread']
    _order = 'date desc, name desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Number',
        required=True,
        default='New',
        index=True,
        help='Invoice number'
    )

    # Type
    move_type = fields.Selection(
        selection=[
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
            ('in_invoice', 'Vendor Bill'),
            ('in_refund', 'Vendor Credit Note'),
        ],
        string='Type',
        required=True,
        default='out_invoice',
        index=True,
        help='Type of invoice'
    )

    # Partner
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        index=True,
        help='Customer or vendor'
    )

    partner_name = fields.Char(
        string='Partner Name',
        related='partner_id.name',
        readonly=True
    )

    # Dates
    invoice_date = fields.Date(
        string='Invoice Date',
        default=lambda self: datetime.now().date(),
        required=True,
        index=True,
        help='Invoice date'
    )

    invoice_date_due = fields.Date(
        string='Due Date',
        help='Payment due date'
    )

    date = fields.Date(
        string='Accounting Date',
        related='invoice_date',
        help='Date for accounting purposes'
    )

    # Journal
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        help='Accounting journal'
    )

    # Currency
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        help='Invoice currency'
    )

    # State
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        index=True,
        help='Invoice status'
    )

    # Payment State
    payment_state = fields.Selection(
        selection=[
            ('not_paid', 'Not Paid'),
            ('in_payment', 'In Payment'),
            ('paid', 'Paid'),
            ('partial', 'Partially Paid'),
            ('reversed', 'Reversed'),
        ],
        string='Payment Status',
        compute='_compute_payment_state',
        store=True,
        help='Payment status'
    )

    # Lines
    line_ids = fields.One2many(
        'account.move.line',
        'move_id',
        string='Invoice Lines',
        help='Invoice line items'
    )

    # Amounts
    amount_untaxed = fields.Float(
        string='Untaxed Amount',
        compute='_compute_amounts',
        store=True,
        help='Total without taxes'
    )

    amount_tax = fields.Float(
        string='Tax',
        compute='_compute_amounts',
        store=True,
        help='Total tax amount'
    )

    amount_total = fields.Float(
        string='Total',
        compute='_compute_amounts',
        store=True,
        help='Total with taxes'
    )

    amount_residual = fields.Float(
        string='Amount Due',
        compute='_compute_amounts',
        store=True,
        help='Remaining amount to pay'
    )

    # References
    ref = fields.Char(
        string='Reference',
        help='External reference (vendor bill number, etc.)'
    )

    invoice_origin = fields.Char(
        string='Origin',
        help='Source document (sales order, repair order, etc.)'
    )

    # Notes
    narration = fields.Text(
        string='Terms and Conditions',
        help='Terms and conditions to print on invoice'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        help='Company issuing the invoice'
    )

    # Related Documents
    repair_id = fields.Many2one(
        'repair.order',
        string='Repair Order',
        help='Related repair order'
    )

    def _compute_amounts(self):
        """Compute invoice amounts from lines"""
        for move in self:
            amount_untaxed = 0.0
            amount_tax = 0.0

            for line in move.line_ids:
                if hasattr(line, 'price_subtotal'):
                    amount_untaxed += line.price_subtotal
                if hasattr(line, 'price_tax'):
                    amount_tax += line.price_tax

            move.amount_untaxed = amount_untaxed
            move.amount_tax = amount_tax
            move.amount_total = amount_untaxed + amount_tax

            # Simplified - would track payments in full implementation
            if move.state == 'posted':
                move.amount_residual = move.amount_total
            else:
                move.amount_residual = 0.0

    def _compute_payment_state(self):
        """Compute payment state"""
        for move in self:
            if move.state != 'posted':
                move.payment_state = False
            elif move.amount_residual == 0.0:
                move.payment_state = 'paid'
            elif move.amount_residual == move.amount_total:
                move.payment_state = 'not_paid'
            else:
                move.payment_state = 'partial'

    async def create(self, vals):
        """Override create to generate invoice number"""
        if vals.get('name', 'New') == 'New':
            move_type = vals.get('move_type', 'out_invoice')

            # Determine sequence code based on type
            if move_type == 'out_invoice':
                code = 'account.move.out_invoice'
            elif move_type == 'out_refund':
                code = 'account.move.out_refund'
            elif move_type == 'in_invoice':
                code = 'account.move.in_invoice'
            else:
                code = 'account.move.in_refund'

            sequence = await self.env['ir.sequence'].search([
                ('code', '=', code)
            ], limit=1)

            if sequence:
                vals['name'] = await sequence.next_by_id()
            else:
                prefix = 'INV' if 'out' in move_type else 'BILL'
                vals['name'] = f"{prefix}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return await super().create(vals)

    async def action_post(self):
        """Post the invoice (make it official)"""
        await self.write({'state': 'posted'})
        await self.message_post(
            body='Invoice posted',
            message_type='notification'
        )

    async def action_cancel(self):
        """Cancel the invoice"""
        await self.write({'state': 'cancel'})
        await self.message_post(
            body='Invoice cancelled',
            message_type='notification'
        )

    async def action_draft(self):
        """Reset to draft"""
        await self.write({'state': 'draft'})

    def __repr__(self):
        return f"<AccountMove {self.name}: {self.partner_id.name if self.partner_id else 'N/A'}>"
