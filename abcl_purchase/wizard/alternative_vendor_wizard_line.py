# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AlternativeVendorWizardLine(models.TransientModel):
    _name = 'alternative.vendor.wizard.line'
    _description = 'Alternative Vendor Wizard Line'

    wizard_id = fields.Many2one(
        'alternative.vendor.wizard', 
        string="Wizard",
        required=True,
        ondelete='cascade'
    )

    order_line_id = fields.Many2one(
        'purchase.order.line',
        string="PO Line",
        required=True
    )

    product_id = fields.Many2one(
        'product.product',
        string="Product",
        related='order_line_id.product_id',
        store=True,
        readonly=True
    )

    vendor_ids = fields.Many2many(
        'res.partner',
        string="Vendors",
        compute='_compute_vendors',
        store=False
    )

    @api.depends('product_id')
    def _compute_vendors(self):
        for line in self:
            line.vendor_ids = line.product_id.seller_ids.mapped('partner_id')
