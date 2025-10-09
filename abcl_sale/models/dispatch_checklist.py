# -*- coding: utf-8 -*-

from odoo import  models, fields, api , _

class DispatchChecklist(models.Model):
    _name = "dispatch.checklist"
    _description = 'Dispatch Checklist'
    _rec_name = 'picking_id'

    customer_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    picking_id = fields.Many2one('stock.picking', required=True, ondelete='cascade')
    stock_move_id = fields.Many2one('stock.move', 'Delivery Address', check_company=True, index='btree_not_null')
    dispatch_date = fields.Char("Date Dispatched")
    deport = fields.Char("Deport")
    vehicle_type = fields.Char("Vehicle Type")
    dis_brand = fields.Many2one('sale.order.line', 'Dispatch Brand', readonly=True)
    dispatch_qty = fields.Float("Dispatch Quantity")
    state = fields.Selection([('draft', "Draft"), ('submitted', "Submitted")], string="State",
                                required=True, default='draft', tracking=True
                            )
    line_ids = fields.One2many('dispatch.checklist.line', 'checklist_id', string='Dispatch Checks')


class DispatchChecklistLine(models.Model):
    _name = "dispatch.checklist.line"
    _description = "Dispatch Checklist Line"
    _order = "checklist_id" 

    checklist_id = fields.Many2one('dispatch.checklist', required=True, ondelete="cascade")
    specifications = fields.Char('Specifications')
    label = fields.Char('Dispatch Parameters', required=True)
    remarks = fields.Char('Remarks')
    status = fields.Boolean('Status')
