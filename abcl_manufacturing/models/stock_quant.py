from odoo import fields, models, api, _

class StockQuant(models.Model):
    _inherit = "stock.quant"

    manufacturing_date = fields.Date(string="Manufacturing Date", compute="_compute_manufacturing_date", inverse="_inverse_manufacturing_date", store=False)

    @api.depends("lot_id", "product_id")
    def _compute_manufacturing_date(self):
        for quant in self:
            if quant.lot_id and quant.lot_id.manufacturing_date:
                quant.manufacturing_date = quant.lot_id.manufacturing_date
            else:
                quant.manufacturing_date = quant.product_id.manufacturing_date

    def _inverse_manufacturing_date(self):
        for quant in self:
            if quant.lot_id:
                quant.lot_id.manufacturing_date = quant.manufacturing_date
                quant.product_id.manufacturing_date = quant.manufacturing_date
