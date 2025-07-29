from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    stage_id = fields.One2many(
        'agriculture.stage',
        'product_id',
        string="Agricultural Stages"
    )
