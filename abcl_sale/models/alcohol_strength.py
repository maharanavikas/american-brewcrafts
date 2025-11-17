# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AlcoholStrength(models.Model):
    _name = 'alcohol.strength'

    name = fields.Char(string="Alcohol Strength", required=True)