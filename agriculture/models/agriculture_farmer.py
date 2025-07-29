from odoo import models, fields, api


class AgricultureFarmer(models.Model):
    _name = "agriculture.farmer"
    _description = "Agriculture Farmer"
    _table = "farmer"

    name = fields.Char(string="Farmer Name", required=True)
    address = fields.Text(string="Address")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    partner_id = fields.Many2one('res.partner', string="Related Partner", readonly=True)
    company_id = fields.Many2one(
        'res.company', string="Company",
        default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        'res.users', string="Responsible User",
        default=lambda self: self.env.user,
        store=True, index=True, tracking=True
    )
    image_field = fields.Binary("Image")

    def copy(self, default=None):
        default = dict(default or {})
        default['name'] = f"{self.name} (Copy)"
        default['image_field'] = self.image_field
        return super().copy(default)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            partner_vals = {
                'name': vals.get('name'),
                'street': vals.get('address', ''),
                'phone': vals.get('phone', ''),
                'email': vals.get('email', ''),
                'company_id': vals.get('company_id'),
                'image_1920': vals.get('image_field'),  # Sync image
            }
            new_partner = self.env['res.partner'].create(partner_vals)
            vals['partner_id'] = new_partner.id
        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            partner_vals = {}
            if 'name' in vals:
                partner_vals['name'] = vals['name']
            if 'address' in vals:
                partner_vals['street'] = vals['address']
            if 'phone' in vals:
                partner_vals['phone'] = vals['phone']
            if 'email' in vals:
                partner_vals['email'] = vals['email']
            if 'company_id' in vals:
                partner_vals['company_id'] = vals['company_id']
            if 'image_field' in vals:
                partner_vals['image_1920'] = vals['image_field']  # Sync image update

            if partner_vals and rec.partner_id:
                rec.partner_id.write(partner_vals)

        return super().write(vals)
