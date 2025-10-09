# -*- coding: utf-8 -*-

from odoo import  models, fields, api , _
from odoo.exceptions import ValidationError


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    status = fields.Selection(
        [('draft','Draft'),('to_approve','To Approve'),('approved','Approved'),('hold','Hold'),('reject','Rejected')], "Status", default='draft')
    user_id = fields.Many2one(
        'res.users', readonly=True, default=lambda self: self.env.user, string="Created by")
    approval_remark = fields.Text(string="Approval Remark", tracking=True)

    def action_to_approve(self):
        for pricelist in self:
            pricelist.status = 'to_approve'
            template = self.env.ref('abcl_sale.email_template_product_pricelist')
            sales_admin_group = self.env.ref('sales_team.group_sale_manager')
            if sales_admin_group and template:
                recipients = sales_admin_group.users.partner_id.ids
                template.send_mail(pricelist.id, email_values={'recipient_ids':  recipients})
    
    def action_approved(self):
        for pricelist in self:
            pricelist.status = 'approved'
            approved_mail_template = self.env.ref('abcl_sale.email_template_pricelist_approved')
            if approved_mail_template:
                approved_mail_template.with_context(action_user=self.env.user).send_mail(pricelist.id)

    def action_reject(self):
        return {
        'name': 'Enter Remark for Reject',
        'type': 'ir.actions.act_window',
        'res_model': 'pricelist.approval.remark.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {
            'default_pricelist_id': self.id,
            'default_status': 'reject',
        },
    }

    def action_hold(self):
        return {
        'name': 'Enter Remark for Hold',
        'type': 'ir.actions.act_window',
        'res_model': 'pricelist.approval.remark.wizard',
        'view_mode': 'form',
        'target': 'new',
        'context': {
            'default_pricelist_id': self.id,
            'default_status': 'hold',
        },
    }
