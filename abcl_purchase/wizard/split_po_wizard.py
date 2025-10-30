# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class SplitPOWizard(models.TransientModel):
    _name = 'split.po.wizard'
    _description = 'Split Purchase Order Wizard'

    purchase_order = fields.Many2one('purchase.order', string="Purchase Order", required=True)
    vendor_ids = fields.One2many('split.po.wizard.line', 'wizard_id', string='Vendors')
    quantities_matched = fields.Boolean(
        string='Quantities Matched',
        compute='_compute_quantities_matched',
        store=False
    )

    @api.depends('vendor_ids.quantity', 'vendor_ids.product_id')
    def _compute_quantities_matched(self):
        for wizard in self:
            if not wizard.purchase_order:
                wizard.quantities_matched = False
                continue

            # Step 1: Get quantities from original PO
            original_qty = defaultdict(float)
            for line in wizard.purchase_order.order_line:
                original_qty[line.product_id.id] += line.product_qty

            # Step 2: Get quantities from wizard
            wizard_qty = defaultdict(float)
            for line in wizard.vendor_ids:
                if line.product_id:
                    wizard_qty[line.product_id.id] += line.quantity

            # Step 3: Compare sets and values
            if set(original_qty.keys()) != set(wizard_qty.keys()):
                wizard.quantities_matched = False
                continue

            matched = all(
                abs(original_qty[pid] - wizard_qty[pid]) < 1e-6
                for pid in original_qty
            )
            wizard.quantities_matched = matched

    def action_confirm(self):
        print(self.vendor_ids)
        self.create_new_pos(self.vendor_ids)
        self.purchase_order.button_cancel()

    # def create_new_pos(self, vendors_info=False):
    #     if vendors_info:
    #         for line in vendors_info:
    #             vals = {
    #                 'partner_id': line.partner_id.id,
    #                 'origin': line.po_id.name if line.po_id else '',
    #                 'product_categ_id': line.product_id.categ_id.id,
    #                 'order_line': [(0, 0, {
    #                     'date_planned': fields.Date.today(),
    #                     'name': line.product_id.display_name,
    #                     'product_id': line.product_id.id,
    #                     'product_qty': line.quantity,
    #                     'product_uom': line.product_id.uom_id.id,
    #                 })]
    #             }
    #             new_purchase = self.env['purchase.order'].create(vals)
    #             print("new_po created", new_purchase.name)
    def create_new_pos(self, vendors_info=False):
        if vendors_info:
            for line in vendors_info:
                # Detect if original PO or line was created from MPS
                from_mps = line.po_id.order_line.filtered(lambda l: l.product_id == line.product_id).mapped('from_mps')
                from_mps_flag = any(from_mps)
                print("from_mps",from_mps)
                print("from_mps_flag",from_mps_flag)

                vals = {
                    'partner_id': line.partner_id.id,
                    'origin': line.po_id.name if line.po_id else '',
                    'product_categ_id': line.product_id.categ_id.id,
                    'order_line': [(0, 0, {
                        'date_planned': fields.Date.today(),
                        'name': line.product_id.display_name,
                        'product_id': line.product_id.id,
                        'product_qty': line.quantity,
                        'product_uom': line.product_id.uom_id.id,
                        'from_mps': from_mps_flag,  # Store flag
                    })]
                }
                print("vals", vals)

                new_purchase = self.env['purchase.order'].with_context(from_mps=from_mps_flag).create(vals)
