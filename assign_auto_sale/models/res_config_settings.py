from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_shipping = fields.Boolean(
        string="Auto Shipping",
        config_parameter='sale.auto_shipping'
    )

    auto_create_invoice = fields.Boolean(
        string="Auto Create Invoice",
        config_parameter='sale.auto_create_invoice'
    )

    