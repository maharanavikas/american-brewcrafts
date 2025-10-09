# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    qty_units = fields.Float("Qty (Units)")
    qty_liters = fields.Float("Qty (Liters)")

