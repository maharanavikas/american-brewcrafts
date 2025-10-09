from odoo import models, fields, api
import datetime

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    manufacturing_date = fields.Date(
        string="Manufacturing Date",
        compute="_compute_expiration_date",
        store=True,
        help="Manufacturing date of the product, taken from the lot."
    )

    @api.depends('product_id', 'lot_id.expiration_date', 'lot_id.manufacturing_date', 'picking_id.scheduled_date')
    def _compute_expiration_date(self):
        super()._compute_expiration_date()

        for move_line in self:
            move_line.manufacturing_date = move_line.lot_id.manufacturing_date or False