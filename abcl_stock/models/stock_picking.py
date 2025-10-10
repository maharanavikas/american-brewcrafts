# -*- coding: utf-8 -*-
from collections import defaultdict
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    gate_entry_number = fields.Char('Gate Entry Number', copy=False)
    security_id = fields.Many2one('res.partner', string='Security Name', copy=False)
    security_signature = fields.Binary(string="Security Signature", copy=False)
    purpose = fields.Char("Purpose")
    requested_user_id = fields.Many2one('res.users', "Requested User")
    # purchase_id = fields.Many2one(
    #     'purchase.order', related='move_ids.purchase_line_id.order_id',
    #     string="Purchase Orders", readonly=False)
    vendor_inovice_no = fields.Char("Vendor Invoice No.")
    receipt_sequence_no = fields.Char("Receipt Sequence No.")
    driver_id = fields.Many2one('res.partner', string='Driver')
    delivery_fleet_tracking_ids = fields.One2many('fleet.vehicle.tracking', 'dispatch_id', string='Delivery Fleet Tracking')

    journal_entry_count = fields.Integer(
        string="Journal Entries Count",
        compute="_compute_journal_entry_count"
    )

    dispatch_sign_status = fields.Selection([('pending', 'Pending'), ('signed', 'Signed')], 
                                            string="Dispatch Sign Status", default='pending')

    accountant_sign_status = fields.Selection([('pending', 'Pending'),('signed', 'Signed')], 
                                              string="Accountant Sign Status", default='pending')
 
    def _compute_journal_entry_count(self):
        for picking in self:
            picking.journal_entry_count = self.env['account.move'].search_count([
                ('stock_move_id.picking_id', '=', picking.id)
            ])
 
    def action_view_journal_entries(self):
        self.ensure_one()
        return {
            'name': 'Journal Entries',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('stock_move_id.picking_id', '=', self.id)],
            'context': dict(self._context, create=False),
        }

    def send_fleet_tracking(self):
        if not self.driver_id:
            raise ValidationError("Please select a driver before sending fleet tracking.")
        template = self.env.ref('abcl_stock.template_fleet_tracking_mail')
        template.send_mail(self.id)

    def action_generate_entry_number(self):
        for picking in self:
            if not picking.gate_entry_number:
                picking.gate_entry_number = self.env['ir.sequence'].next_by_code('stock.picking.gate.entry.number')

    """def button_validate(self):
        res = super(StockPicking, self).button_validate()

        for picking in self:
            if picking.requested_user_id:
                template = self.env.ref('abcl_stock.abcl_delivery_order_approved_mail_template')
                if template:
                    template.send_mail(picking.id)

        return res"""

    # def button_validate(self):
    #     for picking in self:
    #         if picking.picking_type_code == 'outgoing' and picking.sale_id:
    #             if not picking.sign_request_id:
    #                 raise ValidationError("Please generate a sign request before validating.")
    #
    #             if picking.sign_request_state != 'signed':
    #                 raise ValidationError("You cannot validate this delivery until it is fully signed.")
    #
    #     res = super(StockPicking, self).button_validate()
    #
    #     for picking in self:
    #         if picking.picking_type_code == 'outgoing' and picking.requested_user_id:
    #             template = self.env.ref('abcl_stock.abcl_delivery_order_approved_mail_template')
    #             if template:
    #                 template.send_mail(picking.id)
    #
    #     return res

    # Excise report
    def action_excise_report(self):
        return self.env.ref('abcl_stock.action_excise_report_delivery_order').report_action(self)

    def total_goods(self):
        all_goods_lines = self.move_ids.filtered(lambda move: move.product_id.type == 'consu')
        total_goods_qty = sum(product.quantity for product in all_goods_lines)
        return total_goods_qty    
    

    def _send_accountant_mail(self):
        """Send sign request mail to accountant after dispatch signs."""
        template = self.env.ref('abcl_sale.email_template_stock_picking_sign_request', raise_if_not_found=True)
        base_url = self._get_dispatch_checklist_url()

        if not self.finance_user_id or not self.finance_user_id.partner_id.email:
            return

        partner = self.finance_user_id.partner_id
        ctx = {
            'recipient_name': partner.name,
            'dispatch_role_label': 'Accountant',
            'dispatch_role_code': 'accountant',
            'dispatch_sign_order': 2,
            'dispatch_checklist_url': f"{base_url}#accountant",
        }
        email_values = {
            'email_to': partner.email,
            'recipient_ids': [(6, 0, [partner.id])],
        }
        template.with_context(ctx).send_mail(self.id, email_values=email_values, force_send=True)
        self.message_post(body=f"Sign request sent to accountant: {partner.name}")

    
