# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SalePaymentWizard(models.TransientModel):
    _name = 'sale.payment.wizard'
    _description = 'Sale Payment Wizard'

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        required=True,
        ondelete='cascade',
        help="The Sale Order for which the payment is being made."
    )
    partner_bank_id = (fields.Many2one
                       ('res.partner.bank',
                        string="Recipient Bank Account",
                        readonly=False,
                        store=True,
                        tracking=True,
                        ondelete='restrict',
                        ))

    amount = fields.Monetary(
        string='Amount',
        required=True,
        help="The amount to be paid."
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="The currency of the payment amount."
    )

    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        domain="[('type', 'in', ('bank', 'cash'))]",
        help="The journal through which the payment will be recorded."
    )

    payment_method_line_id = fields.Many2one(
        'account.payment.method.line',
        string='Payment Method',
        required=True,
        domain="[('journal_id', '=', journal_id),('payment_type', '=', 'inbound')]",
        help="The payment method used for this payment."
    )

    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.context_today,
        help="The date on which the payment is made."
    )

    communication = fields.Char(
        string='Memo',
        default=lambda self: self._context.get('default_sale_order_id', ''),
        help="A short description or reference for the payment."
    )

    @api.onchange('sale_order_id')
    def _onchange_sale_order_id(self):
        """Sets the default amount, currency, and memo based on the selected sale order."""
        if self.sale_order_id:
            self.amount = self.sale_order_id.amount_total
            self.currency_id = self.sale_order_id.currency_id
            self.communication = self.sale_order_id.name

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        """Update payment methods when journal changes and set default method."""
        if self.journal_id:
            methods = self.journal_id._get_available_payment_method_lines('inbound')
            self.payment_method_line_id = methods[0] if methods else False
            return {'domain': {
                'payment_method_line_id': [('id', 'in', methods.ids)]
            }}
        else:
            self.payment_method_line_id = False
            return {'domain': {
                'payment_method_line_id': []
            }}

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        journal = self.env['account.journal'].search([('type', 'in', ('bank', 'cash'))], limit=1)
        if journal:
            res['journal_id'] = journal.id
            # Filter only inbound payment methods
            methods = journal._get_available_payment_method_lines('inbound').filtered(
                lambda m: m.payment_type == 'inbound'
            )
            method_ids = list(set(methods.ids))
            if method_ids:
                res['payment_method_line_id'] = method_ids[0]
        return res

    def action_create_payment(self):
        """
        Creates a payment record and automatically reconciles with invoice if exists
        """
        self.ensure_one()

        if self.amount <= 0:
            raise ValidationError(_("The payment amount must be positive."))

        # Prepare payment data
        payment_data = {
            'amount': self.amount,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'currency_id': self.currency_id.id,
            'journal_id': self.journal_id.id,
            'payment_method_line_id': self.payment_method_line_id.id,
            'date': self.payment_date,
            'memo': self.communication,
            'partner_id': self.sale_order_id.partner_id.id,
            'sale_order_id': self.sale_order_id.id,
        }

        # Create and post payment
        payment = self.env['account.payment'].create(payment_data)
        payment.action_post()

        return {
            'type': 'ir.actions.act_window_close',
            'context': {'payment_created': True}
        }
