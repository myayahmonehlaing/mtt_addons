from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_crop = fields.Boolean(string="Is Crop", help="Check if this product is an agricultural crop")
    is_seed = fields.Boolean(string="Is Seed", help="Check if this product is an agricultural seed")
    is_expense = fields.Boolean(string="Is Expense", help="Check if this product is an agricultural expense")

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )
