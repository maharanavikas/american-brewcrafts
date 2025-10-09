# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit= 'stock.picking'

    def button_validate(self):
        if self.picking_type_id.code == 'incoming':
            for move_line in self.move_ids:
                if move_line.purchase_line_id and move_line.quantity > (move_line.purchase_line_id.product_qty)-(move_line.purchase_line_id.qty_received):
                    raise ValidationError(f"The Received Quantity for the product {move_line.name} cannot exceed Demand Quantity")
        return super(StockPicking, self).button_validate()

