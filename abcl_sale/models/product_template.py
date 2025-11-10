# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bottled_beer_id = fields.Many2one('bottled.beer', "Bottled Beer")
