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
    location_id = fields.Many2one(
        'stock.location', 'From', related='stock_move_id.location_id')
    location_dest_id = fields.Many2one(
        'stock.location', 'TO', related='stock_move_id.location_dest_id')
    state = fields.Selection('Status', related='stock_move_id.state')
    stock_lot_id = fields.Char(
        string='Lot',
        compute='_compute_stock_lot_id',
        store=True,
        readonly=True
    )

    @api.depends('stock_move_id')
    def _compute_stock_lot_id(self):
        for record in self:
            if record.stock_move_id:
                lot_names = record.stock_move_id.move_line_ids.mapped('lot_id.name')
                record.stock_lot_id = ', '.join(lot_names) if lot_names else ''
            else:
                record.stock_lot_id = ''

    @api.depends('quantity', 'remaining_qty')
    def _compute_consumed_qty(self):
        for svl in self:
            svl.consumed_qty = (svl.quantity or 0.0) - (svl.remaining_qty or 0.0)