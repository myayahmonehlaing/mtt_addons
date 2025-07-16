from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class AssignConsignment(models.Model):
    _name = "assign.consignment"
    _description = "Consignment"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, readonly=True, default=lambda self: 'New')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
    team_id = fields.Many2one('crm.team', string='Sales Team')

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
        states={'draft': [('readonly', False)]},
        tracking=True
    )

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Operation Type',
        domain="[('code', '=', 'internal'),('company_id', '=', company_id)]",
        required=True,
        help="Determines the source location for the transfer"
    )

    allowed_location_ids = fields.Many2many(
        'stock.location',
        compute='_compute_allowed_locations',
        string='Allowed Locations'
    )

    order_line_ids = fields.One2many('assign.consignment.line', 'consignment_id', string='Order Lines')
    amount_total = fields.Float(string='Total', compute='_compute_amount_total', store=True)

    picking_id = fields.Many2one('stock.picking', string='Internal Transfer', readonly=True, copy=False)
    transfer_count = fields.Integer(string='Internal Transfers', compute='_compute_transfer_count')
    sale_order_count = fields.Integer(string='Sales Orders', compute='_compute_sale_order_count')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done')
    ], string="Status", default="draft", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('assign.consignment') or 'New'
        return super().create(vals_list)

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = self.env['ir.sequence'].next_by_code('assign.consignment') or _('New')
        return super().copy(default)

    @api.depends('company_id')
    def _compute_allowed_locations(self):
        for record in self:
            record.allowed_location_ids = self.env['stock.location'].search([
                ('company_id', '=', record.company_id.id),
                ('usage', '=', 'internal')
            ])

    @api.depends('order_line_ids.price_total')
    def _compute_amount_total(self):
        for record in self:
            record.amount_total = sum(line.price_total for line in record.order_line_ids)

    def _compute_transfer_count(self):
        for record in self:
            record.transfer_count = len(record.picking_id)

    def _compute_sale_order_count(self):
        for consignment in self:
            consignment.sale_order_count = self.env['sale.order'].search_count([
                ('consignment_id', '=', consignment.id)
            ])

    def action_close(self):
        for record in self:
            if record.state != 'confirm':
                raise UserError(_("Only confirmed consignments can be closed."))
            record.state = 'done'

    def action_confirm(self):
        for record in self:
            if not record.picking_type_id:
                raise UserError(_("Please select an Operation Type before confirming."))


            consignment_location = record.company_id.consignment_warehouse_id.lot_stock_id
            if not consignment_location:
                raise UserError(_("Consignment location not configured for this company!"))


            transfer_vals = {
                'picking_type_id': record.picking_type_id.id,
                'location_id': record.picking_type_id.default_location_src_id.id,
                'location_dest_id': consignment_location.id,
                'origin': record.name,
                'company_id': record.company_id.id,
                'partner_id': record.partner_id.id,
            }

            internal_transfer = self.env['stock.picking'].create(transfer_vals)

            # Create stock moves
            for line in record.order_line_ids:
                self.env['stock.move'].create({
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': internal_transfer.id,
                    'location_id': record.picking_type_id.default_location_src_id.id,
                    'location_dest_id': consignment_location.id,
                    'company_id': record.company_id.id,
                })

            record.write({
                'state': 'confirm',
                'picking_id': internal_transfer.id
            })
            internal_transfer.action_confirm()

    def action_view_picking(self):
        self.ensure_one()
        if not self.picking_id:
            raise UserError(_("No internal transfer associated with this consignment."))

        return {
            'type': 'ir.actions.act_window',
            'name': f'Internal Transfer - {self.name}',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
            'target': 'current',
            'context': {'create': False}
        }

    def action_view_sales_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Sales Orders - {self.name}',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [('consignment_id', '=', self.id)],
            'context': {'create': False},
            'target': 'current',
        }


class AssignConsignmentLine(models.Model):
    _name = 'assign.consignment.line'
    _description = 'Consignment Order Line'

    consignment_id = fields.Many2one('assign.consignment', string='Consignment')
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain=[('is_storable', '=', True)],
        required=True,
    )
    quantity = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    price_total = fields.Float(string='Amount', compute='_compute_price_total', store=True)
    amount_sold = fields.Float(string='Amount Sold', default=0.0, readonly=True)
    remaining_qty = fields.Float(string='Remaining Quantity', compute='_compute_remaining_qty', store=True)

    @api.depends('quantity', 'price_unit')
    def _compute_price_total(self):
        for line in self:
            line.price_total = line.quantity * line.price_unit

    @api.depends('quantity', 'amount_sold')
    def _compute_remaining_qty(self):
        for line in self:
            line.remaining_qty = max(line.quantity - line.amount_sold, 0)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.price_unit = self.product_id.lst_price
