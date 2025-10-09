# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    
    po_name = fields.Char(string="Name")
    recurring_purchase_order_agreement_count = fields.Integer(compute='_compute_recurring_purchase_order_agreement_count', string="Recurring Purchase Order")

    def _compute_recurring_purchase_order_agreement_count(self):
        for record in self:
            purchase_id = self.env['recurring.purchase.order'].search([('order_id', '=', record.id)])
            if not record.po_name and purchase_id:
                total = 0
                for purchase in purchase_id:
                    count_id = self.env['purchase.order'].search_count([('po_name', '=', purchase.name)])
                    total += count_id
                    record.recurring_purchase_order_agreement_count = total
            else:
                record.recurring_purchase_order_agreement_count = 0

    def recurring_purchase_order_agreement_button(self):
        purchase_id = self.env['recurring.purchase.order'].search([('order_id', '=', self.id)])
        purchase_ids = []
        for rec in purchase_id:
            count_id = self.env['purchase.order'].search([('po_name', '=', rec.name)])
            for record in count_id:
                 purchase_ids.append(record.id)
        return {
            'name': 'Recurring Purchase Order Agreement',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'domain': [('id','in',purchase_ids)]
        }