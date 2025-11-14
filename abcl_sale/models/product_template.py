# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bottled_beer_id = fields.Many2one('bottled.beer', "Bottled Beer")
    bulk_beer_per_liter = fields.Float(related='bottled_beer_id.bulk_liter', string="Bulk Beer Per Liter", store=True)
