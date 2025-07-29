from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    billing_user_id = fields.Many2one(
        'res.users',
        string="Responsible User",
        help="Assigned manager responsible for this bill."
    )
