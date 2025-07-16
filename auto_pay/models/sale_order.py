from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    payment_ids = fields.One2many(
        'account.payment',
        'sale_order_id',
        string='Payments',
        help="Payments made for this sale order"
    )

    def _create_invoices(self, grouped=False, final=False, date=None):
        invoices = super()._create_invoices(grouped=grouped, final=final, date=date)

        for invoice in invoices:
            if invoice.move_type in ('out_invoice', 'out_refund'):
                invoice.sale_order_id = self.id

        return invoices

    def action_open_payment_wizard(self):
        self.ensure_one()
        return {
            'name': _('Pay'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_amount': self.amount_total,
            }
        }

    def action_view_payments(self):
        self.ensure_one()
        return {
            'name': _('Payments'),
            'view_mode': 'list,form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'create': False}
        }

    payment_count = fields.Integer(
        string="Payment Count",
        compute='_compute_payment_count',
        store=True
    )

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for order in self:
            order.payment_count = len(order.payment_ids)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        help="The sale order this payment is associated with"
    )
