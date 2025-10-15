# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from datetime import date
from odoo.exceptions import UserError, ValidationError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_id = fields.Many2one('product.product', 'Product', domain="[('product_tmpl_id.bom_ids', '!=', False)]", required=True)
    production_source = fields.Selection([('self','Self'),('third_party','Third Party')])
    product_categ_id = fields.Many2one('product.category', string='Product Category', related='product_id.categ_id')
    brew_number = fields.Char(string="Brew Number")
    brew_label = fields.Char(compute="_compute_brew_label")
    quantity_available = fields.Float(string="Quantity Available", compute="_compute_quantity_available", store=False)
    extra_production = fields.Float(string="Extra Production", tracking=True)

    # def action_update_extra_quantity(self):
    #     """Update on-hand quantity for the same lot used in this MO."""
    #     for record in self:
    #         if not record.product_id:
    #             raise UserError("No product defined for this production order.")
    #         if record.extra_production <= 0:
    #             raise UserError("Please enter a valid extra production quantity greater than zero.")
    #         if not record.finished_move_line_ids:
    #             raise UserError("No finished move lines found for this production order.")
    #
    #         finished_move_line = record.finished_move_line_ids.filtered(lambda l: l.lot_id)
    #         if not finished_move_line:
    #             raise UserError("No lot/serial number found in finished move lines.")
    #         lot = finished_move_line[0].lot_id
    #
    #         location = record.location_dest_id or record.location_src_id
    #         if not location:
    #             raise UserError("No valid location found to update stock.")
    #
    #         self.env['stock.quant']._update_available_quantity(
    #             record.product_id,
    #             location,
    #             record.extra_production,
    #             lot_id=lot,
    #         )

    def action_open_extra_production_wizard(self):
        """Open the Extra Production Wizard with default values."""
        self.ensure_one()

        finished_move_line = self.finished_move_line_ids.filtered(lambda l: l.lot_id)
        lot_id = finished_move_line[0].lot_id.id if finished_move_line else False

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'extra.production.wizard',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Register Extra Production',
            'context': {
                'default_production_id': self.id,
                'default_product_id': self.product_id.id,
                'default_location_id': self.location_dest_id.id or self.location_src_id.id,
                'default_lot_id': lot_id,
            },
        }

    def _compute_quantity_available(self):
        for rec in self:
            rec.quantity_available = rec.lot_producing_id.product_qty

    def _compute_brew_label(self):
        for rec in self:
            if rec.product_categ_id.is_wort == True:
                rec.brew_label = "Brew Number"
            elif rec.product_categ_id.is_yb == True:
                rec.brew_label = "UT Number"
            elif rec.product_categ_id.is_bbs == True:
                rec.brew_label = "BBT Number"
            elif rec.product_categ_id.is_fg == True:
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
        res = super(MrpProduction, self).button_mark_done()
        if self.quality_check_fail:
            raise ValidationError("You cannot mark the Production as Done Pre Production Quality Checks for the components have failed")
        for record in self.workorder_ids:
            if record.quality_check_fail:
                raise ValidationError("You cannot mark the Production as Done as Quality Checks for the components have failed") 
        return res

    # def _generate_finished_moves(self):
    #     res = super()._generate_finished_moves()
    #     for move in self.move_finished_ids:
    #         move = move.with_context(default_production_id=self.id)
    #     return res


    def action_generate_component_lot_qc(self):
        print("inside action_generate_component_lot_qc .........")
        QP = self.env['quality.point'].sudo()
        QualityCheck = self.env['quality.check'].sudo()

        check_vals_list = []
        seen = set()

        existing_checks = QualityCheck.search([
            ('production_id', 'in', self.ids),
            ('measure_on', '=', 'lots_serial_no'),
        ])
        existing_keys = set(
            (qc.point_id.id, qc.production_id.id, qc.product_id.id, qc.lot_id.id, qc.measure_on)
            for qc in existing_checks
        )

        for production in self:
            # Get Manufacturing quality points for lots/serials
            manu_points = QP.search([
                ('measure_on', '=', 'lots_serial_no'),
                ('picking_type_ids.name', '=', 'Manufacturing')
            ])
            if not manu_points:
                continue

            component_moves = production.move_raw_ids.filtered(lambda m: not m.scrapped)

            for move in component_moves:
                lots = (move.mapped('move_line_ids.lot_id') | move.lot_ids)
                if not lots:
                    continue

                for lot in lots:
                    for point in manu_points:
                        if point.product_ids and move.product_id not in point.product_ids:
                            continue

                        key = (point.id, production.id, move.product_id.id, lot.id, 'lots_serial_no')
                        if key in seen or key in existing_keys:
                            continue
                        seen.add(key)
                        check_vals_list.append({
                            'point_id': point.id,
                            'team_id': point.team_id.id,
                            'measure_on': 'lots_serial_no',
                            'production_id': production.id,
                            'company_id': production.company_id.id,
                            'product_id': move.product_id.id,
                            'lot_id': lot.id,
                        })

        if not check_vals_list:
            raise ValidationError(
                "Quality Checks have already been generated for all existing lots.\n"
                "No new lots found to create new Quality Checks."
            )
        QualityCheck.create(check_vals_list)

        action = self.env["ir.actions.actions"]._for_xml_id("quality_control.quality_check_action_main")
        action['domain'] = [('production_id', 'in', self.ids)]
        action['context'] = {
            'search_default_groupby_point': 0,
            'default_production_id': self[:1].id,
        }
        return action

    def _action_confirm_mo_backorders(self):
        super()._action_confirm_mo_backorders()
        processed_groups = set()
        for mo in self:
            group = mo.procurement_group_id
            if not group or group.id in processed_groups:
                continue
            processed_groups.add(group.id)

            related_mos = self.env['mrp.production'].search([('procurement_group_id', '=', group.id)])
            for rmo in related_mos:
                lots = rmo.move_raw_ids.mapped('lot_ids')
                valid_lot_ids = set(lots.ids)
                if not valid_lot_ids:
                    continue

                mo_qcs = self.env['quality.check'].search([
                    ('production_id', '=', rmo.id),
                    ('lot_id', '!=', False),
                ])

                invalid_qcs = mo_qcs.filtered(lambda qc: qc.lot_id.id not in valid_lot_ids)
                if invalid_qcs:
                    invalid_qcs.sudo().unlink()
