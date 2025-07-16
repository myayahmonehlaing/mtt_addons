# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessError


class AccountMove(models.Model):
    _inherit = 'account.move'


    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        default=lambda self: self.env.user.department_id.id,
        readonly=False,
    )



    def action_post(self):

        is_department_accounting = self.env.user.has_group('assign_security_department_document.group_department_accounting')

        if not (self.env.user.has_group('account.group_account_invoice') or is_department_accounting):
            raise AccessError("You do not have the required group to post this invoice.")

        if is_department_accounting:
            return super(AccountMove, self.sudo()).action_post()
        else:
            return super().action_post()
