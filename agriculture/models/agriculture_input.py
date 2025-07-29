from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AgricultureFarmInput(models.Model):
    _name = "agriculture.input"
    _description = "Agriculture Farm Input"
    _table = "input"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string="Input Reference",
        required=True,
        readonly=True,
        default=lambda self: _('New')
    )

    planting_id = fields.Many2one(
        'agriculture.planting',
        domain=[('status', '=', 'progress')],
        required=True
    )

    date = fields.Date(
        string="Date",
        default=lambda self: date.today(),
        required=True
    )

    stage_id = fields.Many2one(
        'agriculture.stage',
        string="Stage"
    )

    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ], string="Status", default='draft')

    line_ids = fields.One2many(
        'agriculture.input.line',
        'input_id',
        string="Input Usage"
    )

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company
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
        string="Product",
        related='planting_id.finish_product_id',
        store=True,
        readonly=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True,
        readonly=True
    )

    total = fields.Monetary(
        string="Total Cost",
        compute="_compute_price_total",
        store=True,
        currency_field='currency_id'
    )
    # product_list = fields.Char(
    #     string="Input Line Product",
    #     compute="_compute_line_data",
    #     store=True
    # )
    #
    # total_quantity = fields.Float(
    #     string="Total Quantity",
    #     compute="_compute_line_data",
    #     store=True
    # )
    #
    # total_value = fields.Monetary(
    #     string="Total Value",
    #     currency_field='currency_id',
    #     compute="_compute_line_data",
    #     store=True
    # )

    planting_count = fields.Integer(string="Planting Count", compute="_compute_planting_count")
    bill_count = fields.Integer(string="Bill Count", compute="_compute_bill_count")
    production_count = fields.Integer(string="Production", compute="_compute_production_count")

    quantity = fields.Float(related='line_ids.quantity', string="Quantity", store=True)
    is_checked = fields.Boolean(string="Is Checked", default=False)

    @api.model
    def create(self, vals):

        if vals.get('planting_id'):
            planting = self.env['agriculture.planting'].browse(vals['planting_id'])

            if not vals.get('field_id') and planting.field_id:
                vals['field_id'] = planting.field_id.id

            if not vals.get('farmer_id') and planting.farmer_id:
                vals['farmer_id'] = planting.farmer_id.id

            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('agriculture.input') or _('New')
        return super().create(vals)

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = self.env['ir.sequence'].next_by_code('agriculture.input') or _('New')
        default['status'] = 'draft'
        return super().copy(default)

    def _compute_planting_count(self):
        for record in self:
            record.planting_count = self.env['agriculture.planting'].search_count([
                ('id', '=', record.planting_id.id)
            ]) if record.planting_id else 0

    def _compute_bill_count(self):
        for record in self:
            record.bill_count = self.env['account.move'].search_count([
                ('invoice_origin', '=', record.name),
                ('move_type', '=', 'in_invoice')
            ])

    def _compute_production_count(self):
        for rec in self:
            rec.production_count = self.env['mrp.production'].search_count([('planting_id', '=', rec.planting_id.id)])

    def action_confirm(self):
        for rec in self:
            rec.status = 'confirmed'

            if rec.planting_id:
                if rec.stage_id:
                    rec.planting_id.stage_id = rec.stage_id

                mo = self.env['mrp.production'].search([('planting_id', '=', rec.planting_id.id)], limit=1)
                if not mo:
                    raise UserError(_("No manufacturing order found for this planting."))

                # Determine sequence starting after current max
                sequence = max(mo.move_raw_ids.mapped('sequence') or [0]) + 1

                new_lines = []
                for line in rec.line_ids:
                    new_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'product_uom': line.product_uom_id.id,
                        'product_uom_qty': line.quantity,
                        'name': line.product_id.name,
                        'sequence': sequence,
                    }))
                    sequence += 1

                if new_lines:
                    mo.write({
                        'move_raw_ids': new_lines,
                    })

    def action_done(self):
        for rec in self:
            rec.status = 'done'

    def action_create_bill(self):
        for rec in self:
            rec.is_checked = True
            if not rec.farmer_id:
                raise UserError(_("Please set a farmer before creating a bill."))

            invoice_lines = []
            for line in rec.line_ids:
                if line.product_id.type == 'service':
                    invoice_lines.append((0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.name or line.product_id.name,
                        'quantity': line.quantity,
                        'product_uom_id': line.product_uom_id.id,
                        'price_unit': line.price_unit,
                        'currency_id': rec.currency_id.id,
                    }))

            bill = self.env['account.move'].create({
                'partner_id': rec.farmer_id.partner_id.id,
                'invoice_date': date.today(),
                'move_type': 'in_invoice',
                'invoice_origin': rec.name,
                'currency_id': rec.currency_id.id,
                'ref': rec.name,
                'billing_user_id': self.env.user.id,
                'invoice_line_ids': invoice_lines,
            })

            return {
                'type': 'ir.actions.act_window',
                'name': f"Vendor Bill for {rec.name}",
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': bill.id,
                'target': 'current',
            }

    def action_view_bill(self):
        self.ensure_one()
        bill = self.env['account.move'].search([
            ('invoice_origin', '=', self.name),
            ('move_type', '=', 'in_invoice')
        ], limit=1)

        if not bill:
            raise UserError(_("No vendor bill found for this planting."))

        return {
            'type': 'ir.actions.act_window',
            'name': f'Bill - {self.name}',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': bill.id,
            'target': 'current',
            'context': {'create': False}
        }

    def action_view_planting(self):
        self.ensure_one()
        if not self.planting_id:
            raise UserError(_("No internal transfer associated with this consignment."))

        return {
            'type': 'ir.actions.act_window',
            'name': f'Planting- {self.name}',
            'res_model': 'agriculture.planting',
            'view_mode': 'form',
            'res_id': self.planting_id.id,
            'target': 'current',
            'context': {'create': False}
        }

    def action_view_production(self):
        self.ensure_one()
        production = self.env['mrp.production'].search([
            ('planting_id', '=', self.planting_id.id)
        ], limit=1)

        if not production:
            raise UserError(_("No production order linked to this planting."))

        return {
            'type': 'ir.actions.act_window',
            'name': f'Production - {self.planting_id.name}',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': production.id,
            'target': 'current',
            'context': {'create': False}
        }

    @api.onchange('planting_id')
    def _onchange_planting_id_auto_fill_field_and_farmer(self):
        if self.planting_id:
            self.field_id = self.planting_id.field_id
            self.farmer_id = self.planting_id.farmer_id
            self.product_id = self.planting_id.finish_product_id

    @api.depends('line_ids.price_subtotal')
    def _compute_price_total(self):
        for rec in self:
            rec.total = sum(rec.line_ids.mapped('price_subtotal'))

    def unlink(self):
        restricted = self.filtered(lambda rec: rec.status in ['confirmed', 'done'])
        if restricted:
            raise UserError(_("You cannot delete Inputs that are Confirmed or Done."))
        return super().unlink()


