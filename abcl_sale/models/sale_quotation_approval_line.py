# -*- coding: utf-8 -*-

from odoo import models, fields


class SaleQuotationApprovalLine(models.Model):
    _name = 'sale.quotation.approval.line'
    _description = 'Sale Quotation Approval Line'
    _order = 'sequence asc'

    order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='cascade')
    sequence = fields.Integer(string='Sequence')
    user_id = fields.Many2one('res.users', string='Approvers')
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('pending', 'To Approve'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending', string='Status')
    comment = fields.Text(string="Comment")
