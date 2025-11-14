# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BottledBeer(models.Model):
    _name = 'bottled.beer'

    name = fields.Char(string="Beer Name", required=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", required=True)
    amount = fields.Float(string="Amount")
    bulk_liter = fields.Float(string="Bulk Liter per case", store=True)