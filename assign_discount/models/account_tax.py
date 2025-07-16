from odoo import api, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    @api.model
    def _prepare_base_line_for_taxes_computation(self, record, **kwargs):
        """Convert a model record into a base_line dictionary for tax computation."""

        def load(field, fallback):
            return self._get_base_line_field_value_from_record(record, field, kwargs, fallback)

        return {
            **kwargs,
            'record': record,
            'id': load('id', 0),
            'product_id': load('product_id', self.env['product.product']),
            'tax_ids': load('tax_ids', self.env['account.tax']),
            'price_unit': load('price_unit', 0.0),
            'quantity': load('quantity', 0.0),
            'discount': load('discount', 0.0),
            'fixed_discount': load('fixed_discount', 0.0),
            'currency_id': load('currency_id', self.env['res.currency']),
            'special_mode': kwargs.get('special_mode', False),
            'special_type': kwargs.get('special_type', False),
            'rate': load('rate', 1.0),
            'sign': load('sign', 1.0),
            'is_refund': load('is_refund', False),
            'tax_tag_invert': load('tax_tag_invert', False),
            'partner_id': load('partner_id', self.env['res.partner']),
            'account_id': load('account_id', self.env['account.account']),
            'analytic_distribution': load('analytic_distribution', None),
            'deferred_start_date': load('deferred_start_date', False),
            'deferred_end_date': load('deferred_end_date', False),
        }

    @api.model
    def _add_tax_details_in_base_line(self, base_line, company, rounding_method=None):
        """
        Apply percentage and fixed discount to `price_unit`, then compute taxes.
        """

        # Apply percentage discount
        if base_line.get('discount', 0.0) and base_line.get('quantity', 0) > 0:
            base_line['price_unit'] *= (1 - base_line['discount'] / 100.0)

        # Apply fixed discount (per unit)
        if base_line.get('fixed_discount', 0.0) and base_line.get('quantity', 0) > 0:
            base_line['price_unit'] -= base_line['fixed_discount'] / base_line['quantity']
            base_line['price_unit'] = max(base_line['price_unit'], 0.0)

        # Compute tax details based on adjusted price_unit
        taxes_computation = base_line['tax_ids']._get_tax_details(
            price_unit=base_line['price_unit'],
            quantity=base_line['quantity'],
            precision_rounding=base_line['currency_id'].rounding,
            rounding_method=rounding_method or company.tax_calculation_rounding_method,
            product=base_line['product_id'],
            special_mode=base_line['special_mode'],
        )

        rate = base_line.get('rate', 1.0)

        tax_details = base_line['tax_details'] = {
            'raw_total_excluded_currency': taxes_computation['total_excluded'],
            'raw_total_excluded': taxes_computation['total_excluded'] / rate if rate else 0.0,
            'raw_total_included_currency': taxes_computation['total_included'],
            'raw_total_included': taxes_computation['total_included'] / rate if rate else 0.0,
            'taxes_data': [],
        }

        if company.tax_calculation_rounding_method == 'round_per_line':
            tax_details['raw_total_excluded'] = company.currency_id.round(tax_details['raw_total_excluded'])
            tax_details['raw_total_included'] = company.currency_id.round(tax_details['raw_total_included'])

        for tax_data in taxes_computation['taxes_data']:
            tax_amount = tax_data['tax_amount'] / rate if rate else 0.0
            base_amount = tax_data['base_amount'] / rate if rate else 0.0

            if company.tax_calculation_rounding_method == 'round_per_line':
                tax_amount = company.currency_id.round(tax_amount)
                base_amount = company.currency_id.round(base_amount)

            tax_details['taxes_data'].append({
                **tax_data,
                'raw_tax_amount_currency': tax_data['tax_amount'],
                'raw_tax_amount': tax_amount,
                'raw_base_amount_currency': tax_data['base_amount'],
                'raw_base_amount': base_amount,
            })

        return base_line

