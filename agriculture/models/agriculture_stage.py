from odoo import models, fields, api, _


class AgricultureStage(models.Model):
    _name = "agriculture.stage"
    _description = "Agriculture Stage"
    _table = "stage"

    name = fields.Char(string="Stage Name", required=True)
    product_id = fields.Many2one(
        'product.product',
        string="Related Product",
        domain="[('is_crop', '=', True)]",
        required=False,
        help="Select the agricultural product linked to this stage."
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )
    image_field = fields.Binary("Image")

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = f"{self.name} (Copy)"
        return super().copy(default)
