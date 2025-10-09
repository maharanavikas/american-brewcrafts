# -*-  coding: utf-8 -*-

from odoo import models, fields


class SaleQuotationApprovers(models.Model):
    _name = 'sale.quotation.approvers'
    _description = 'Sale Quotation Approver Setup'
    _rec_name = 'name'
    _order = 'sequence asc'

    name = fields.Char(string='Approval Name', required=True)
    sequence = fields.Integer(string='Sequence', default=1)
    user_id = fields.Many2one('res.users', string='Responsible User', required=True)

    _sql_constraints = [
        ('unique_sequence', 'unique(sequence)', 'The sequence must be unique per approver.')
    ]
