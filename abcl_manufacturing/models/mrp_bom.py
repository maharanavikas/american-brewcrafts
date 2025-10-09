# -*- coding: utf-8 -*-

from odoo import api, fields, models

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    bom_source = fields.Selection([('self','Self'),('third_party','Third Party')] , default='self')
    product_categ_id = fields.Many2one('product.category', string='Product Category', related='product_id.categ_id')