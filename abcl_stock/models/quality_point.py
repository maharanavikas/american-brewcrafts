# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class QualityPoint(models.Model):
    _inherit = "quality.point"

    measure_on = fields.Selection([
        ('operation', 'Operation'),
        ('product', 'Product'),
        ('move_line', 'Quantity'),
        ('lots_serial_no', 'Lots & Serial No.')], string="Control per", default='product', required=True,
        help="""Operation = One quality check is requested at the operation level.
                Product = A quality check is requested per product.
                Quantity = A quality check is requested for each new product quantity registered, with partial quantity checks also possible.
                Lots & Serial No = A quality check is requested per Lot & Serial no.""")

    product_cell = fields.Char('Product Cell No.')
    qty_cell = fields.Char('Quantity Cell No.')
    uom_cell = fields.Char('UOM Cell No.')
    # quality_point_product_ids = fields.One2many('quality.point.products', 'quality_point_id',"Products", compute="_onchange_product_ids", store=True)
    #
    #
    # @api.depends('product_ids')
    # def _onchange_product_ids(self):
    #     self.quality_point_product_ids = [(5, 0, 0)]
    #     product_lines = []
    #     for product in self.product_ids:
    #         product_lines.append((0, 0, {
    #             'product_id': product.id,
    #             'uom_id': product.uom_id.id,
    #             'quantity': product.qty_available or 1.0,
    #         }))
    #     self.quality_point_product_ids = product_lines

    def _get_checks_values(self, products, company_id, existing_checks=False):
        quality_points_list = []
        point_values = []
        if not existing_checks:
            existing_checks = []
        for check in existing_checks:
            point_key = (check.point_id.id, check.team_id.id, check.product_id.id, check.lot_id.id if hasattr(check, 'lot_id') else False)
            quality_points_list.append(point_key)

        for point in self:
            if not point.check_execute_now():
                continue

            point_products = point.product_ids

            if point.product_category_ids:
                point_product_from_categories = self.env['product.product'].search([
                    ('categ_id', 'child_of', point.product_category_ids.ids),
                    ('id', 'in', products.ids)
                ])
                point_products |= point_product_from_categories

            if not point.product_ids and not point.product_category_ids:
                point_products |= products

            if point.measure_on == 'lots_serial_no':
                production = self.env.context.get('production')
                if production:
                    for move in production.move_finished_ids.filtered(lambda m: not m.scrapped):
                        for ml in move.move_line_ids:
                            if ml.lot_id and ml.product_id in point_products:
                                point_key = (point.id, point.team_id.id, ml.product_id.id, ml.lot_id.id)
                                if point_key in quality_points_list:
                                    continue
                                point_values.append({
                                    'point_id': point.id,
                                    'measure_on': point.measure_on,
                                    'team_id': point.team_id.id,
                                    'product_id': ml.product_id.id,
                                    'lot_id': ml.lot_id.id,
                                    'company_id': company_id,
                                    'production_id': production.id,
                                })
                                quality_points_list.append(point_key)
                continue  # Skip default product-based handling

            for product in point_products:
                if product not in products:
                    continue
                point_key = (point.id, point.team_id.id, product.id, False)
                if point_key in quality_points_list:
                    continue
                point_values.append({
                    'point_id': point.id,
                    'measure_on': point.measure_on,
                    'team_id': point.team_id.id,
                    'product_id': product.id,
                    'company_id': company_id,
                })
                quality_points_list.append(point_key)

        return point_values


class QualityCheck(models.Model):
    _inherit = "quality.check"

    lot_id = fields.Many2one('stock.lot', string="Lot/Serial Number")
    measure_on = fields.Selection([
        ('operation', 'Operation'),
        ('product', 'Product'),
        ('move_line', 'Quantity'),
        ('lots_serial_no', 'Lots & Serial No.')], string="Control per", default='product', required=True,
        help="""Operation = One quality check is requested at the operation level.
                Product = A quality check is requested per product.
                Quantity = A quality check is requested for each new product quantity registered, with partial quantity checks also possible.
                Lots & Serial No = A quality check is requested per Lot & Serial no.""")



