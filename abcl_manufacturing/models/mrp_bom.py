# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import float_round

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    bom_source = fields.Selection([('self','Self'),('third_party','Third Party')] , default='self')
    product_categ_id = fields.Many2one('product.category', string='Product Category', related='product_id.categ_id')

    def explode(self, product, quantity, picking_type=False, never_attribute_values=False):
        """
            Explodes the BoM and creates two lists with all the information you need: bom_done and line_done
            Quantity describes the number of times you need the BoM: so the quantity divided by the number created by the BoM
            and converted into its UoM
        """
        product_ids = set()
        product_boms = {}
        def update_product_boms():
            products = self.env['product.product'].browse(product_ids)
            product_boms.update(self._bom_find(products, picking_type=picking_type or self.picking_type_id,
                company_id=self.company_id.id, bom_type='phantom'))
            # Set missing keys to default value
            for product in products:
                product_boms.setdefault(product, self.env['mrp.bom'])

        boms_done = [(self, {'qty_should_consume':quantity, 'qty': quantity, 'product': product, 'original_qty': quantity, 'parent_line': False})]
        lines_done = []

        bom_lines = []
        for bom_line in self.bom_line_ids:
            product_id = bom_line.product_id
            bom_lines.append((bom_line, product, quantity, False))
            product_ids.add(product_id.id)
        update_product_boms()
        product_ids.clear()
        while bom_lines:
            current_line, current_product, current_qty, parent_line = bom_lines[0]
            bom_lines = bom_lines[1:]

            if current_line._skip_bom_line(current_product, never_attribute_values):
                continue
            print("current_line", current_line)
            line_quantity = current_qty * current_line.product_qty
            should_consume_line_quantity = current_qty * (current_line.product_consumed_qty or current_line.product_qty)
            print("line_quantity",line_quantity)
            print("current_qty",current_qty)
            if current_line.product_id not in product_boms:
                update_product_boms()
                product_ids.clear()
            bom = product_boms.get(current_line.product_id)
            if bom:
                converted_line_quantity = current_line.product_uom_id._compute_quantity(
                    line_quantity / bom.product_qty, bom.product_uom_id, round=False
                )
                converted_should_consume_line_quantity = current_line.product_uom_id._compute_quantity(
                    should_consume_line_quantity / bom.product_qty, bom.product_uom_id, round=False
                )
                bom_lines = [(line, current_line.product_id, converted_line_quantity, current_line) for line in bom.bom_line_ids] + bom_lines
                for bom_line in bom.bom_line_ids:
                    if bom_line.product_id not in product_boms:
                        product_ids.add(bom_line.product_id.id)
                boms_done.append((bom, { 'qty_should_consume': converted_should_consume_line_quantity,
                    'qty': converted_line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': current_line}))
            else:
                # We round up here because the user expects that if he has to consume a little more, the whole UOM unit
                # should be consumed.
                rounding = current_line.product_uom_id.rounding
                line_quantity = float_round(line_quantity, precision_rounding=rounding, rounding_method='UP')
                should_consume_line_quantity = float_round(should_consume_line_quantity, precision_rounding=rounding, rounding_method='UP')
                lines_done.append((current_line, {'qty_should_consume': should_consume_line_quantity,
                    'qty': line_quantity, 'product': current_product, 'original_qty': quantity, 'parent_line': parent_line}))

        return boms_done, lines_done


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    product_consumed_qty = fields.Float('Consumed Quantity', digits='Product Unit of Measure')