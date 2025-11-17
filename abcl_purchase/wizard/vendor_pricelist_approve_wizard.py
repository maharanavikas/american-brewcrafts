# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class VendorPricelistApprovalWizard(models.TransientModel):
    _name = 'vendor.pricelist.approval.wizard'
    _description = 'Vendor Pricelist Approval Wizard'

    comment = fields.Text(string="Comment", required=True)
    product_supplierinfo_id = fields.Many2one('product.supplierinfo', string="Supplier Info", required=True)
    action_type = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ], default='approve', string="Action Type")

    @api.constrains('comment')
    def _check_comment_not_empty_or_spaces(self):
        for record in self:
            if not record.comment or not record.comment.strip():
                raise ValidationError("The comment cannot be empty or contain only spaces.")

    def action_submit(self):
        self.ensure_one()
        self.product_supplierinfo_id.action_pricelist_approval(self.action_type, self.comment)
    