from odoo import api, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends('order_line.price_total')
    def _compute_amounts(self):
        """Compute the totals for the order."""
        super(SaleOrder, self)._compute_amounts()