class AgricultureFarmInput(models.Model):
    _name = "agriculture.input.line"
    _description = "Agriculture Farm Input Line"
    _table = "input_line"

    name = fields.Char(
        string="Description",
        help="Describe this input item or usage step."
    )

    product_id = fields.Many2one(
        'product.product',
        string=" Input Product",
        required=True,
        help="Select the input item (e.g., fertilizer, pesticide, tool, seed)."
    )

    quantity = fields.Float(
        string="Quantity",
        required=True,
        default=1.0
    )

    product_uom_id = fields.Many2one(
        'uom.uom',
        string="Unit of Measure",
        domain="[('category_id', '=', uom_category_id)]",
        required=True
    )

    uom_category_id = fields.Many2one(
        'uom.category',
        string="UoM Category",
        compute='_compute_uom_category',
        store=True
    )

    input_id = fields.Many2one(
        'agriculture.input',
        string="Input Record",
        required=True,
        ondelete='cascade'
    )

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        default=lambda self: self.env.company
    )

    price_unit = fields.Float(
        string="Unit Price",
        help="Automatically pulled from the product's cost"
    )

    price_subtotal = fields.Monetary(
        string="Subtotal",
        compute="_compute_price_subtotal",
        currency_field='currency_id',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        store=True,
        readonly=True
    )
    planting_id = fields.Many2one(
        'agriculture.planting',
        string="Planting",
        compute="_compute_planting_id",
        store=True,
        index=True
    )
    stage_id = fields.Many2one(
        'agriculture.stage',
        string="Stage",
        related='input_id.stage_id',
        store=True
    )
    field_id = fields.Many2one(
        'agriculture.field',
        string="Field",
        related='input_id.field_id',
        store=True
    )

    @api.depends('input_id.planting_id')
    def _compute_planting_id(self):
        for line in self:
            line.planting_id = line.input_id.planting_id

    @api.depends('product_id')
    def _compute_uom_category(self):
        for line in self:
            line.uom_category_id = line.product_id.uom_id.category_id if line.product_id else False

    @api.onchange('product_id')
    def _onchange_product_set_price_unit(self):
        for line in self:
            if line.product_id:
                line.price_unit = line.product_id.standard_price
                line.product_uom_id = line.product_id.uom_id
                line.uom_category_id = line.product_id.uom_id.category_id

    @api.depends('quantity', 'price_unit')
    def _compute_price_subtotal(self):
        for rec in self:
            rec.price_subtotal = rec.quantity * rec.price_unit

    @api.model
    def create(self, vals):
        if vals.get('product_id') and not vals.get('product_uom_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            if product.uom_id:
                vals['product_uom_id'] = product.uom_id.id
        qty = vals.get('quantity', 1.0)
        price = vals.get('price_unit')
        vals['price_subtotal'] = qty * price
        return super().create(vals)
