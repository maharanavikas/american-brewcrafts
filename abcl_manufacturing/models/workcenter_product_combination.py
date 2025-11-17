# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import MissingError, ValidationError, AccessError, UserError


class WorkcenterProductCombination(models.Model):
    _name = 'workcenter.product.combination'
    _description = 'Workcenter Product Combination'

    name = fields.Char(string="Combination Name", required=True)
    workcenter_category_id = fields.Many2one('mrp.workcenter.tag', string="Workcenter Category", required=True)
    description = fields.Text(string="Description")
    product_ids = fields.Many2many('product.product', string="Products")

    @api.constrains('workcenter_category_id', 'product_ids')
    def _check_duplicate_combination(self):
        for rec in self:
            if not rec.workcenter_category_id or not rec.product_ids:
                continue

            # All other combinations in the same category
            others = self.search([
                ('id', '!=', rec.id),
                ('workcenter_category_id', '=', rec.workcenter_category_id.id),
            ])

            current_set = set(rec.product_ids.ids)

            for other in others:
                other_set = set(other.product_ids.ids)

                if current_set & other_set:
                    raise ValidationError(
                        _("Some products in this combination already exist in another combination for the same category.")
                    )







