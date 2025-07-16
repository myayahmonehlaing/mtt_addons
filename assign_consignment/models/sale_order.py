from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    consignment_id = fields.Many2one(
        'assign.consignment',
        string='Consignment',
        domain="[('partner_id', '=', partner_id), ('picking_id.state', '=', 'done'), ('state', '=', 'confirm')]",
        help="Select a consignment with completed transfer"
    )

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=lambda self: self._get_default_warehouse()
    )

    def _get_default_warehouse(self):
        """Get default warehouse from company settings"""
        return self.env.company.consignment_warehouse_id or \
            self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Reset consignment and warehouse when partner changes"""
        res = super()._onchange_partner_id()
        self.update({
            'order_line': [(5, 0, 0)],
            'warehouse_id': self._get_default_warehouse(),
            'consignment_id': False
        })
        return res

    @api.onchange('consignment_id')
    def _onchange_consignment_id(self):
        """Update order lines and warehouse when consignment changes"""
        self.order_line = [(5, 0, 0)]

        if not self.consignment_id:
            self.warehouse_id = self._get_default_warehouse()
            return

        # Set warehouse from consignment's company settings
        self.warehouse_id = self.consignment_id.company_id.consignment_warehouse_id

        # Add consignment products to order lines
        for line in self.consignment_id.order_line_ids.filtered(lambda l: l.remaining_qty > 0):
            self.order_line += self.env['sale.order.line'].new({
                'order_id': self.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.remaining_qty,
                'price_unit': line.price_unit,
                'name': line.product_id.name,
                'product_uom': line.product_id.uom_id.id,
                'consignment_line_id': line.id,
            })

    def action_confirm(self):
        """Update consignment quantities when order is confirmed"""
        res = super().action_confirm()
        for order in self.filtered('consignment_id'):
            for line in order.order_line.filtered('consignment_line_id'):
                line.consignment_line_id.amount_sold += line.product_uom_qty
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    consignment_line_id = fields.Many2one(
        'assign.consignment.line',
        string='Consignment Line',
        ondelete='set null'
    )
# from odoo import models, fields, api
# from odoo.exceptions import UserError
# from odoo.tools.translate import _
# from odoo.tools.float_utils import float_compare
#
#
# class SaleOrder(models.Model):
#     _inherit = 'sale.order'
#
#     warehouse_id = fields.Many2one(
#         'stock.warehouse',
#         string='Warehouse',
#         required=True,
#         readonly=True,
#         states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
#         default=lambda self: self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
#     )
#
#     consignment_id = fields.Many2one(
#         'assign.consignment',
#         string='Consignment',
#         domain="[('partner_id', '=', partner_id), ('picking_id.state', '=', 'done'),('state', '=', 'confirm')]",
#         help="Select a consignment with completed transfer"
#     )
#
#     def _get_default_warehouse(self):
#         """Get default warehouse from company-specific consignment settings"""
#         company_id = self.env.company.id
#         warehouse_key = f'assign_consignment.consignment_warehouse_id_{company_id}'
#         warehouse_id = int(self.env['ir.config_parameter'].sudo().get_param(warehouse_key, 0))
#         warehouse = self.env['stock.warehouse'].browse(warehouse_id)
#         if warehouse.exists() and warehouse.company_id.id == company_id:
#             return warehouse
#         return self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
#
#     # def _get_default_warehouse(self):
#     #     """Get default warehouse from consignment settings"""
#     #     warehouse_id = int(self.env['ir.config_parameter'].sudo().get_param(
#     #         'assign_consignment.consignment_warehouse_id', 0
#     #     ))
#     #     if warehouse_id:
#     #         return self.env['stock.warehouse'].browse(warehouse_id)
#     #     return self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
#
#     @api.onchange('partner_id')
#     def _onchange_partner_id(self):
#         """Reset order lines, warehouse and consignment when partner changes"""
#         # Call parent's onchange first to maintain standard behavior
#         res = super(SaleOrder, self)._onchange_partner_id()
#
#         # Reset related fields
#         self.order_line = [(5, 0, 0)]  # Clear all order lines
#         self.warehouse_id = self._get_default_warehouse()  # Reset to default warehouse
#         self.consignment_id = False  # Clear consignment selection
#
#         return res
#
#     @api.onchange('consignment_id')
#     def _onchange_consignment_id(self):
#         """Handle consignment selection changes including reset when cleared"""
#         # Always reset order lines first
#         self.order_line = [(5, 0, 0)]
#
#         if not self.consignment_id:
#             # Case 1: When clearing consignment (selecting non-consignment)
#             # Reset warehouse to company default
#             self.warehouse_id = self.env['stock.warehouse'].search(
#                 [('company_id', '=', self.env.company.id)],
#                 limit=1
#             )
#             return
#
#         # Case 2: When selecting a consignment
#         company_id = self.env.company.id
#         warehouse_key = f'assign_consignment.consignment_warehouse_id_{company_id}'
#         warehouse_id = int(self.env['ir.config_parameter'].sudo().get_param(warehouse_key, 0))
#         warehouse = self.env['stock.warehouse'].browse(warehouse_id)
#         if warehouse.exists() and warehouse.company_id.id == company_id:
#             self.warehouse_id = warehouse
#         else:
#             # fallback
#             self.warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', company_id)], limit=1)
#
#         # warehouse_id = int(self.env['ir.config_parameter'].sudo().get_param(
#         #     'assign_consignment.consignment_warehouse_id', 0
#         # ))
#         # if warehouse_id:
#         #     self.warehouse_id = self.env['stock.warehouse'].browse(warehouse_id)
#         # else:
#         #     # Fallback to company default if no consignment warehouse set
#         #     self.warehouse_id = self.env['stock.warehouse'].search(
#         #         [('company_id', '=', self.env.company.id)],
#         #         limit=1
#         #     )
#
#         # Add consignment products to order lines
#         existing_product_ids = self.order_line.mapped('product_id.id')
#         for consignment_line in self.consignment_id.order_line_ids:
#             if (consignment_line.product_id.id not in existing_product_ids and
#                     consignment_line.remaining_qty > 0):
#                 self.order_line += self.env['sale.order.line'].new({
#                     'order_id': self.id,
#                     'product_id': consignment_line.product_id.id,
#                     'product_uom_qty': consignment_line.remaining_qty,
#                     'price_unit': consignment_line.price_unit,
#                     'name': consignment_line.product_id.name,
#                     'product_uom': consignment_line.product_id.uom_id.id,
#                     'consignment_line_id': consignment_line.id,
#                 })
#
#     def action_confirm(self):
#         res = super().action_confirm()
#         for order in self:
#             if order.consignment_id:
#                 for line in order.order_line:
#                     consignment_lines = order.consignment_id.order_line_ids.filtered(
#                         lambda l: l.product_id == line.product_id and l.remaining_qty > 0
#                     )
#                     qty_to_assign = line.product_uom_qty
#                     for cons_line in consignment_lines:
#                         if qty_to_assign <= 0:
#                             break
#                         available = cons_line.remaining_qty
#                         assign_qty = min(qty_to_assign, available)
#                         cons_line.amount_sold += assign_qty
#                         qty_to_assign -= assign_qty
#         return res
#
#
# class SaleOrderLine(models.Model):
#     _inherit = 'sale.order.line'
#
#     consignment_line_id = fields.Many2one(
#         'assign.consignment.line',
#         string='Consignment Line',
#         ondelete='set null'
#     )