############for historical data import#########333
    def button_validate(self):
        for picking in self:
            if picking.picking_type_code == 'outgoing' and picking.sale_id:
                if picking.is_dispatch_sent == False:
                    raise ValidationError("Please generate a sign request before validating.")

                if not picking.dispatch_signature or not picking.accountant_signature:
                    raise ValidationError("You cannot validate this delivery until it is fully signed.")

        res = super(StockPicking, self).button_validate()

        for picking in self:
            if picking.picking_type_code == 'outgoing' and picking.requested_user_id:
                template = self.env.ref('abcl_stock.abcl_delivery_order_approved_mail_template')
                if template:
                    template.send_mail(picking.id)

            picking.date_done = picking.scheduled_date

            if picking.move_line_ids and picking.scheduled_date:
                picking.move_line_ids.write({'date': picking.scheduled_date})

            if picking.move_ids_without_package and picking.scheduled_date:
                picking.move_ids_without_package.write({'date': picking.scheduled_date})

            if picking.move_ids_without_package and picking.scheduled_date:
                valuation_layers = self.env['stock.valuation.layer'].search([
                    ('stock_move_id', 'in', picking.move_ids_without_package.ids)
                ])
                for layer in valuation_layers:
                    self.env.cr.execute("""
                                UPDATE stock_valuation_layer
                                SET create_date = %s
                                WHERE id = %s
                            """, (picking.scheduled_date, layer.id))
            if picking.scheduled_date:
                quants = self.env['stock.quant'].search([
                    ('location_id', '=', picking.location_dest_id.id),
                    ('product_id', 'in', picking.move_ids_without_package.mapped('product_id').ids)
                ])
                for quant in quants:
                    self.env.cr.execute("""
                                UPDATE stock_quant
                                SET in_date = %s
                                WHERE id = %s
                            """, (picking.scheduled_date, quant.id))

        return res

class StockMove(models.Model):
    _inherit = 'stock.move'

    purchase_line_id = fields.Many2one(
        'purchase.order.line', 'Purchase Order Line',
        ondelete='set null', index='btree_not_null', readonly=False)

    def _create_quality_checks_for_mo(self):
        print("_create_quality_checks_for_mo ..........")
        mo_moves = defaultdict(lambda: self.env['stock.move'])
        check_vals_list = []
        seen = set()

        for move in self:
            if move.production_id and not move.scrapped:
                mo_moves[move.production_id] |= move

        # QC of product type
        for production, moves in mo_moves.items():
            quality_points = self._search_quality_points(moves.product_id, production.picking_type_id, 'product')

            quality_points_lot_type = self._search_quality_points(
                production.product_id, production.picking_type_id, 'move_line'
            )

            quality_points = quality_points | quality_points_lot_type
            if not quality_points:
                continue

            mo_check_vals_list = quality_points._get_checks_values(
                moves.product_id, production.company_id.id,
                existing_checks=production.sudo().check_ids
            )
            for check_value in mo_check_vals_list:
                check_value.update({'production_id': production.id})
            check_vals_list += mo_check_vals_list

        # QC of operation type
        for production, moves in mo_moves.items():
            quality_points_operation = self._search_quality_points(
                production.move_finished_ids.product_id, production.picking_type_id, 'operation'
            )
            for point in quality_points_operation:
                if point.check_execute_now():
                    key = (point.id, production.id, 0, 0, 'operation')
                    if key in seen:
                        continue
                    seen.add(key)
                    check_vals_list.append({
                        'point_id': point.id,
                        'team_id': point.team_id.id,
                        'measure_on': 'operation',
                        'production_id': production.id,
                    })

        #CUSTOM COMPONENT LOT QC 
        QP = self.env['quality.point'].sudo()
        for production, moves in mo_moves.items():
            print(f"Checking component lots for MO: {production.name}")

            # get 'Manufacturing' control points for lot/serial checks
            manu_points = QP.search([
                ('measure_on', '=', 'lots_serial_no'),
                ('picking_type_ids.name', '=', 'Manufacturing')
            ])
            print("manu_points ------>", manu_points)
            if not manu_points:
                continue

            # get raw material (component) moves
            component_moves = production.move_raw_ids.filtered(lambda m: not m.scrapped)
            print("component_moves --->", component_moves)
            for move in component_moves:
                lots = (move.mapped('move_line_ids.lot_id') | move.lot_ids)
                print("lots ------>", lots)
                if not lots:
                    continue

                for lot in lots:
                    print("lot --->", lot)
                    for point in manu_points:
                        print("point --->", point)
                        # skip unrelated points if restricted to certain products
                        if point.product_ids and move.product_id not in point.product_ids:
                            continue

                        key = (point.id, production.id, move.product_id.id, lot.id, 'lots_serial_no')
                        print("key ---->", key)
                        if key in seen:
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

        if check_vals_list:
            print("check_vals_list ---->", check_vals_list)
            self.env['quality.check'].sudo().create(check_vals_list)
            print(f"Created {len(check_vals_list)} quality checks (including lot/serial).")
        else:
            print("Created 0 quality checks (including lot/serial).")


# For Tracking the fleet vehicles during dispatches
class FleetVehicleTracking(models.Model):
    _name = 'fleet.vehicle.tracking'
    _description = 'Fleet Vehicle Tracking'
    _rec_name = 'dispatch_id'

    dispatch_id = fields.Many2one('stock.picking', string='Dispatch', required=True)
    longitude = fields.Float(string='Longitude', required=True, digits=(10, 7))
    latitude = fields.Float(string='Latitude', required=True, digits=(10, 8))
    timestamp = fields.Datetime(string='Timestamp', required=True)        

    def get_location_map(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.get_google_maps_url(self.latitude, self.longitude),
            'target': 'new'
        }

    def get_google_maps_url(self, latitude, longitude):
        return f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"
