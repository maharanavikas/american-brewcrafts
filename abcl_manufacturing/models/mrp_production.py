# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command, SUPERUSER_ID
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
    from_mps = fields.Boolean(string="From MPS", readonly=True)

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
    
    # def _get_move_raw_values(self, product, product_uom_qty, product_uom, operation_id=False, bom_line=False):
    #     data = super(MrpProduction, self)._get_move_raw_values(
    #         product, product_uom_qty, product_uom, operation_id, bom_line)
    #     data.update({
    #         'bom_uom_qty': data['product_uom_qty'],
    #         'deviation_percentage': 0,
    #     })
    #     return data

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

    @api.model_create_multi
    def create(self, vals_list):
        productions = super().create(vals_list)
        restrict_mo = self.env['ir.config_parameter'].sudo().get_param('mrp.restrict_manual_mo_creation', 'False') == 'True'
        for rec in productions:
            # if not rec._context.get('from_mps', False):
            # if not rec.from_mps:
            if restrict_mo and not rec.from_mps:
                bom_line_exists = self.env['mrp.bom.line'].search_count([('product_id', '=', rec.product_id.id)])
                bom_master_exists = self.env['mrp.bom'].search_count(
                    [('product_tmpl_id', '=', rec.product_id.product_tmpl_id.id)])

                if bom_line_exists or bom_master_exists:
                    raise ValidationError(_(
                        "You cannot manually create a Manufacturing Order for '%s' "
                        "because it is already used in a Bill of Materials."
                    ) % rec.product_id.display_name)
        return productions

    def copy(self, default=None):
        for record in self:
            if record.from_mps:
                raise ValidationError(_(
                    "You cannot duplicate the Manufacturing Order '%s' because it was created from MPS."
                ) % record.name)

        return super(MrpProduction, self).copy(default)

    def action_split(self):
        self._pre_action_split_merge_hook(split=True)
        if len(self) > 1:
            productions = [Command.create({'production_id': production.id}) for production in self]
            # Wizard need a real id to have buttons enable in the view
            wizard = self.env['mrp.production.split.multi'].create({'production_ids': productions})
            action = self.env['ir.actions.actions']._for_xml_id('mrp.action_mrp_production_split_multi')
            action['res_id'] = wizard.id
            action['context'] = {
                'default_from_mps': any(self.mapped('from_mps')),
            }
            return action
        else:
            action = self.env['ir.actions.actions']._for_xml_id('mrp.action_mrp_production_split')
            action['context'] = {
                'default_production_id': self.id,
            }
            return action

    def action_merge(self):
        self._pre_action_split_merge_hook(merge=True)
        products = set([(production.product_id, production.bom_id) for production in self])
        product_id, bom_id = products.pop()
        users = set([production.user_id for production in self])
        if len(users) == 1:
            user_id = users.pop()
        else:
            user_id = self.env.user

        origs = self._prepare_merge_orig_links()
        dests = {}
        for move in self.move_finished_ids:
            dests.setdefault(move.byproduct_id.id, []).extend(move.move_dest_ids.ids)
        from_mps_flag = any(self.mapped(lambda p: p._context.get('from_mps') or getattr(p, 'from_mps', False)))

        production = self.env['mrp.production'].with_context(default_picking_type_id=self.picking_type_id.id,from_mps=from_mps_flag).create({
            'product_id': product_id.id,
            'bom_id': bom_id.id,
            'picking_type_id': self.picking_type_id.id,
            'product_qty': sum(production.product_uom_qty for production in self),
            'product_uom_id': product_id.uom_id.id,
            'user_id': user_id.id,
            'origin': ",".join(sorted([production.name for production in self])),
            'from_mps': from_mps_flag,
        })

        for move in production.move_raw_ids:
            for field, vals in origs[move.bom_line_id.id].items():
                move[field] = vals

        for move in production.move_finished_ids:
            move.move_dest_ids = [Command.set(dests[move.byproduct_id.id])]

        self.move_dest_ids.created_production_id = production.id

        self.procurement_group_id.stock_move_ids.group_id = production.procurement_group_id

        if 'confirmed' in self.mapped('state'):
            production.move_raw_ids._adjust_procure_method()
            (production.move_raw_ids | production.move_finished_ids).write({'state': 'confirmed'})
            production.action_confirm()

        self.with_context(skip_activity=True)._action_cancel()
        # set the new deadline of origin moves (stock to pre prod)
        production.move_raw_ids.move_orig_ids.with_context(date_deadline_propagate_ids=set(production.move_raw_ids.ids)).write({'date_deadline': production.date_start})
        for p in self:
            p._message_log(body=_('This production has been merge in %s', production.display_name))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': production.id,
        }

    def _get_moves_raw_values(self):
        moves = []
        for production in self:
            if not production.bom_id:
                continue
            producing_factor = self._context.get('qty_producing_value', 0)
            factor = production.product_uom_id._compute_quantity(
                'qty_producing_value' in self._context and self._context['qty_producing_value'] or production.product_qty, production.bom_id.product_uom_id) / production.bom_id.product_qty
            _boms, lines = production.bom_id.explode(production.product_id, factor, picking_type=production.bom_id.picking_type_id, never_attribute_values=production.never_product_template_attribute_value_ids)
            for bom_line, line_data in lines:
                if bom_line.child_bom_id and bom_line.child_bom_id.type == 'phantom' or\
                        bom_line.product_id.type != 'consu':
                    continue
                operation = bom_line.operation_id.id or line_data['parent_line'] and line_data['parent_line'].operation_id.id
                moves.append(production.with_context(qty_should_consume=line_data['qty_should_consume'])._get_move_raw_values(
                    bom_line.product_id,
                    line_data['qty'],
                    bom_line.product_uom_id,
                    operation,
                    bom_line
                ))
        return moves


    def _get_move_raw_values(self, product, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        data = super(MrpProduction, self)._get_move_raw_values(
            product, product_uom_qty, product_uom, operation_id=operation_id, bom_line=bom_line
        )
        data.update({
            'bom_uom_qty': 'qty_should_consume' in self._context and self._context['qty_should_consume'] or product_uom_qty,
        })
        return data

    # def _link_bom(self, bom):
    #     """ Links the given BoM to the MO. Assigns BoM's lines, by-products and operations
    #     to the corresponding MO's components, by-products and workorders.
    #     """
    #     self.ensure_one()
    #     product_qty = self.product_qty
    #     uom = self.product_uom_id
    #     qty_should_consume = self._context.get('qty_should_consume', 0.0)
    #     print('qty_should_consume',qty_should_consume)
    #     moves_to_unlink = self.env['stock.move']
    #     workorders_to_unlink = self.env['mrp.workorder']
    #     # For draft MO, all the work will be done by compute methods.
    #     # For cancelled and done MO, we don't want to do anything more than assinging the BoM.
    #     if self.state == 'draft' and self.bom_id == bom:
    #         # Empties `bom_id` field so when the BoM is reassigns to this field, depending computes
    #         # will be triggered (doesn't happen if the field's value doesn't change).
    #         self.bom_id = False
    #     if self.state in ['cancel', 'done', 'draft']:
    #         if self.state == 'draft':
    #             # Don't straight delete the moves/workorders to avoid to cancel the MO, those will
    #             # be deleted once the BoM is assigned (and thus after new moves/WO were created).
    #             moves_to_unlink = self.move_raw_ids
    #             workorders_to_unlink = self.workorder_ids
    #         self.bom_id = bom
    #         moves_to_unlink.unlink()
    #         workorders_to_unlink.unlink()
    #         if self.state == 'draft':
    #             # we reset the product_qty/uom when the bom is changed on a draft MO
    #             # change them back to the original value
    #             self.write({'product_qty': product_qty, 'product_uom_id': uom.id,'qty_should_consume': qty_should_consume})
    #         return

