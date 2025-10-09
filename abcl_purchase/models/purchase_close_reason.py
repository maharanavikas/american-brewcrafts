# -*- coding: utf-8 -*-
from odoo import models, fields

class PurchaseCloseReason(models.Model):
    _name = 'purchase.close.reason'
    _description = 'Purchase Close Reason'

    name = fields.Char(string="Reason", required=True)
