# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    minimum_qty = fields.Float(string="Monthly Maximum Quantity")
    manufacturing_date = fields.Date("Manufacturing Date")
