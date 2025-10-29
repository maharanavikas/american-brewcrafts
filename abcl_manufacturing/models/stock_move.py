# -*- coding: utf-8 -*-
from Tools.scripts.dutree import store
from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError

class StockMove(models.Model):
    _inherit = 'stock.move'

    bom_uom_qty = fields.Float(
        'Consumption Quantity',
        digits='Product Unit of Measure',
        default=0,
        compute="update_bom_demand",
        store=True
    )
    deviation_percentage = fields.Float(
        "Deviation Percentage", compute="_compute_bom_quantity_deviations", digits='Product Unit of Measure', store=True)
    qty_difference = fields.Float(
        "Quantity Difference", compute="_compute_bom_quantity_deviations", digits='Product Unit of Measure', store=True)
    date_start = fields.Datetime(
        'Start',related='raw_material_production_id.date_start',)
    date_finished = fields.Datetime(
        'End', related='raw_material_production_id.date_finished',)

    @api.depends('raw_material_production_id.qty_producing','bom_uom_qty','product_uom_qty', 'quantity')
    def _compute_bom_quantity_deviations(self):
        for move in self:
            move.qty_difference = move.bom_uom_qty - move.quantity
            # if (not move.bom_uom_qty and not move.quantity):
            #     move.deviation_percentage = 0
            #     continue
            # move.deviation_percentage = (move.bom_uom_qty - move.quantity) / move.quantity * 100
            if not move.quantity:
                move.deviation_percentage = 0.0
            else:
                move.deviation_percentage = ((move.bom_uom_qty - move.quantity) / move.quantity) * 100

    @api.depends('raw_material_production_id.qty_producing','product_uom_qty','quantity')
    def update_bom_demand(self):
        print('raw_material_production_id.qty_producing')
        for rec in self:
            # production = rec.production_id
            production = rec.raw_material_production_id
            print('raw_material_production_id//',production)
            if production.bom_id and production.product_id and production.product_qty > 0:
                moves_raw_values = production.with_context(qty_producing_value=production.qty_producing)._get_moves_raw_values()
                move_raw_dict = {move.bom_line_id.id: move for move in
                                 production.move_raw_ids.filtered(lambda m: m.bom_line_id)}
                for move_raw_values in moves_raw_values:
                    if move_raw_values['bom_line_id'] in move_raw_dict:
                        move_raw_dict[move_raw_values['bom_line_id']].bom_uom_qty = move_raw_values['bom_uom_qty']

    def action_view_lots(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Lot/Serial Numbers'),
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.lot_ids.ids)],
            'context': {'default_product_id': self.product_id.id},
        }


    @api.model
    def action_generate_lot_line_vals(self, context, mode, first_lot, count, lot_text):
        vals_list = super().action_generate_lot_line_vals(context, mode, first_lot, count, lot_text)

        manufacturing_date = context.get('default_manufacturing_date')
        if manufacturing_date:
            for vals in vals_list:
                vals['manufacturing_date'] = manufacturing_date
                if vals.get('lot_name') and not vals.get('lot_id'):
                    vals['manufacturing_date'] = manufacturing_date

        return vals_list


    def _create_lot_ids_from_move_line_vals(self, vals_list, product_id, company_id=False):
        """ This method will search or create the lot_id from the lot_name and set it in the vals_list
        """
        lot_names = {vals['lot_name'] for vals in vals_list if vals.get('lot_name')}
        lot_ids = self.env['stock.lot'].search([
            ('product_id', '=', product_id),
            '|', ('company_id', '=', company_id), ('company_id', '=', False),
            ('name', 'in', list(lot_names)),
        ])

        lot_names -= set(lot_ids.mapped('name'))
        lots_to_create_vals = [
            {'product_id': product_id, 'name': lot_name, 'manufacturing_date': vals_list[i].get('manufacturing_date')}
            for i, lot_name in enumerate(lot_names)
            if vals_list[i].get('manufacturing_date')
        ]
        print("lots_to_create_vals",lots_to_create_vals)
        lot_ids |= self.env['stock.lot'].create(lots_to_create_vals)

        lot_id_by_name = {lot.name: lot.id for lot in lot_ids}
        for vals in vals_list:
            lot_name = vals.get('lot_name', None)
            if not lot_name:
                continue
            vals['lot_id'] = lot_id_by_name[lot_name]
            vals['lot_name'] = False
            if vals.get('lot_id') and vals.get('manufacturing_date'):
                lot = self.env['stock.lot'].browse(vals['lot_id'])
                lot.product_id.write({'manufacturing_date': vals['manufacturing_date']})

    def open_form_view(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
            'views': [(self.env.ref('stock.view_move_form').id, 'form')],
        }
