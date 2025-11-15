from odoo import _, api, fields, models
from odoo.osv import expression


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    is_internal_consumption = fields.Boolean(string="Internal Consumption", help="Is this picking type for internal consumption operations?")