# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit= 'stock.picking'

    def button_validate(self):
        if self.picking_type_id.code == 'incoming':
            for move_line in self.move_ids.filtered('purchase_line_id'):
                purchase_line = move_line.purchase_line_id
                receiving_quantity = move_line.quantity

                if purchase_line.product_uom != move_line.product_uom:
                    receiving_quantity = move_line.product_uom._compute_quantity(
                        move_line.quantity, purchase_line.product_uom
                    )
                if receiving_quantity > (purchase_line.product_qty - purchase_line.qty_received):
                    raise ValidationError(f"The Received Quantity for the product {move_line.name} cannot exceed Demand Quantity. The remaining demand quantity is {purchase_line.product_qty - purchase_line.qty_received} {purchase_line.product_uom.name}.")
        
        return super(StockPicking, self).button_validate()
