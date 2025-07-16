from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_checked = fields.Boolean(string="My Checkbox")
