# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PricelistApprovalLog(models.Model):
    _name = 'purchase.pricelist.approval.log'
    _description = "Pricelist Approval Log"
    _order = "id desc"

    pricelist_id = fields.Many2one("product.supplierinfo", "Pricelist", required=True, ondelete="restrict")
    approver_id = fields.Many2one('res.users', string="Approved By")
    approved_on = fields.Datetime("Approved On")
    is_initial = fields.Boolean("Initial Request", help="This will be true when the pricelist will be created.")

    old_price = fields.Float(
        'Old Price', default=0.0, digits='Product Price', required=True)

    new_price = fields.Float(
        'New Price', default=0.0, digits='Product Price', required=True)
    
    req_remark = fields.Char("Requester Remark")
    approve_remark = fields.Char("Approver Remark")

    status = fields.Selection(
        [('applied', 'Applied'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        string="Status", required=True, default="applied"
    )


class SupplierInfo(models.Model):
    _inherit = ['product.supplierinfo', 'mail.thread', 'mail.activity.mixin']
    _name = 'product.supplierinfo'

    min_qty = fields.Float('Quantity', default=1, required=True, digits="Product Unit of Measure",
    help="The quantity to purchase from this vendor to benefit from the price, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")
    minimum_order_qty = fields.Float('Minimum Order Quantity' )

    price = fields.Float('Price', default=0.0, digits='Product Price', required=True, help="The price to purchase a product", tracking=True)
    active = fields.Boolean(string="Active", default=False, tracking=True, copy=False)
    
    is_approval_requested = fields.Boolean(string="Approval Requested", compute="_compute_is_approval_requested")
    approval_log_ids = fields.One2many('purchase.pricelist.approval.log', 'pricelist_id', string="Approval Logs")

    def _compute_is_approval_requested(self):
        for pl in self:
            pl.is_approval_requested = pl.approval_log_ids.filtered(
                lambda log: log.status == 'applied'
            )

    def open_vendor_pricelist_change_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Price Change Request',
            'res_model': 'supplier.price.change.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_supplierinfo_id': self.id},
        }
    
    def action_for_request(self):
        self.ensure_one()
        if self.active:
            return
        self.create_approval_log_and_notify(initial=True)
        
    def create_approval_log_and_notify(self, initial=False, new_price=0, remark=''):
        approval_log = self.env['purchase.pricelist.approval.log'].create({
            'pricelist_id': self.id,
            'is_initial': initial,
            'old_price': 0 if initial else self.price,
            'new_price': self.price if initial else new_price,
            'req_remark': 'Initial Pricelist Approval (System Generated)' if initial else remark,
        })
        self.schedule_activity_for_approval(approval_log)

    def schedule_activity_for_approval(self, approval_log):
        admin_user = self.env.ref('base.user_admin')
        vp_users = self.env.ref("abcl_base.group_vice_president").users - admin_user
        template = self.env.ref("abcl_purchase.abcl_vendor_pricelist_approval_mail_template")

        if not vp_users:
            raise ValidationError(_('No Users configured in Vice President Approval.Please contact administrator.'))

        for user in vp_users:
            self.activity_schedule(
                'abcl_purchase.abcl_pricelist_approval_mail_act',
                user_id=user.id,
                note="Please review and approve the Vendor Pricelist",
            )

            template.with_context(approver_name=user.partner_id.name).send_mail(
                self.id, email_values={'recipient_ids': [(6, 0, vp_users.partner_id.ids)]})

    def action_approve_wizard(self):
        self.ensure_one()
        return {
            'name': 'Vendor Pricelist Approval',
            'type': 'ir.actions.act_window',
            'res_model': 'vendor.pricelist.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_supplierinfo_id': self.id,
                'default_action_type': 'approve'
            }
        }

    def action_reject_wizard(self):
        self.ensure_one()
        return {
            'name': 'Vendor Pricelist Approval',
            'type': 'ir.actions.act_window',
            'res_model': 'vendor.pricelist.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_supplierinfo_id': self.id,
                'default_action_type': 'reject'
            }
        }

    def action_pricelist_approval(self, action_type, remark):
        template = self.env.ref('abcl_purchase.abcl_vendor_pricelist_result_mail_template')
        feedback = action_type == 'approve' and 'Approved' or 'Rejected'
        status = 'approved' if action_type == 'approve' else 'rejected'
        for rec in self:
            approval_log = rec.approval_log_ids.filtered(lambda r: r.status == 'applied')
            if approval_log:
                template.with_context(action_type=action_type, approval_log=approval_log).send_mail(
                    rec.id, email_values={'email_to': approval_log.create_uid.partner_id.email}
                )
                approval_log.write({
                    'status' : status,
                    'approve_remark': remark,
                })
                if approval_log.is_initial:
                    rec.active = True
                elif action_type == 'approve':
                    rec.price = approval_log.new_price
                
                rec.activity_feedback(['abcl_purchase.abcl_pricelist_approval_mail_act'], feedback=feedback)

    @api.constrains('min_qty')
    def _check_min_qty(self):
        for record in self:
            if record.min_qty != 1:
                raise UserError("Minimum quantity must always be 1 and cannot be changed.")

    @api.constrains('product_id', 'partner_id')
    def _check_duplicate_vendor_line(self):
        for pl in self:
            duplicate_pl = self.search([
                ('product_id', '=', pl.product_id and pl.product_id.id or False),
                ('product_tmpl_id', '=', pl.product_tmpl_id and pl.product_tmpl_id.id or False),
                ('partner_id', '=', pl.partner_id.id),
            ])-pl
            if duplicate_pl:
                raise ValidationError(_(f"Vendor line already exists for product:{duplicate_pl[0].product_id.name} and vendor: {pl.partner_id.name}."))

    @api.constrains('minimum_order_qty')
    def _check_minimum_order_qty(self):
        for rec in self:
            if rec.minimum_order_qty < 0:
                raise ValidationError(_("Minimum Order Quantity cannot be less than zero."))

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        for rec in self:
            if rec.product_tmpl_id:
                variants = rec.product_tmpl_id.product_variant_ids
                if len(variants) == 1:
                    rec.product_id = variants.id
                else:
                    rec.product_id = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id and not rec.product_tmpl_id:
                rec.product_tmpl_id = rec.product_id.product_tmpl_id
    