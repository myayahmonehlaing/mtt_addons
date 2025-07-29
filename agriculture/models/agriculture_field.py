from odoo import models, fields, api, _


class AgricultureField(models.Model):
    _name = "agriculture.field"
    _description = "Agriculture Field"
    _table = "field"

    name = fields.Char(string="Field Name", required=True)
    location = fields.Char(string="Location")
    total_area = fields.Float(string="Total Area (acres)")
    code = fields.Char(string="Short Code")
    warehouse_id = fields.Many2one('stock.warehouse', string="Linked Warehouse", readonly=True)

    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env.company
    )
    farmer_id = fields.Many2one(
        'agriculture.farmer',
        string="Farmer",
        required=True
    )
    user_id = fields.Many2one(
        'res.users', string="Manager",
        default=lambda self: self.env.user,
        store=True, index=True, tracking=True
    )
    image_field = fields.Binary("Image")

    @api.model
    def create(self, vals):
        name = vals.get('name') or _('Unnamed Field')
        code = vals.get('code') or name[:3].upper()

        warehouse = self.env['stock.warehouse'].create({
            'name': name,  # Directly using field name
            'code': code,
            'company_id': vals.get('company_id') or self.env.company.id,
        })

        vals['warehouse_id'] = warehouse.id
        return super().create(vals)

    def write(self, vals):
        for field in self:
            if 'name' in vals and field.warehouse_id:
                field.warehouse_id.name = vals['name']
            if 'code' in vals and field.warehouse_id:
                field.warehouse_id.code = vals['code']
        return super().write(vals)

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = f"{self.name} (Copy)"
        default['image_field'] = self.image_field
        default['code'] = f"{self.code}_COPY"
        return super().copy(default)

# from odoo import models, fields, api, _
#
#
# class AgricultureField(models.Model):
#     _name = "agriculture.field"
#     _description = "Agriculture Field"
#     _table = "field"
#
#     name = fields.Char(string="Field Name", required=True)
#     location = fields.Char(string="Location")
#     total_area = fields.Float(string="Total Area (acres)")
#     company_id = fields.Many2one(
#         'res.company', string="Company",
#         default=lambda self: self.env.company
#     )
#     farmer_id = fields.Many2one(
#         'agriculture.farmer',
#         string="Farmer",
#         required=True
#     )
#     user_id = fields.Many2one(
#         'res.users', string="Manager",
#         default=lambda self: self.env.user,
#         store=True, index=True, tracking=True
#     )
#     image_field = fields.Binary("Image")
#     warehouse_name = fields.Char(string="Warehouse Name")
#     code = fields.Char(string="Short Code")
#     warehouse_id = fields.Many2one('stock.warehouse', string="Linked Warehouse", readonly=True)
#
#     @api.model
#     def create(self, vals):
#         warehouse_name = vals.get('warehouse_name') or f"{vals.get('name')} Warehouse"
#         code = vals.get('code') or (vals.get('name') or '')[:3].upper()
#
#         # Create warehouse
#         warehouse = self.env['stock.warehouse'].create({
#             'name': warehouse_name,
#             'code': code,
#             'company_id': vals.get('company_id') or self.env.company.id,
#         })
#
#         # Link warehouse to field
#         vals['warehouse_id'] = warehouse.id
#         return super().create(vals)
#
#     def write(self, vals):
#         for field in self:
#             if 'warehouse_name' in vals and field.warehouse_id:
#                 field.warehouse_id.name = vals['warehouse_name']
#
#             if 'code' in vals and field.warehouse_id:
#                 field.warehouse_id.code = vals['code']
#
#         return super().write(vals)
#
#     def copy(self, default=None):
#         default = dict(default or {})
#         default['name'] = f"{self.name} (Copy)"
#         default['image_field'] = self.image_field
#         default['warehouse_name'] = f"{self.warehouse_name} (Copy)"
#         default['code'] = f"{self.code}_COPY"
#         return super().copy(default)
