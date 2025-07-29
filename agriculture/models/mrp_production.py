# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, Command, SUPERUSER_ID
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'

    planting_id = fields.Many2one('agriculture.planting', string='Planting Reference')
    field_id = fields.Many2one('agriculture.field', string='Field Reference')



    def _set_qty_producing(self, pick_manual_consumption_moves=True):
        if self.product_id.tracking == 'serial':
            qty_producing_uom = self.product_uom_id._compute_quantity(self.qty_producing, self.product_id.uom_id,
                                                                      rounding_method='HALF-UP')
            # allow changing a non-zero value to a 0 to not block mass produce feature
            if qty_producing_uom != 1 and not (
                    qty_producing_uom == 0 and self._origin.qty_producing != self.qty_producing):
                self.qty_producing = self.product_id.uom_id._compute_quantity(1, self.product_uom_id,
                                                                              rounding_method='HALF-UP')

        # waiting for a preproduction move before assignement
        is_waiting = self.warehouse_id.manufacture_steps != 'mrp_one_step' and self.picking_ids.filtered \
            (lambda p: p.picking_type_id == self.warehouse_id.pbm_type_id and p.state not in ('done', 'cancel'))

        for move in (self.move_raw_ids.filtered
                         (lambda m: not is_waiting or m.product_id.tracking == 'none') | self.move_finished_ids.filtered
                         (lambda m: m.product_id != self.product_id)):
            # picked + manual means the user set the quantity manually
            if move.manual_consumption and move.picked:
                continue

            # sudo needed for portal users
            if move.sudo()._should_bypass_set_qty_producing():
                continue

            new_qty = float_round((self.product_qty - self.qty_produced) * move.unit_factor,
                                  precision_rounding=move.product_uom.rounding)
            move._set_quantity_done(new_qty)
            if not move.manual_consumption or pick_manual_consumption_moves:
                move.picked = True

    def button_mark_done(self):
        res = super(MrpProduction, self).button_mark_done()

        for production in self:
            planting = production.planting_id
            if planting:
                # Transfer product quantity to planting
                planting.production_quantity = production.qty_producing
                planting.production_product_uom_id=production.product_uom_id
                planting.action_done()

        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.depends('raw_material_production_id.qty_producing', 'product_uom_qty', 'product_uom')
    def _compute_should_consume_qty(self):
        for move in self:
            mo = move.raw_material_production_id
            if not mo or not move.product_uom:
                move.should_consume_qty = 0
                continue

            move.should_consume_qty = float_round((mo.product_qty - mo.qty_produced) * move.unit_factor,
                                                  precision_rounding=move.product_uom.rounding)

# from odoo import models, fields, api, _
#
#
# class MrpProduction(models.Model):
#     _inherit = 'mrp.production'
#
#     planting_id = fields.Many2one(
#         'agriculture.planting',
#         string="Related Planting"
#     )
#
#     input_id = fields.Many2one(
#         'agriculture.input',
#         string="Farm Inputs"
#     )
#
#     def _update_raw_moves(self, factor):
#         return []
#
#     def _set_qty_producing(self, pick_manual_consumption_moves=True):
#         for move in self.move_raw_ids:
#             continue
#
#
#
#     def action_confirm(self):
#         res = super().action_confirm()
#         for production in self:
#             for move in production.move_raw_ids:
#                 for move_line in move.move_line_ids:
#                     move_line.qty_done = move_line.quantity
#                     move_line.picked = True
#         return res
#
#
