# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AlternativeVendorWizard(models.TransientModel):
    _name = 'alternative.vendor.wizard'
    _description = 'Alternative Vendor Wizard'

    purchase_order = fields.Many2one('purchase.order', string="Purchase Order", required=True)
    line_ids = fields.One2many(
        'alternative.vendor.wizard.line', 
        'wizard_id', 
        string="Product Lines"
    )
    alternative_vendor = fields.Many2one(
        'res.partner', 
        string="Alternative Vendor", 
    )

    @api.onchange('purchase_order')
    def _onchange_purchase_order(self):
        if self.purchase_order:
            lines = []
            for line in self.purchase_order.order_line:
                lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'order_line_id': line.id,
                }))
            self.line_ids = lines
        else:
            self.line_ids = [(5, 0, 0)]  # Clears existing lines

    def action_confirm(self):
        if not self.alternative_vendor:
            raise UserError("Please select an alternative vendor before confirming.")
        
        self.purchase_order.partner_id = self.alternative_vendor.id
        