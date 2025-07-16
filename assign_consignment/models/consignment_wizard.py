from collections import defaultdict
from odoo import models, fields, api
from datetime import datetime


class ConsignmentReportWizard(models.TransientModel):
    _name = 'consignment.report.wizard'
    _description = 'Consignment Report Wizard'

    date_to = fields.Date(string='Date To', required=True, default=fields.Date.today)

    def _prepare_report_data(self):
        domain = [('state', '!=', 'draft')]
        if self.date_to:
            domain.append(('date', '<=', self.date_to))

        consignments = self.env['assign.consignment'].search(domain)

        data = {}
        customers = set()
        products_set = set()

        for consignment in consignments:
            if not consignment.partner_id:
                continue
            customer_name = consignment.partner_id.name
            customers.add(customer_name)

            for line in consignment.order_line_ids:
                if line.product_id:
                    product_name = line.product_id.name
                    products_set.add(product_name)  # Add to the set
                    initial_qty = line.quantity
                    sale_lines = self.env['sale.order.line'].search([
                        ('order_id.consignment_id', '=', consignment.id),
                        ('product_id', '=', line.product_id.id),
                        ('order_id.state', 'not in', ['cancel', 'draft']),
                        ('order_id.date_order', '<=', self.date_to)
                    ])

                    sold_qty = sum(sale_lines.mapped('product_uom_qty'))
                    remaining_qty = max(initial_qty - sold_qty, 0)

                    if product_name not in data:
                        data[product_name] = {}
                    data[product_name][customer_name] = data[product_name].get(customer_name, 0.0) + remaining_qty

        sorted_product_names = sorted(products_set)
        products_with_serial = []
        for i, prod_name in enumerate(sorted_product_names):
            products_with_serial.append({
                'serial': i + 1,
                'name': prod_name
            })

        report_values = {
            'date_to': self.date_to.strftime('%Y-%m-%d'),
            'data_matrix': data,  # Renamed for clarity in QWeb
            'sorted_customers': sorted(customers),
            'products_with_serial': products_with_serial,  # Pass the new list with serials
            'user_name': self.env.user.name,
            'current_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return report_values

    def action_print_pdf_report(self):
        data = self._prepare_report_data()
        return self.env.ref('assign_consignment.action_consignment_report_pdf').report_action(self, data=data)

    def action_print_report(self):
        data = {
            'date_to': self.date_to,
            'wizard_id': self.id
        }
        return self.env.ref('assign_consignment.action_consignment_report_xlsx').report_action(self, data=data)

    def action_view_pivot(self):
        data = self._prepare_report_data()
        self.env['consignment.pivot.data'].search([]).unlink()


        PivotData = self.env['consignment.pivot.data']
        pivot_records = []

        for product in data['products_with_serial']:
            product_name = product['name']
            for customer in data['sorted_customers']:
                qty = data['data_matrix'].get(product_name, {}).get(customer, 0.0)


                product_record = self.env['product.product'].search([('name', '=', product_name)], limit=1)
                customer_record = self.env['res.partner'].search([('name', '=', customer)], limit=1)

                if product_record and customer_record:
                    pivot_records.append({
                        'product_id': product_record.id,
                        'customer_id': customer_record.id,
                        'remaining_qty': qty,
                        'date_to': self.date_to
                    })


        if pivot_records:
            PivotData.create(pivot_records)

        # Return the pivot view action
        return {
            'type': 'ir.actions.act_window',
            'name': f'Consignment Remaining Quantity as of {self.date_to}',
            'res_model': 'consignment.pivot.data',
            'view_mode': 'pivot',
            'views': [(False, 'pivot')],
            'target': 'current',
            'context': {'search_default_group_by_product': True},
        }
