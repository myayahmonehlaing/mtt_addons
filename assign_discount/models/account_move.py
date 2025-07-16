from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"


    def _prepare_product_base_line_for_taxes_computation(self, product_line):

        self.ensure_one()
        # Call the parent method to retain the original functionality
        base_line = super(AccountMove, self)._prepare_product_base_line_for_taxes_computation(product_line)

        is_invoice = self.is_invoice(include_receipts=True)
        if is_invoice:
            fixed_discount = getattr(product_line, 'fixed_discount', 0.0)
            base_line['fixed_discount'] = fixed_discount
        return base_line


    def _prepare_epd_base_lines_for_taxes_computation_from_base_lines(self, base_lines):

        epd_lines = super(AccountMove, self)._prepare_epd_base_lines_for_taxes_computation_from_base_lines(base_lines)


        for base_line in epd_lines:

            related_line = base_line.get('related_line')
            if related_line and hasattr(related_line,
                                        'fixed_discount') and related_line.fixed_discount > 0:  # Renamed field

                fixed_discount_per_unit = related_line.fixed_discount / related_line.quantity if related_line.quantity else 0.0
                base_line['price_unit'] -= fixed_discount_per_unit  # Adjusted to per unit.

        return epd_lines

    def _get_invoice_counterpart_amls_for_early_payment_discount(self, aml_values_list, open_balance):
        res = super(AccountMove, self)._get_invoice_counterpart_amls_for_early_payment_discount(aml_values_list,
                                                                                                open_balance)

        for aml_values in aml_values_list:
            aml = aml_values['aml']
            invoice = aml.move_id


            fixed_discount = invoice.invoice_payment_term_id.fixed_discount or 0.0
            if fixed_discount > 0:
                for key in ('base_lines', 'tax_lines', 'term_lines'):
                    for grouping_dict, vals in res[key].items():
                        vals['amount_currency'] -= fixed_discount
                        vals['balance'] -= aml.company_currency_id.round(fixed_discount)
                        open_balance -= aml.company_currency_id.round(fixed_discount)

        return res
