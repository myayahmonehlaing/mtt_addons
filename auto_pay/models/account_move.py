from odoo import models, api, fields, _
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        help="The sale order this invoice is associated with",
        copy=False,
        index=True,
    )

    # @api.model
    # def create(self, vals):
    #     move = super().create(vals)
    #     _logger.info("Invoice created with origin: %s", move.invoice_origin)
    #     return move


    def action_post(self):
        res = super().action_post()

        for move in self:
            if move.move_type == 'out_invoice' and move.sale_order_id:
                sale_order = move.sale_order_id

                if sale_order and sale_order.payment_ids:
                    account = move.partner_id.property_account_receivable_id

                    payment_lines = sale_order.payment_ids.mapped('move_id.line_ids').filtered(
                        lambda l: l.account_id == account and not l.reconciled and l.credit > 0
                    )

                    invoice_lines = move.line_ids.filtered(
                        lambda l: l.account_id == account and not l.reconciled and l.debit > 0
                    )

                    lines_to_reconcile = payment_lines + invoice_lines
                    if lines_to_reconcile:
                        _logger.info("Reconciling payment lines and invoice lines for move %s", move.name)
                        lines_to_reconcile.reconcile()

        return res
