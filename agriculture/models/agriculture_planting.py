from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AgriculturePlanting(models.Model):
    _name = "agriculture.planting"
    _description = "Agriculture Farmer"
    _table = "planting"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        default=lambda self: _('New')
    )

    farmer_id = fields.Many2one(
        'agriculture.farmer',
        string="Farmer",
        required=True
    )

    field_id = fields.Many2one(
        'agriculture.field',
        string="Field",
        required=True
    )

    product_id = fields.Many2one(
        'product.product',
        string="Seed",
        domain="[('is_seed', '=', True)]",
        required=True
    )

    finish_product_id = fields.Many2one(
        'product.product',
        string="Finish Product",
        domain="[('is_crop', '=', True)]",
        required=True
    )

    product_uom_id = fields.Many2one(
        'uom.uom',
        required=True,
        domain="[('category_id', '=', product_uom_category_id)]"
    )

    finish_product_uom_id = fields.Many2one(
        'uom.uom',
        required=True,
        domain="[('category_id', '=', finish_product_uom_category_id)]"
    )
    production_product_uom_id = fields.Many2one(
        'uom.uom',

    )

    quantity = fields.Float(
        string="Seed Quantity",
        required=True
    )

    finish_quantity = fields.Float(
        string="Estimated Quantity",
        required=True
    )
    production_quantity = fields.Float(
        string="Production Quantity",
    )

    product_uom_category_id = fields.Many2one(
        'uom.category',
        string="Input UoM Category",
        compute='_compute_uom_categories',
        store=True
    )

    finish_product_uom_category_id = fields.Many2one(
        'uom.category',
        string="Output UoM Category",
        compute='_compute_uom_categories',
        store=True
    )

    start_date = fields.Date(
        string="Planting Date",
        default=lambda self: date.today(),
        required=True
    )

    end_date = fields.Date(
        string="Estimated Harvest Date",
        default=lambda self: date.today(),
        copy=True
    )

    status = fields.Selection([
        ('draft', 'Draft'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
    ], string="Status", default='draft')

    stage_id = fields.Many2one(
        'agriculture.stage',
        string="Stage",
        copy=False
    )

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company
    )
    input_id = fields.One2many(
        'agriculture.input',
        'planting_id',
        string="Farm Inputs"
    )
    line_ids = fields.One2many(
        'agriculture.input.line',
        'planting_id',
        string="Input Lines"
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True,
        readonly=True
    )
    total = fields.Monetary(string='Total Input Cost', currency_field='currency_id', compute='_compute_total',
                            store=True)

    @api.depends('line_ids.price_subtotal')
    def _compute_total(self):
        for record in self:
            record.total = sum(line.price_subtotal for line in record.line_ids)

    input_count = fields.Integer(string='Farm Input', compute='_compute_input_count')

    def _compute_input_count(self):
        for record in self:
            record.input_count = self.env['agriculture.input'].search_count([
                ('planting_id', '=', record.id)
            ])

    production_count = fields.Integer(string="Production", compute="_compute_production_count")

    def _compute_production_count(self):
        for rec in self:
            rec.production_count = self.env['mrp.production'].search_count([('planting_id', '=', rec.id)])

    @api.model
    def create(self, vals):
        if not vals.get('farmer_id') and vals.get('field_id'):
            field = self.env['agriculture.field'].browse(vals['field_id'])
            if field and field.farmer_id:
                vals['farmer_id'] = field.farmer_id.id
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('agriculture.planting') or _('New')
        return super().create(vals)

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = self.env['ir.sequence'].next_by_code('agriculture.planting') or _('New')
        default['status'] = 'draft'
        return super().copy(default)

    def action_confirm(self):
        for rec in self:
            rec.status = 'progress'

            components = [(0, 0, {
                'product_id': rec.product_id.id,
                'product_uom': rec.product_uom_id.id,
                'product_uom_qty': rec.quantity,
                'name': rec.product_id.name,

            })]

            # Create manufacturing order based on planting record
            production = self.env['mrp.production'].create({
                'product_id': rec.finish_product_id.id,
                'product_uom_id': rec.finish_product_uom_id.id,
                'origin': rec.name,
                'company_id': rec.company_id.id,
                'date_start': rec.start_date,
                'planting_id': rec.id,
                'field_id': rec.field_id.id,
                'date_finished': rec.end_date,
                'move_raw_ids': components,
                'bom_id': False,
                'picking_type_id': rec.field_id.warehouse_id.manu_type_id.id,
                'location_src_id': rec.field_id.warehouse_id.lot_stock_id.id,
                'location_dest_id': rec.field_id.warehouse_id.lot_stock_id.id,

            })

            production.action_confirm()

    def action_done(self):
        for rec in self:
            rec.status = 'done'

    def action_view_input(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Farm Input - {self.name}',
            'res_model': 'agriculture.input',
            'view_mode': 'list,form',
            'domain': [('planting_id', '=', self.id)],
            'context': {'default_planting_id': self.id},
            'target': 'current',
        }

    def action_view_production(self):
        self.ensure_one()
        production = self.env['mrp.production'].search([('planting_id', '=', self.id)], limit=1)
        if not production:
            raise UserError(_("No production order linked to this planting."))

        return {
            'type': 'ir.actions.act_window',
            'name': f'Production - {self.name}',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': production.id,
            'target': 'current',
            'context': {'create': False}
        }

    @api.onchange('field_id')
    def _onchange_field_id_set_farmer(self):
        if self.field_id and self.field_id.farmer_id:
            self.farmer_id = self.field_id.farmer_id

    @api.depends('product_id', 'finish_product_id')
    def _compute_uom_categories(self):
        for rec in self:
            rec.product_uom_category_id = rec.product_id.uom_id.category_id if rec.product_id else False
            rec.finish_product_uom_category_id = rec.finish_product_id.uom_id.category_id if rec.finish_product_id else False

    @api.onchange('product_id')
    def _onchange_product_id_set_uom(self):
        for rec in self:
            if rec.product_id:
                rec.product_uom_id = rec.product_id.uom_id
                rec.product_uom_category_id = rec.product_id.uom_id.category_id

    @api.onchange('finish_product_id')
    def _onchange_finish_product_id_set_uom(self):
        for rec in self:
            if rec.finish_product_id:
                rec.finish_product_uom_id = rec.finish_product_id.uom_id
                rec.finish_product_uom_category_id = rec.finish_product_id.uom_id.category_id

    def unlink(self):
        restricted = self.filtered(lambda rec: rec.status in ['confirmed', 'done'])
        if restricted:
            raise UserError(_("You cannot delete records that are in Confirmed or Done status."))
        return super().unlink()
