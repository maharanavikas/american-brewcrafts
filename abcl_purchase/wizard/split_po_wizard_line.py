# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class SplitPOWizardLine(models.TransientModel):
    _name = 'split.po.wizard.line'
    _description = 'Vendor and Quantity Line'

    wizard_id = fields.Many2one('split.po.wizard', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Vendor', required=True, domain="[('id', 'in', wizard_vendor_ids)]")
    quantity = fields.Float(string='Quantity', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, domain="[('id', 'in', wizard_product_ids)]")
    po_id = fields.Many2one('purchase.order', "PO Reference", related="wizard_id.purchase_order", store=True)

    wizard_product_ids = fields.Many2many(
        'product.product', compute='_compute_wizard_product_ids')
    wizard_vendor_ids = fields.Many2many('res.partner', compute='_compute_available_supplier_ids')

    @api.depends('wizard_id')
    def _compute_wizard_product_ids(self):
        for record in self:
            wizard = record.wizard_id
            if wizard and wizard.purchase_order:
                product_ids = wizard.purchase_order.order_line.mapped('product_id')
                record.wizard_product_ids = product_ids
            else:
                record.wizard_product_ids = []

    @api.depends('product_id')
    def _compute_available_supplier_ids(self):
        for record in self:
            if record.product_id:
                vendor_ids = record.product_id.seller_ids.mapped('partner_id')
                record.wizard_vendor_ids = vendor_ids.ids
            else:
                record.wizard_vendor_ids = []
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if not self.partner_id or not self.product_id or not self.po_id:
            return

        duplicates = self.wizard_id.vendor_ids.filtered(lambda line:
            line.partner_id == self.partner_id and
            line.product_id == self.product_id and
            line.po_id == self.po_id
        )
        if len(duplicates)>1:
            raise UserError("Same Vendor cannot be added for the same Product in this Purchase Order.")

