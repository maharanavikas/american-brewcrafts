# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    tag_ids = fields.Many2many('mrp.workcenter.tag', string="Category")
    current_running_qty = fields.Float(
        string="Current Running Qty",
        compute="_compute_running_and_remaining_qty",
        store=False
    )

    capacity_remaining = fields.Float(
        string="Capacity Remaining",
        compute="_compute_running_and_remaining_qty",
        store=False
    )

    @api.depends('default_capacity')
    def _compute_running_and_remaining_qty(self):
        for record in self:
            # Fetch all workorders currently in progress for this workcenter
            running_wos = self.env['mrp.workorder'].search([
                ('workcenter_id', '=', record.id),
                ('qty_producing', '>', 0),
                ('state', '=', 'progress'),
            ])

            # Sum of qty_producing of all running workorders
            current_qty = sum(running_wos.mapped('qty_producing'))
            record.current_running_qty = current_qty

            # Remaining capacity: workcenter capacity - running qty
            record.capacity_remaining = record.default_capacity - current_qty
