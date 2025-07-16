from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    consignment_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Consignment Warehouse",
        domain="[('company_id', '=', id)]",
        help="Warehouse containing the consignment location"
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    consignment_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Consignment Warehouse",
        related='company_id.consignment_warehouse_id',
        readonly=False,
        domain="[('company_id', '=', company_id)]",
        help="Warehouse containing the consignment location"
    )

    consignment_location_id = fields.Many2one(
        'stock.location',
        string="Consignment Location (Auto)",
        related='consignment_warehouse_id.lot_stock_id',
        readonly=True
    )

# from odoo import models, fields, api
#
#
# class ResConfigSettings(models.TransientModel):
#     _inherit = 'res.config.settings'
#
#     company_id = fields.Many2one(
#         'res.company',
#         string='Company',
#         required=True,
#         default=lambda self: self.env.company,
#         readonly=False
#     )
#
#     consignment_warehouse_id = fields.Many2one(
#         'stock.warehouse',
#         string="Consignment Warehouse",
#         compute='_compute_consignment_warehouse',
#         inverse='_inverse_consignment_warehouse',
#         domain="[('company_id', '=', company_id)]",
#         store=True,
#         help="Warehouse containing the consignment location"
#     )
#
#     consignment_location_id = fields.Many2one(
#         'stock.location',
#         string="Consignment Location (Auto)",
#         compute='_compute_consignment_location',
#         readonly=True
#     )
#
#     # --- Compute consignment warehouse per company ---
#     @api.depends('company_id')
#     def _compute_consignment_warehouse(self):
#         for record in self:
#             warehouse_id = self.env['ir.config_parameter'].sudo().get_param(
#                 f'assign_consignment.consignment_warehouse_id_{record.company_id.id}'
#             )
#             record.consignment_warehouse_id = int(warehouse_id) if warehouse_id and warehouse_id.isdigit() else False
#
#     # --- Save the selected warehouse for current company ---
#     def _inverse_consignment_warehouse(self):
#         for record in self:
#             key = f'assign_consignment.consignment_warehouse_id_{record.company_id.id}'
#             value = str(record.consignment_warehouse_id.id) if record.consignment_warehouse_id else ''
#             self.env['ir.config_parameter'].sudo().set_param(key, value)
#
#     # --- Filter domain when switching company in settings UI ---
#     @api.onchange('company_id')
#     def _onchange_company_id(self):
#         return {
#             'domain': {
#                 'consignment_warehouse_id': [('company_id', '=', self.company_id.id)]
#             }
#         }
#
#     # --- Compute the lot_stock_id of the selected warehouse ---
#     @api.depends('consignment_warehouse_id')
#     def _compute_consignment_location(self):
#         for record in self:
#             warehouse = record.consignment_warehouse_id
#             if warehouse and warehouse.company_id == record.company_id:
#                 record.consignment_location_id = warehouse.lot_stock_id
#                 self.env['ir.config_parameter'].sudo().set_param(
#                     f'assign_consignment.consignment_location_id_{record.company_id.id}',
#                     warehouse.lot_stock_id.id
#                 )
#             else:
#                 record.consignment_location_id = False
#