# from odoo import models, fields, api
# from odoo.exceptions import UserError
# from odoo.tools.translate import _
#
#
# class AssignConsignment(models.Model):
#     _name = "assign.consignment"
#     _description = "Consignment"
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#
#     picking_type_id = fields.Many2one(
#         'stock.picking.type',
#         string='Operation Type',
#         domain="[('code', '=', 'internal'),('company_id', '=', company_id)]",
#         required=True,
#         help="Determines the source location for the transfer"
#     )
#
#     company_id = fields.Many2one(
#         'res.company',
#         string='Company',
#         required=True,
#         default=lambda self: self.env.company,
#         readonly=True,
#         states={'draft': [('readonly', False)]},
#         tracking=True
#     )
#
#     # Ensure consignment locations are filtered by company
#     @api.depends('company_id')
#     def _compute_allowed_locations(self):
#         for record in self:
#             # This would filter locations based on company
#             record.allowed_location_ids = self.env['stock.location'].search([
#                 ('company_id', '=', record.company_id.id),
#                 ('usage', '=', 'internal')
#             ])
#
#     allowed_location_ids = fields.Many2many(
#         'stock.location',
#         compute='_compute_allowed_locations',
#         string='Allowed Locations'
#     )
#
#     name = fields.Char(string='Reference', required=True, readonly=True, default=lambda self: 'New')
#
#     def copy(self, default=None):
#         default = dict(default or {})
#         default['name'] = self.env['ir.sequence'].next_by_code('assign.consignment') or _('New')
#         return super().copy(default)
#
#     date = fields.Datetime(string='Date', default=fields.Datetime.now)
#     partner_id = fields.Many2one('res.partner', string='Customer', required=True)
#
#     user_id = fields.Many2one('res.users', string='Salesperson', default=lambda self: self.env.user)
#     team_id = fields.Many2one('crm.team', string='Sales Team')
#     # company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
#
#     order_line_ids = fields.One2many('assign.consignment.line', 'consignment_id', string='Order Lines')
#
#     amount_total = fields.Float(string='Total', compute='_compute_amount_total', store=True)
#
#     # Internal Transfer tracking (renamed for clarity, but still stores stock.picking)
#     picking_id = fields.Many2one('stock.picking', string='Internal Transfer', readonly=True, copy=False)
#     transfer_count = fields.Integer(string='Internal Transfers', compute='_compute_transfer_count')
#
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('confirm', 'Confirmed'),
#         ('done', 'Done')
#     ], string="Status", default="draft", tracking=True)
#
#     @api.depends('order_line_ids.price_total')
#     def _compute_amount_total(self):
#         for record in self:
#             record.amount_total = sum(line.price_total for line in record.order_line_ids)
#
#     def _compute_transfer_count(self):
#         for record in self:
#             record.transfer_count = len(record.picking_id)
#
#     @api.model_create_multi
#     def create(self, vals_list):
#         for vals in vals_list:
#             if vals.get('name', 'New') == 'New':
#                 vals['name'] = self.env['ir.sequence'].next_by_code('assign.consignment') or 'New'
#         return super().create(vals_list)
#
#
#
#     # added
#     def action_close(self):
#         for record in self:
#             if record.state != 'confirm':
#                 raise UserError(_("Only confirmed consignments can be closed."))
#             record.state = 'done'
#
#     def action_confirm(self):
#         for record in self:
#             # Use company-specific warehouse key
#             warehouse_key = f'assign_consignment.consignment_warehouse_id_{record.company_id.id}'
#             warehouse_id = int(self.env['ir.config_parameter'].sudo().get_param(warehouse_key, 0))
#
#             if not warehouse_id:
#                 raise UserError(_("Consignment warehouse not configured in Settings for this company!"))
#
#             warehouse = self.env['stock.warehouse'].browse(warehouse_id)
#
#             # Cross-check company
#             if warehouse.company_id != record.company_id:
#                 raise UserError(_(
#                     "Configured warehouse belongs to %s, but this consignment is for %s!"
#                 ) % (warehouse.company_id.name, record.company_id.name))
#
#             consignment_location = warehouse.lot_stock_id
#
#             if not record.picking_type_id:
#                 raise UserError(_("Please select an Operation Type before confirming."))
#
#             # Create the internal transfer
#             transfer_vals = {
#                 'picking_type_id': record.picking_type_id.id,
#                 'location_id': record.picking_type_id.default_location_src_id.id,
#                 'location_dest_id': consignment_location.id,
#                 'origin': record.name,
#                 'company_id': record.company_id.id,
#                 'partner_id': record.partner_id.id,
#             }
#
#             internal_transfer = self.env['stock.picking'].create(transfer_vals)
#
#             # Create stock moves
#             for line in record.order_line_ids:
#                 self.env['stock.move'].create({
#                     'name': line.product_id.name,
#                     'product_id': line.product_id.id,
#                     'product_uom_qty': line.quantity,
#                     'product_uom': line.product_id.uom_id.id,
#                     'picking_id': internal_transfer.id,
#                     'location_id': record.picking_type_id.default_location_src_id.id,
#                     'location_dest_id': consignment_location.id,
#                     'company_id': record.company_id.id,
#                 })
#
#             record.write({
#                 'state': 'confirm',
#                 'picking_id': internal_transfer.id
#             })
#
#             internal_transfer.action_confirm()
#
#     def action_view_picking(self):
#         self.ensure_one()
#         if not self.picking_id:
#             raise UserError(_("No internal transfer associated with this consignment."))
#
#         return {
#             'type': 'ir.actions.act_window',
#             'name': f'Internal Transfer - {self.name}',
#             'res_model': 'stock.picking',
#             'view_mode': 'form',
#             'res_id': self.picking_id.id,
#             'target': 'current',
#             'context': {'create': False}
#         }
#
#     # added
#     sale_order_count = fields.Integer(
#         string='Sales Orders',
#         compute='_compute_sale_order_count'
#     )
#
#     def _compute_sale_order_count(self):
#         for consignment in self:
#             consignment.sale_order_count = self.env['sale.order'].search_count([
#                 ('consignment_id', '=', consignment.id)
#             ])
#
#     def action_view_sales_orders(self):
#         self.ensure_one()
#         return {
#             'type': 'ir.actions.act_window',
#             'name': f'Sales Orders - {self.name}',
#             'res_model': 'sale.order',
#             'view_mode': 'list,form',
#             'views': [  # Using (False, 'view_type') for robust view lookup
#                 (False, 'list'),
#                 (False, 'form')
#             ],
#             'domain': [('consignment_id', '=', self.id),
#                        ],
#             'context': {
#                 'create': False,
#                 'default_consignment_id': self.id
#             },
#             'target': 'current',
#         }
#
#
# class AssignConsignmentLine(models.Model):
#     _name = 'assign.consignment.line'
#     _description = 'Consignment Order Line'
#
#     consignment_id = fields.Many2one('assign.consignment', string='Consignment')
#     product_id = fields.Many2one(
#         'product.product',
#         string='Product',
#         domain=[('is_storable', '=', True)],
#         required=True,
#     )
#     quantity = fields.Float(string='Quantity', default=1.0)
#     price_unit = fields.Float(string='Unit Price', digits='Product Price')
#     price_total = fields.Float(string='Amount', compute='_compute_price_total', store=True)
#
#     @api.depends('quantity', 'price_unit')
#     def _compute_price_total(self):
#         for line in self:
#             line.price_total = line.quantity * line.price_unit
#
#     @api.onchange('product_id')
#     def _onchange_product_id(self):
#         if self.product_id:
#             self.price_unit = self.product_id.lst_price
#
#     amount_sold = fields.Float(string='Amount Sold', default=0.0, readonly=True)
#     remaining_qty = fields.Float(string='Remaining Quantity', compute='_compute_remaining_qty', store=True)
#
#     # @api.depends('quantity', 'amount_sold')
#     # def _compute_remaining_qty(self):
#     #     for line in self:
#     #         line.remaining_qty = line.quantity - line.amount_sold
#
#     @api.depends('quantity', 'amount_sold')
#     def _compute_remaining_qty(self):
#         for line in self:
#             line.remaining_qty = max(line.quantity - line.amount_sold, 0)
#
#     @api.depends('quantity', 'price_unit')
#     def _compute_price_total(self):
#         for line in self:
#             line.price_total = line.quantity * line.price_unit
