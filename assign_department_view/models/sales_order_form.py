from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        default=lambda self: self.env.user.department_id.id,
        readonly=False,
    )

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals['department_id'] = self.department_id.id
        return invoice_vals

    # @api.depends('user_id','department_id')
    # def _compute_department(self):
    #     for order in self:
    #         if order.user_id and order.user_id.department_id:
    #
    #             order.department_id = order.user_id.department_id
    #         else:
    #             order.department_id = False
