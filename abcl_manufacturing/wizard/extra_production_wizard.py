# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

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

        production.extra_production += self.extra_production

        self.env['stock.quant']._update_available_quantity(
            self.product_id,
            self.location_id,
            self.extra_production,
            lot_id=self.lot_id,
        )

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

