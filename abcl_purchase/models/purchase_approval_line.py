#  -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseApprovalLine(models.Model):
    _name = 'purchase.approval.line'
    _description = 'Purchase Approval Line'
    _order = 'sequence asc'

    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", required=True, ondelete='cascade')
    approver_id = fields.Many2one('res.users', string="Approver", required=True)
    approval_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="Status", default='pending')
    comment = fields.Text(string="Comment", tracking=True)
    sequence = fields.Integer(string="Sequence", default=1)


