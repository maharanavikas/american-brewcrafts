# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError


class SupplierInfo(models.Model):
    _inherit = ['product.supplierinfo', 'mail.thread', 'mail.activity.mixin']
    _name = 'product.supplierinfo'

    min_qty = fields.Float('Quantity', default=1, required=True, digits="Product Unit of Measure",
    help="The quantity to purchase from this vendor to benefit from the price, expressed in the vendor Product Unit of Measure if not any, in the default unit of measure of the product otherwise.")
    minimum_order_qty = fields.Float('Minimum Order Quantity' )
    requested_price = fields.Float("Requested Price")
    requested_by = fields.Many2one('res.users', string="Requested By", default=lambda self: self.env.user)
    price = fields.Float('Price', default=0.0, digits='Product Price', required=True, help="The price to purchase a product", tracking=True )
    is_approval_requested = fields.Boolean(string="Approval Requested", default=False, tracking=True)
    active = fields.Boolean(string="Active", default=False, tracking=True,copy=False)
    is_new_request = fields.Boolean(string="New request", default=False, tracking=True)
    approver_comment = fields.Text(string="Approver Comment", tracking=True)

    def action_open_change_request_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Price Change Request',
            'res_model': 'supplier.price.change.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_supplierinfo_id': self.id},
        }

    def action_for_request(self):
        vp_group = self.env.ref("abcl_base.group_vice_president", raise_if_not_found=False)
        template = self.env.ref("abcl_purchase.abcl_vendor_pricelist_approval_mail_template", raise_if_not_found=False)

        if not vp_group or not vp_group.users:
            return

        vp_users = vp_group.users

        for rec in self:
            if rec.is_approval_requested:
                continue

            rec.is_approval_requested = True
            rec.is_new_request = True
            for user in vp_users:
                rec.activity_schedule(
                    'abcl_purchase.abcl_pricelist_approval_mail_act',
                    user_id=user.id,
                    note="Please review and approve the Vendor Pricelist",
                )

                if template:
                    template.with_context(approver_name=user.partner_id.name).send_mail(
                        rec.id,
                        force_send=True,
                        email_values={'recipient_ids': [(6, 0, vp_users.mapped('partner_id').ids)]}
                    )

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

    def action_approve_request(self):
        for rec in self:
            rec.activity_feedback(['abcl_purchase.abcl_pricelist_approval_mail_act'], feedback='Approved')

            template = self.env.ref('abcl_purchase.abcl_vendor_pricelist_result_mail_template')
            if template and rec.requested_by and rec.requested_by.partner_id:
                template.with_context(request_outcome='approved').send_mail(
                    rec.id,
                    force_send=True,
                    email_values={'email_to': rec.requested_by.partner_id.email}
                )
            if rec.requested_price:
                rec.price = rec.requested_price
                rec.requested_price = 0.0

            rec.is_approval_requested = False
            rec.is_new_request = False
            rec.active = True


    def action_reject_request(self):
        for rec in self:
            rec.activity_feedback(['abcl_purchase.abcl_pricelist_approval_mail_act'], feedback='Rejected')

            template = self.env.ref('abcl_purchase.abcl_vendor_pricelist_result_mail_template')
            if template and rec.requested_by and rec.requested_by.partner_id:
                template.with_context(request_outcome='rejected').send_mail(
                    rec.id,
                    force_send=True,
                    email_values={'email_to': rec.requested_by.partner_id.email}
                )
            rec.is_approval_requested = False
            rec.is_new_request = False
            rec.requested_price = 0.0

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
    