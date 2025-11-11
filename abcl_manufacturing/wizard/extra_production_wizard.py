# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round, float_is_zero, OrderedSet

class ExtraProductionWizard(models.TransientModel):
    _name = 'extra.production.wizard'
    _description = 'Extra Production Wizard'

    production_id = fields.Many2one('mrp.production', string="Manufacturing Order", required=True)
    product_id = fields.Many2one('product.product', string="Product", required=True)
    lot_id = fields.Many2one('stock.lot', string="Lot/Serial Number", required=True)
    extra_production = fields.Float(string="Extra Production Quantity", required=True)
    location_id = fields.Many2one('stock.location', string="Location", readonly=True)

    def action_apply_extra_production(self):
        """Update on-hand quantity and MO extra production field"""
        self.ensure_one()

        if self.extra_production <= 0:
            raise UserError("Please enter a valid extra production quantity greater than zero.")
        if not self.product_id or not self.location_id:
            raise UserError("Missing product or location information.")
        if not self.lot_id:
            raise UserError("No lot/serial number found to update stock.")
        if not self.production_id:
            raise UserError("Manufacturing order not found.")

        production = self.production_id
        bom = production.bom_id

        # ---------------- NEW VALIDATION CHECK ----------------
        if bom and bom.extra_production_percentage > 0:
            percent = bom.extra_production_percentage

            # Allowed range based on percentage variation
            min_allowed_qty = production.product_qty * (1 - percent)
            max_allowed_qty = production.product_qty * (1 + percent)

            if not (min_allowed_qty <= self.extra_production <= max_allowed_qty):
                raise UserError(
                    f"Entered quantity is outside allowed production tolerance.\n\n"
                    f"Planned Qty: {production.product_qty}\n"
                    f"Allowed Range ({percent * 100:.0f}% variation): {min_allowed_qty:.2f} to {max_allowed_qty:.2f}\n"
                    f"Entered: {self.extra_production}"
                )

        # production.extra_production += self.extra_production

        # self.env['stock.quant']._update_available_quantity(
        #     self.product_id,
        #     self.location_id,
        #     self.extra_production,
        #     lot_id=self.lot_id,
        # )
        # self.production_id.with_context(force_update=True).qty_producing = self.extra_production
        self.production_id.qty_producing = self.extra_production
        production.extra_production = production.qty_producing - production.product_qty
        if production.bom_id and production.product_id and production.product_qty > 0:
            moves_raw_values = production.with_context(qty_producing_value=production.qty_producing)._get_moves_raw_values()
            move_raw_dict = {move.bom_line_id.id: move for move in production.move_raw_ids.filtered(lambda m: m.bom_line_id)}
            for move_raw_values in moves_raw_values:
                if move_raw_values['bom_line_id'] in move_raw_dict:
                    move_raw_dict[move_raw_values['bom_line_id']].bom_uom_qty = move_raw_values['bom_uom_qty']


        production.message_post(
            body=f"Extra production of {self.extra_production} units added for {self.product_id.display_name} (Lot: {self.lot_id.name})."
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Extra production of {self.extra_production} units added for {self.product_id.display_name}.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

