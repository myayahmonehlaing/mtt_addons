import logging
from odoo import api, fields, models, Command, _
from odoo.tools import frozendict, mute_logger, date_utils, SQL

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    fixed_discount = fields.Float(
        string="Fixed Discount",
        digits="Product Price",
        default=0.0,
        help="Fixed amount discount for this line.",
    )

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id', 'fixed_discount')
    def _compute_totals(self):
        super(AccountMoveLine, self)._compute_totals()
        AccountTax = self.env['account.tax']
        for line in self:

            if line.display_type not in ('product', 'cogs'):
                line.price_total = line.price_subtotal = 0.0
                continue

            base_line = line.move_id._prepare_product_base_line_for_taxes_computation(line)

            AccountTax._add_tax_details_in_base_line(base_line, line.company_id)

            # Compute the price_subtotal and price_total from the tax details.
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']

    @api.depends('account_id', 'company_id', 'discount', 'fixed_discount', 'price_unit', 'quantity',
                 'currency_rate')  # Added 'fixed_discount' to depends
    def _compute_discount_allocation_needed(self):
        for line in self:
            line.discount_allocation_dirty = True
            discount_allocation_account = line.move_id._get_discount_allocation_account()

            # Ensure fixed_discount is also considered for the condition
            if not discount_allocation_account or line.display_type != 'product' or (
                    line.currency_id.is_zero(line.discount) and line.currency_id.is_zero(line.fixed_discount)):
                line.discount_allocation_needed = False
                continue

            # Calculate total discount amount in currency
            # Percentage discount
            percentage_discount_amount = line.quantity * line.price_unit * line.discount / 100.0
            # Fixed discount per line
            total_fixed_discount_amount = line.fixed_discount

            # Combine both discounts
            total_discount_amount_currency = line.currency_id.round(
                line.move_id.direction_sign * (percentage_discount_amount + total_fixed_discount_amount))

            discount_allocation_needed = {}
            # Debit the product sales account for the discount amount
            discount_allocation_needed_vals = discount_allocation_needed.setdefault(
                frozendict({
                    'account_id': line.account_id.id,
                    'move_id': line.move_id.id,
                    'currency_rate': line.currency_rate,
                }),
                {
                    'display_type': 'discount',
                    'name': _("Discount"),
                    'amount_currency': 0.0,
                },
            )
            discount_allocation_needed_vals['amount_currency'] += total_discount_amount_currency

            # Credit the discount allocation account (e.g., Cash Discount Loss) for the discount amount
            discount_allocation_needed_vals = discount_allocation_needed.setdefault(
                frozendict({
                    'move_id': line.move_id.id,
                    'account_id': discount_allocation_account.id,
                    'currency_rate': line.currency_rate,
                }),
                {
                    'display_type': 'discount',
                    'name': _("Discount"),
                    'amount_currency': 0.0,
                },
            )
            discount_allocation_needed_vals['amount_currency'] -= total_discount_amount_currency
            line.discount_allocation_needed = {k: frozendict(v) for k, v in discount_allocation_needed.items()}
