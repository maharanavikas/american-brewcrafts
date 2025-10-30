# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    minimum_qty = fields.Float(string="Monthly Maximum Quantity")
    manufacturing_date = fields.Date("Manufacturing Date")

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_bom_component = fields.Boolean(
        string="Used in BoM",
        compute="_compute_is_bom_component",
        store=True
    )

    @api.depends('bom_line_ids')
    def _compute_is_bom_component(self):
        for product in self:
            product.is_bom_component = bool(self.env['mrp.bom.line'].search_count([('product_id', '=', product.id)]))
