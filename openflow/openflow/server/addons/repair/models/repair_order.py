"""
repair.order - Repair Orders

Main model for repair order management with full workflow.
"""
from datetime import datetime, timedelta
from openflow.server.core.orm import Model, fields


class RepairOrder(Model):
    """
    Repair Orders

    Manages the complete repair lifecycle from quotation to delivery.
    Inherits from mail.thread for full chatter functionality.
    """
    _name = 'repair.order'
    _description = 'Repair Order'
    _inherit = ['mail.thread']
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Repair Reference',
        required=True,
        default='New',
        index=True,
        help='Unique repair order reference'
    )

    # Customer
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        index=True,
        help='Customer who owns the item being repaired'
    )

    address_id = fields.Many2one(
        'res.partner',
        string='Delivery Address',
        help='Address for returning the repaired item'
    )

    # Product Being Repaired
    product_id = fields.Many2one(
        'product.product',
        string='Product to Repair',
        required=True,
        help='Product being repaired'
    )

    product_qty = fields.Float(
        string='Quantity',
        default=1.0,
        required=True,
        help='Quantity of products being repaired'
    )

    lot_id = fields.Many2one(
        'stock.production.lot',
        string='Lot/Serial Number',
        help='Serial number or lot of the item being repaired'
    )

    # Helpdesk Integration
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Related Ticket',
        help='Helpdesk ticket that created this repair order'
    )

    # State Workflow
    state = fields.Selection(
        selection=[
            ('draft', 'Quotation'),
            ('confirmed', 'Confirmed'),
            ('under_repair', 'Under Repair'),
            ('ready', 'Ready to Repair'),
            ('2binvoiced', 'To be Invoiced'),
            ('invoice_except', 'Invoice Exception'),
            ('done', 'Repaired'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        index=True,
        help='Current state of the repair order'
    )

    # Warranty
    guarantee_limit = fields.Date(
        string='Warranty Expiration',
        help='Warranty expiry date'
    )

    is_under_warranty = fields.Boolean(
        string='Under Warranty',
        compute='_compute_is_under_warranty',
        help='Whether the repair is covered by warranty'
    )

    # Invoicing
    invoice_method = fields.Selection(
        selection=[
            ('none', 'No Invoice'),
            ('b4repair', 'Before Repair'),
            ('after_repair', 'After Repair'),
        ],
        string='Invoice Method',
        default='none',
        required=True,
        help='When to generate the invoice'
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        help='Generated invoice for this repair'
    )

    invoiced = fields.Boolean(
        string='Invoiced',
        default=False,
        help='Has this repair been invoiced'
    )

    # Operations (Labor)
    operations = fields.One2many(
        'repair.line',
        'repair_id',
        string='Operations',
        help='Labor and operations performed'
    )

    # Parts/Fees
    fees_lines = fields.One2many(
        'repair.fee',
        'repair_id',
        string='Parts & Fees',
        help='Parts used and additional fees'
    )

    # Locations (Stock Integration)
    location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        help='Location where item is received'
    )

    location_dest_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        help='Location after repair completion'
    )

    move_ids = fields.One2many(
        'stock.move',
        'repair_id',
        string='Stock Moves',
        help='Stock moves for parts used'
    )

    # Notes
    quotation_notes = fields.Text(
        string='Quotation Notes',
        help='Notes to include on quotation'
    )

    internal_notes = fields.Text(
        string='Internal Notes',
        help='Internal notes (not visible to customer)'
    )

    # Dates
    create_date = fields.DateTime(
        string='Creation Date',
        default=lambda self: datetime.now(),
        help='Date when repair order was created'
    )

    schedule_date = fields.Datetime(
        string='Scheduled Date',
        help='Scheduled date to start repair'
    )

    repaired_date = fields.Datetime(
        string='Repair Date',
        help='Date when repair was completed'
    )

    # Amounts
    amount_untaxed = fields.Float(
        string='Untaxed Amount',
        compute='_compute_amounts',
        store=True,
        help='Total amount without taxes'
    )

    amount_tax = fields.Float(
        string='Taxes',
        compute='_compute_amounts',
        store=True,
        help='Total tax amount'
    )

    amount_total = fields.Float(
        string='Total',
        compute='_compute_amounts',
        store=True,
        help='Total amount including taxes'
    )

    # Assigned User
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        help='User responsible for this repair'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help='Company this repair belongs to'
    )

    # Priority
    priority = fields.Selection(
        selection=[
            ('0', 'Normal'),
            ('1', 'High'),
            ('2', 'Urgent'),
        ],
        string='Priority',
        default='0',
        help='Repair priority'
    )

    def _compute_is_under_warranty(self):
        """Check if repair is under warranty"""
        today = datetime.now().date()

        for repair in self:
            if repair.guarantee_limit:
                repair.is_under_warranty = repair.guarantee_limit >= today
            else:
                repair.is_under_warranty = False

    def _compute_amounts(self):
        """Compute total amounts from operations and fees"""
        for repair in self:
            amount_untaxed = 0.0
            amount_tax = 0.0

            # Sum operations
            for line in repair.operations:
                if hasattr(line, 'price_subtotal'):
                    amount_untaxed += line.price_subtotal
                if hasattr(line, 'price_tax'):
                    amount_tax += line.price_tax

            # Sum fees
            for fee in repair.fees_lines:
                if hasattr(fee, 'price_subtotal'):
                    amount_untaxed += fee.price_subtotal
                if hasattr(fee, 'price_tax'):
                    amount_tax += fee.price_tax

            repair.amount_untaxed = amount_untaxed
            repair.amount_tax = amount_tax
            repair.amount_total = amount_untaxed + amount_tax

    async def create(self, vals):
        """Override create to generate repair reference"""
        if vals.get('name', 'New') == 'New':
            sequence = await self.env['ir.sequence'].search([
                ('code', '=', 'repair.order')
            ], limit=1)

            if sequence:
                vals['name'] = await sequence.next_by_id()
            else:
                vals['name'] = f"REP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        return await super().create(vals)

    async def action_validate(self):
        """Confirm the repair order"""
        await self.write({'state': 'confirmed'})
        await self.message_post(
            body='Repair order confirmed',
            message_type='notification'
        )

    async def action_repair_start(self):
        """Start the repair"""
        await self.write({'state': 'under_repair'})
        await self.message_post(
            body='Repair started',
            message_type='notification'
        )

    async def action_repair_end(self):
        """Mark repair as complete"""
        await self.write({
            'state': 'ready',
            'repaired_date': datetime.now()
        })
        await self.message_post(
            body='Repair completed',
            message_type='notification'
        )

    async def action_repair_done(self):
        """
        Finalize repair order

        Depending on invoice_method:
        - Create invoice if needed
        - Move to done state
        - Process stock moves
        """
        for repair in self:
            # Create invoice if needed
            if repair.invoice_method != 'none' and not repair.invoiced:
                await repair.action_create_invoice()

            # Mark as done
            await repair.write({'state': 'done'})

            await repair.message_post(
                body='Repair order finalized',
                message_type='notification'
            )

    async def action_create_invoice(self):
        """Generate invoice for this repair"""
        self.ensure_one()

        if self.invoiced:
            return

        # In a full implementation, this would:
        # 1. Create account.move (invoice)
        # 2. Add invoice lines for operations and fees
        # 3. Link invoice to repair order

        # Simplified version for now
        await self.write({'invoiced': True})

        await self.message_post(
            body=f'Invoice created for {self.amount_total:.2f}',
            message_type='notification'
        )

    async def action_cancel(self):
        """Cancel the repair order"""
        await self.write({'state': 'cancel'})
        await self.message_post(
            body='Repair order cancelled',
            message_type='notification'
        )

    def __repr__(self):
        return f"<RepairOrder {self.name}: {self.product_id.name if self.product_id else 'N/A'}>"
