# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class MrpProductionSchedule(models.Model):
    _inherit = 'mrp.production.schedule'

    def set_forecast_qty(self, date_index, quantity, period_scale=False):
        self.ensure_one()
        actual_quantity = float_round(float(quantity), precision_rounding=self.product_uom_id.rounding)
        date_start, date_stop = self.company_id._get_date_range(force_period=period_scale)[date_index]
       
        company_id = self.env.company
        date_range = company_id._get_date_range(force_period=period_scale)

        outgoing_qty, outgoing_qty_done = self._get_outgoing_qty(date_range)
        product = self.product_id
        rounding = product.uom_id.rounding

        key = ((date_start, date_stop), product, self.warehouse_id)
        outgoing_qty = float_round(outgoing_qty.get(key, 0.0) + outgoing_qty_done.get(key, 0.0), precision_rounding=rounding)
        
        additional_10_percent = outgoing_qty + outgoing_qty * (10/100)
        # lesser_10_percent = outgoing_qty - outgoing_qty * (10/100)

        if not actual_quantity > 0:
            raise UserError(
                f"Please set a +ve quantity for product {product.name}.")
        elif not actual_quantity <= additional_10_percent:
            raise UserError(
                f"The planned quantity must be maximum of {additional_10_percent} for product {product.name} as the planning threshold is allowed additional 10% of the actual quantity.")

        # if not (lesser_10_percent <= actual_quantity <= additional_10_percent):
        #     raise UserError(
        #         f"The planned quantity must be between  {lesser_10_percent} to {additional_10_percent} for product {product.name} as the planning threshold is allowed +/- 10% of the actual quantity.")
        
        return super(MrpProductionSchedule, self).set_forecast_qty(date_index, quantity, period_scale)
