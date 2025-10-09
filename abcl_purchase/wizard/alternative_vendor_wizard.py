# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AlternativeVendorWizard(models.TransientModel):
    _name = 'alternative.vendor.wizard'
    _description = 'Alternative Vendor Wizard'

    purchase_order = fields.Many2one('purchase.order', string="Purchase Order", required=True)

    vendor_info = fields.Many2many('product.supplierinfo', string="Vendors",compute="_compute_vendor_info", store=True)
    
    alternative_vendor = fields.Many2one(
        'res.partner', 
        string="Alternative Vendor", 
        domain="[('id', 'in', common_vendor_ids)]",
    )
    common_vendor_ids = fields.Many2many(
        'res.partner',
        compute='_compute_common_vendor_ids',
        string='Common Vendors',
        store=False,
    )

    @api.depends('purchase_order')
    def _compute_common_vendor_ids(self):
        for wizard in self:
            vendor_sets = []
            for line in wizard.purchase_order.order_line:
                if line.product_id:
                    vendors = line.product_id.seller_ids.mapped('partner_id')
                    vendor_sets.append(set(vendors.ids))

            if vendor_sets:
                common_ids = set.intersection(*vendor_sets)
                wizard.common_vendor_ids = self.env['res.partner'].browse(common_ids)
            else:
                wizard.common_vendor_ids = self.env['res.partner'].browse()

    def action_confirm(self):
        if not self.alternative_vendor:
            raise UserError("Please select an alternative vendor before confirming.")
    
        self.purchase_order.partner_id = self.alternative_vendor.id

    @api.depends('purchase_order')
    def _compute_vendor_info(self):
        for wizard in self:
            if wizard.purchase_order:
                products = wizard.purchase_order.order_line.mapped('product_id')
                if products:
                    wizard.vendor_info = products.mapped('seller_ids')
                else:
                    wizard.vendor_info = False
            else:
                wizard.vendor_info = False
