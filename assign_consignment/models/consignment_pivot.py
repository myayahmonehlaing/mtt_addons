from odoo import models, fields, api


class ConsignmentPivotData(models.Model):
    _name = 'consignment.pivot.data'
    _description = 'Consignment Pivot Data'
    _log_access = True

    product_id = fields.Many2one('product.product', string='Product')
    customer_id = fields.Many2one('res.partner', string='Customer')
    remaining_qty = fields.Float(string='Remaining Quantity')
    date_to = fields.Date(string='As of Date')

    @api.model
    def init(self):
        pass
