from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        default=lambda self: self.env.user.department_id.id,
        readonly=False,
    )

    # @api.depends('invoice_user_id','department_id')
    # def _compute_department(self):
    #     for invoice in self:
    #         if invoice.invoice_user_id and invoice.invoice_user_id.department_id:
    #             invoice.department_id = invoice.invoice_user_id.department_id
    #         else:
    #             invoice.department_id = False


