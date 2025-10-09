# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class QualityPointProducts(models.Model):
    _name = "quality.point.products"

    product_id = fields.Many2one('product.product', "Products")
    uom_id = fields.Many2one('uom.uom', "UOM")
    quantity = fields.Float('Quantity')
    quality_point_id = fields.Many2one('quality.point', "Quality Point")
