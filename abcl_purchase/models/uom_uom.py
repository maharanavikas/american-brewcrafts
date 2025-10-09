# -*- coding: utf-8 -*-
from odoo import models, fields, api
import uuid

class Uom(models.Model):
    _inherit = 'uom.uom'

    alias = fields.Char(string="Alias")