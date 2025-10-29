# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit= 'stock.picking'

    def button_validate(self):
        if self.picking_type_id.code == 'incoming':
            for move_line in self.move_ids:
                if move_line.product_uom == move_line.purchase_line_id.product_uom:
                    if move_line.purchase_line_id and move_line.quantity > (move_line.purchase_line_id.product_qty)-(move_line.purchase_line_id.qty_received):
                        raise ValidationError(f"The Received Quantity for the product {move_line.name} cannot exceed Demand Quantity")
                elif move_line.product_uom.name == 'g':
                    kg_uom = self.env.ref('uom.product_uom_kgm')
                    g_uom = self.env.ref('uom.product_uom_gram')
                    qty_in_units = g_uom._compute_quantity(move_line.quantity, kg_uom)
                    print(qty_in_units)
                    if move_line.purchase_line_id and qty_in_units > (move_line.purchase_line_id.product_qty)-(move_line.purchase_line_id.qty_received):
                        raise ValidationError(f"The Received Quantity for the product {move_line.name} cannot exceed Demand Quantity")
                else:    
                    raise ValidationError(f"The UoM for the product {move_line.name} in Stock Move Line must be same as UoM in Purchase Order Line")        
        return super(StockPicking, self).button_validate()

