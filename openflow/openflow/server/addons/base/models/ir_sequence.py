"""
ir.sequence - Sequence Number Generator

Generates sequential numbers for documents (invoices, orders, etc.)
with customizable formatting.
"""
from datetime import datetime
from typing import Optional
from openflow.server.core.orm import Model, fields


class IrSequence(Model):
    """
    Sequences

    Generates sequential numbers with prefix, suffix, and padding.
    Used for document numbering (SO0001, INV0001, etc.)
    """
    _name = 'ir.sequence'
    _description = 'Sequence'
    _order = 'name'

    name = fields.Char(
        string='Sequence Name',
        required=True,
        index=True,
        help='Name of the sequence'
    )

    code = fields.Char(
        string='Sequence Code',
        required=True,
        index=True,
        help='Unique code to identify this sequence'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to disable this sequence'
    )

    implementation = fields.Selection(
        selection=[
            ('standard', 'Standard'),
            ('no_gap', 'No Gap'),
        ],
        string='Implementation',
        default='standard',
        required=True,
        help='Standard: faster but may have gaps. No Gap: slower but guarantees no gaps.'
    )

    # Number Configuration
    prefix = fields.Char(
        string='Prefix',
        help='Prefix value of the record (e.g., "SO" for sales orders)'
    )

    suffix = fields.Char(
        string='Suffix',
        help='Suffix value of the record'
    )

    number_next = fields.Integer(
        string='Next Number',
        required=True,
        default=1,
        help='Next number in the sequence'
    )

    number_increment = fields.Integer(
        string='Increment Number',
        required=True,
        default=1,
        help='Increment number of the record'
    )

    padding = fields.Integer(
        string='Number Padding',
        required=True,
        default=4,
        help='Number of digits to pad with zeros (e.g., 4 for 0001)'
    )

    # Date Configuration
    use_date_range = fields.Boolean(
        string='Use Date Range',
        default=False,
        help='Use date ranges for sequence numbering'
    )

    date_range_ids = fields.One2many(
        'ir.sequence.date_range',
        'sequence_id',
        string='Date Ranges',
        help='Date ranges for this sequence'
    )

    # Multi-Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help='Company this sequence belongs to'
    )

    def _get_prefix_suffix(self) -> tuple:
        """
        Get interpolated prefix and suffix

        Supports date interpolation in prefix/suffix:
        - %(year)s: 4-digit year
        - %(y)s: 2-digit year
        - %(month)s: 2-digit month
        - %(day)s: 2-digit day

        Returns:
            Tuple of (prefix, suffix)
        """
        self.ensure_one()

        def interpolate(s: Optional[str]) -> str:
            if not s:
                return ''

            now = datetime.now()
            return s % {
                'year': now.strftime('%Y'),
                'y': now.strftime('%y'),
                'month': now.strftime('%m'),
                'day': now.strftime('%d'),
            }

        return interpolate(self.prefix), interpolate(self.suffix)

    async def next_by_id(self) -> str:
        """
        Get next sequence number

        Returns:
            Next sequence number as formatted string
        """
        self.ensure_one()

        # Get prefix and suffix with date interpolation
        prefix, suffix = self._get_prefix_suffix()

        # Check if we should use date range
        if self.use_date_range:
            date_range = await self._get_date_range()
            if date_range:
                return await date_range.next_by_id()

        # Get and increment the next number
        number = self.number_next

        # Update next number
        await self.write({
            'number_next': number + self.number_increment
        })

        # Format the number with padding
        formatted_number = str(number).zfill(self.padding)

        # Return full sequence
        return f"{prefix}{formatted_number}{suffix}"

    async def _get_date_range(self):
        """
        Get date range for current date

        Returns:
            Date range record or None
        """
        if not self.use_date_range:
            return None

        today = datetime.now().date()

        # Find date range that includes today
        date_ranges = await self.env['ir.sequence.date_range'].search([
            ('sequence_id', '=', self.id),
            ('date_from', '<=', today),
            ('date_to', '>=', today),
        ], limit=1)

        if date_ranges:
            return date_ranges

        # Create new date range for this year if not exists
        return await self._create_date_range_for_year(today.year)

    async def _create_date_range_for_year(self, year: int):
        """
        Create date range for a specific year

        Args:
            year: Year to create range for

        Returns:
            New date range record
        """
        date_from = datetime(year, 1, 1).date()
        date_to = datetime(year, 12, 31).date()

        return await self.env['ir.sequence.date_range'].create({
            'sequence_id': self.id,
            'date_from': date_from,
            'date_to': date_to,
            'number_next': 1,
        })

    def __repr__(self):
        return f"<IrSequence {self.name} ({self.code})>"


class IrSequenceDateRange(Model):
    """
    Sequence Date Ranges

    Allows sequences to reset per date range (e.g., per year).
    """
    _name = 'ir.sequence.date_range'
    _description = 'Sequence Date Range'
    _order = 'date_from desc'

    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Sequence',
        required=True,
        index=True,
        help='Parent sequence'
    )

    date_from = fields.Date(
        string='From',
        required=True,
        help='Start date of this range'
    )

    date_to = fields.Date(
        string='To',
        required=True,
        help='End date of this range'
    )

    number_next = fields.Integer(
        string='Next Number',
        required=True,
        default=1,
        help='Next number for this date range'
    )

    async def next_by_id(self) -> str:
        """
        Get next sequence number for this date range

        Returns:
            Next sequence number as formatted string
        """
        self.ensure_one()

        # Get prefix and suffix from parent sequence
        prefix, suffix = self.sequence_id._get_prefix_suffix()

        # Get and increment the next number
        number = self.number_next

        # Update next number
        await self.write({
            'number_next': number + self.sequence_id.number_increment
        })

        # Format the number with padding
        formatted_number = str(number).zfill(self.sequence_id.padding)

        # Return full sequence
        return f"{prefix}{formatted_number}{suffix}"

    def __repr__(self):
        seq_name = self.sequence_id.name if self.sequence_id else 'N/A'
        return f"<IrSequenceDateRange {seq_name} {self.date_from} - {self.date_to}>"
