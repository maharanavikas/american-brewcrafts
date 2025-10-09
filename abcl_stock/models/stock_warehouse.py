# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    responsible_user_id = fields.Many2one('res.users', "Responsible User")