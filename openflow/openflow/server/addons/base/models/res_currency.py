"""
res.currency - Currencies and Exchange Rates

Multi-currency support with historical exchange rates.
"""
from datetime import datetime
from typing import Optional
from openflow.server.core.orm import Model, fields


class ResCurrency(Model):
    """
    Currencies

    Represents different currencies with their symbols, rounding rules,
    and exchange rates over time.
    """
    _name = 'res.currency'
    _description = 'Currency'
    _order = 'name'

    name = fields.Char(
        string='Currency',
        required=True,
        size=3,
        index=True,
        help='Currency code (ISO 4217)'
    )

    full_name = fields.Char(
        string='Full Name',
        translate=True,
        help='Full currency name (e.g., United States Dollar)'
    )

    symbol = fields.Char(
        string='Symbol',
        required=True,
        size=10,
        help='Currency symbol (e.g., $, €, £)'
    )

    position = fields.Selection(
        selection=[
            ('before', 'Before Amount'),
            ('after', 'After Amount'),
        ],
        string='Symbol Position',
        default='before',
        required=True,
        help='Position of currency symbol relative to amount'
    )

    rounding = fields.Float(
        string='Rounding Factor',
        default=0.01,
        required=True,
        help='Amounts in this currency are rounded to multiples of this value'
    )

    decimal_places = fields.Integer(
        string='Decimal Places',
        default=2,
        required=True,
        help='Number of decimal places for display'
    )

    rate_ids = fields.One2many(
        'res.currency.rate',
        'currency_id',
        string='Rates',
        help='Historical exchange rates for this currency'
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to hide the currency'
    )

    date = fields.Date(
        string='Date',
        compute='_compute_current_rate',
        help='Date of the current rate'
    )

    rate = fields.Float(
        string='Current Rate',
        compute='_compute_current_rate',
        help='Current exchange rate (1 base currency = X of this currency)'
    )

    inverse_rate = fields.Float(
        string='Inverse Rate',
        compute='_compute_current_rate',
        help='Inverse exchange rate (1 of this currency = X base currency)'
    )

    def _compute_current_rate(self):
        """Compute current exchange rate from rate_ids"""
        for currency in self:
            date = datetime.now().date()

            # Find the most recent rate for this currency
            if currency.rate_ids:
                # Get the most recent rate
                rates = sorted(
                    currency.rate_ids,
                    key=lambda r: r.name if hasattr(r, 'name') else date,
                    reverse=True
                )
                if rates:
                    latest_rate = rates[0]
                    currency.date = latest_rate.name if hasattr(latest_rate, 'name') else date
                    currency.rate = latest_rate.rate if hasattr(latest_rate, 'rate') else 1.0
                    currency.inverse_rate = (
                        1.0 / latest_rate.rate
                        if hasattr(latest_rate, 'rate') and latest_rate.rate
                        else 1.0
                    )
                else:
                    currency.date = date
                    currency.rate = 1.0
                    currency.inverse_rate = 1.0
            else:
                currency.date = date
                currency.rate = 1.0
                currency.inverse_rate = 1.0

    def get_rate(self, date: Optional[datetime] = None) -> float:
        """
        Get exchange rate for a specific date

        Args:
            date: Date to get rate for (defaults to today)

        Returns:
            Exchange rate for the specified date
        """
        self.ensure_one()

        if date is None:
            date = datetime.now().date()

        # Find rate for the specific date or closest earlier date
        rates = self.env['res.currency.rate'].search([
            ('currency_id', '=', self.id),
            ('name', '<=', date)
        ], order='name desc', limit=1)

        if rates:
            return rates.rate
        return 1.0

    def format(self, amount: float) -> str:
        """
        Format amount with currency symbol

        Args:
            amount: Numeric amount to format

        Returns:
            Formatted currency string (e.g., "$100.00")
        """
        self.ensure_one()

        # Round amount
        rounded = round(amount / self.rounding) * self.rounding

        # Format with decimal places
        formatted_amount = f"{rounded:,.{self.decimal_places}f}"

        # Add symbol in correct position
        if self.position == 'before':
            return f"{self.symbol}{formatted_amount}"
        else:
            return f"{formatted_amount}{self.symbol}"

    def round(self, amount: float) -> float:
        """
        Round amount according to currency rounding rules

        Args:
            amount: Amount to round

        Returns:
            Rounded amount
        """
        self.ensure_one()
        return round(amount / self.rounding) * self.rounding

    def compare_amounts(self, amount1: float, amount2: float) -> int:
        """
        Compare two amounts considering currency rounding

        Args:
            amount1: First amount
            amount2: Second amount

        Returns:
            -1 if amount1 < amount2, 0 if equal, 1 if amount1 > amount2
        """
        self.ensure_one()
        rounded1 = self.round(amount1)
        rounded2 = self.round(amount2)

        if rounded1 < rounded2:
            return -1
        elif rounded1 > rounded2:
            return 1
        return 0

    def is_zero(self, amount: float) -> bool:
        """
        Check if amount is zero considering currency rounding

        Args:
            amount: Amount to check

        Returns:
            True if amount rounds to zero
        """
        return self.compare_amounts(amount, 0.0) == 0

    def __repr__(self):
        return f"<ResCurrency {self.name} ({self.symbol})>"


class ResCurrencyRate(Model):
    """
    Currency Exchange Rates

    Historical exchange rates for currencies over time.
    """
    _name = 'res.currency.rate'
    _description = 'Currency Rate'
    _order = 'name desc'

    name = fields.Date(
        string='Date',
        required=True,
        index=True,
        default=lambda self: datetime.now().date(),
        help='Date of this exchange rate'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        index=True,
        help='Currency this rate applies to'
    )

    rate = fields.Float(
        string='Rate',
        required=True,
        default=1.0,
        help='Exchange rate: 1 base currency = X of this currency'
    )

    inverse_rate = fields.Float(
        string='Inverse Rate',
        compute='_compute_inverse_rate',
        help='Inverse rate: 1 of this currency = X base currency'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help='Company this rate applies to'
    )

    def _compute_inverse_rate(self):
        """Compute inverse exchange rate"""
        for rate_record in self:
            if rate_record.rate:
                rate_record.inverse_rate = 1.0 / rate_record.rate
            else:
                rate_record.inverse_rate = 0.0

    def __repr__(self):
        currency_name = self.currency_id.name if self.currency_id else 'N/A'
        return f"<ResCurrencyRate {currency_name} @ {self.name}: {self.rate}>"
