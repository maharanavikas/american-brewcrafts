# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from datetime import date
from odoo.exceptions import UserError, ValidationError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('product_tmpl_id.bom_ids', '!=', False)]",
        required=True
    )
    production_source = fields.Selection([('self','Self'),('third_party','Third Party')])
    product_categ_id = fields.Many2one('product.category', string='Product Category', related='product_id.categ_id')
    brew_number = fields.Char(string="Brew Number")
    brew_label = fields.Char(compute="_compute_brew_label")
    quantity_available = fields.Float(string="Quantity Available", compute="_compute_quantity_available", store=False)

    def _compute_quantity_available(self):
        for rec in self:
            rec.quantity_available = rec.lot_producing_id.product_qty

    def _compute_brew_label(self):
        for rec in self:
            if rec.product_categ_id.name == "Wort Liquid":
                rec.brew_label = "Brew Number"
            elif rec.product_categ_id.name == "Young Beer":
                rec.brew_label = "UT Number"
            elif rec.product_categ_id.name == "Bulk Beer Stock":
                rec.brew_label = "BBT Number"
            elif rec.product_categ_id.name == "Finished Goods":
                rec.brew_label = "Batch Number"
            else:
                rec.brew_label = "Brew Number"


    def _prepare_stock_lot_values(self):
        self.ensure_one()
        vals = super()._prepare_stock_lot_values()
        vals['manufacturing_date'] = date.today()
        return vals
    
    def _get_move_raw_values(self, product, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        data = super(MrpProduction, self)._get_move_raw_values(
            product, product_uom_qty, product_uom, operation_id, bom_line)
        data.update({
            'bom_uom_qty': data['product_uom_qty'],
            'deviation_percentage': 0,
        })
        return data

    def button_mark_done(self):
        for record in self.workorder_ids:
            if record.quality_check_fail:
                raise ValidationError("You cannot mark the Production as Done as Quality Checks for the components have failed")
        res = super(MrpProduction, self).button_mark_done()
        return res

    # def _generate_finished_moves(self):
    #     res = super()._generate_finished_moves()
    #     for move in self.move_finished_ids:
    #         move = move.with_context(default_production_id=self.id)
    #     return res
