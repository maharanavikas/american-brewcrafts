from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError


class SupplierPriceChangeWizard(models.TransientModel):
    _name = "supplier.price.change.wizard"
    _description = "Supplier Price Change Request"

    supplierinfo_id = fields.Many2one("product.supplierinfo", string="Supplier Info", required=True)
    new_price = fields.Float("New Price", required=True)
    product_tmpl_id = fields.Many2one(related="supplierinfo_id.product_tmpl_id", string="Product", readonly=True)
    current_price = fields.Float(related="supplierinfo_id.price", string="Current Price", readonly=True)

    # def action_submit_request(self):
    #     supplierinfo = self.supplierinfo_id
    #     print("supplierinfo",supplierinfo)
    #     supplierinfo.write({
    #         "requested_price": self.new_price,
    #         # "approval_status": "requested",
    #         "is_approval_requested": True,
    #         "requested_by": self.env.user.id,
    #     })
    #
    #     vp_group = self.env.ref("abcl_base.group_vice_president")
    #     vp_users = vp_group.users
    #
    #     for user in vp_users:
    #         supplierinfo.activity_schedule(
    #             'abcl_purchase.abcl_pricelist_approval_mail_act',
    #             user_id=user.id,
    #             note=f'Please review and approve the Vendor Pricelist'
    #         )
    #
    #     template = self.env.ref("abcl_purchase.abcl_vendor_pricelist_approval_mail_template")
    #     if template:
    #         template.send_mail(
    #             supplierinfo.id,
    #             force_send=True,
    #             email_values={'recipient_ids': [(6, 0, vp_users.mapped('partner_id').ids)]}
    #         )
    def action_submit_request(self):
        supplierinfo = self.supplierinfo_id
        supplierinfo.write({
            "requested_price": self.new_price,
            "is_approval_requested": True,
            "is_new_request": False,
            "requested_by": self.env.user.id,
        })

        vp_group = self.env.ref("abcl_base.group_vice_president", raise_if_not_found=False)
        template = self.env.ref("abcl_purchase.abcl_vendor_pricelist_approval_mail_template", raise_if_not_found=False)

        if not vp_group or not vp_group.users or not template:
            return

        vp_users = vp_group.users

        for user in vp_users:
            supplierinfo.activity_schedule(
                'abcl_purchase.abcl_pricelist_approval_mail_act',
                user_id=user.id,
                note='Please review and approve the Vendor Pricelist'
            )

            template.with_context(approver_name=user.partner_id.name).send_mail(
                supplierinfo.id,
                force_send=True,
                email_values={
                    'email_to': user.partner_id.email,
                    'recipient_ids': [(6, 0, [user.partner_id.id])]
                }
            )

    @api.constrains('new_price')
    def _check_new_price(self):
        for rec in self:
            if rec.new_price <= 0:
                raise ValidationError("New Price must be greater than 0.")
            if rec.supplierinfo_id and rec.new_price == rec.supplierinfo_id.price:
                raise ValidationError("New Price must be different from the current price.")