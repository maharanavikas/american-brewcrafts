# -*- coding: utf-8 -*-
from odoo import _, fields, models, tools, api
from odoo.exceptions import UserError


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    consumed_qty = fields.Float(
        string="Consumed Quantity",
        compute="_compute_consumed_qty",
        digits='Product Unit of Measure',
        readonly=True,
        store=True
    )

    @api.depends('quantity', 'remaining_qty')
    def _compute_consumed_qty(self):
        for svl in self:
            svl.consumed_qty = (svl.quantity or 0.0) - (svl.remaining_qty or 0.0)