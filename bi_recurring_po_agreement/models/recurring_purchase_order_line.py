# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class RecurringPurchaseOrderline(models.Model):
    _name = "recurring.purchase.order.line"
    _description = "Recurring Purchase Order line"

    recurring_order_id = fields.Many2one('recurring.purchase.order',string ="Recurring Purchase Order")
    product_id = fields.Many2one('product.product', string='Product',required = True)
    name = fields.Text(string='Description', required = True)
    product_uom_quantity = fields.Float(string='Quantity ', digits='Product Unit of Measure', default=1.0)
    product_qty = fields.Float(string='Quantity', default=1.0)
    price_unit = fields.Float('Unit Price', default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')


    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.write({
                        'name': self.product_id.name,
                        'price_unit': self.product_id.lst_price,
                        'product_uom': self.product_id.uom_id.id     
                      })