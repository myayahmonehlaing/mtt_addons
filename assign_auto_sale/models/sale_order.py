from odoo import models, api, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        # Get system parameters
        auto_shipping = self.env['ir.config_parameter'].sudo().get_param('sale.auto_shipping')
        auto_invoice = self.env['ir.config_parameter'].sudo().get_param('sale.auto_create_invoice')

        for order in self:
            # Process auto shipping if enabled
            if auto_shipping and order.picking_ids:
                for picking in order.picking_ids:
                    if picking.state != 'done':
                        try:
                            # Confirm the transfer
                            picking.action_confirm()

                            # Check availability (this is the critical part)
                            picking.action_assign()

                            if all(move.state == 'assigned' for move in picking.move_ids):
                                for move in picking.move_ids:
                                    for move_line in move.move_line_ids:
                                        move_line.qty_done = move.product_uom_qty  # set qty from move, not move_line
                                picking.button_validate()
                            else:
                                unavailable_products = picking.move_ids.filtered(
                                    lambda m: m.state != 'assigned').mapped('product_id.display_name')
                                order.message_post(body=_(
                                    "Auto Shipping: Could not process delivery %s automatically because the following products are not available in stock: %s."
                                ) % (picking.name, ', '.join(unavailable_products)))

                        except Exception as e:
                            raise UserError(_('Failed to process shipping automatically: %s') % str(e))
            # # Process auto shipping if enabled
            # if auto_shipping and order.picking_ids:
            #     for picking in order.picking_ids:
            #         if picking.state != 'done':
            #             try:
            #                 picking.action_confirm()  # Confirm the transfer if not already confirmed
            #                 picking.action_assign()  # Check availability
            #
            #                 # Mark all moves as done - updated field name
            #                 for move_line in picking.move_ids_without_package:
            #                     move_line.quantity = move_line.product_uom_qty
            #
            #                 # Alternative approach using move_line_ids if above doesn't work
            #                 # for move_line in picking.move_line_ids:
            #                 #     move_line.qty_done = move_line.product_uom_qty
            #
            #                 picking.button_validate()  # Validate the picking
            #             except Exception as e:
            #                 raise UserError(_('Failed to process shipping automatically: %s') % str(e))

            # Process auto invoice if enabled
            if auto_invoice and order.invoice_status == 'to invoice':
                try:
                    # Create invoice
                    invoice = order._create_invoices()

                    # Post the invoice
                    if invoice.state == 'draft':
                        invoice.action_post()
                except Exception as e:
                    raise UserError(_('Failed to create invoice automatically: %s') % str(e))

        return res
