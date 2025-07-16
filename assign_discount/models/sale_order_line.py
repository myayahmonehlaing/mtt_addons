from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    fixed_discount = fields.Float(
        string="Fixed Discount",
        digits="Product Price",
        help="Fixed amount discount applied per line.",
    )

    @api.depends('fixed_discount', 'discount', 'price_unit', 'product_uom_qty', 'tax_id')
    def _compute_amount(self):
        super(SaleOrderLine, self)._compute_amount()

        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            self.env['account.tax']._add_tax_details_in_base_line(base_line, line.company_id)
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']
            line.price_tax = line.price_total - line.price_subtotal

    def _prepare_invoice_line(self, **optional_values):
        """Pass both fixed and percentage discounts to the invoice line."""
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        res.update({
            "fixed_discount": self.fixed_discount,
        })
        return res
