# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import date


class StockLot(models.Model):
    _inherit = "stock.lot"

    manufacturing_date = fields.Date("Manufacturing Date")

    @api.model_create_multi
    def create(self, vals_list):
        lots = super().create(vals_list)

        for lot, vals in zip(lots, vals_list):
            active_model = self.env.context.get("active_model")
            active_id = self.env.context.get("active_id")

            if (active_model == "mrp.production" and active_id and not vals.get("manufacturing_date")):
                mo = self.env["mrp.production"].browse(active_id)
                lot.manufacturing_date = date.today()

        return lots