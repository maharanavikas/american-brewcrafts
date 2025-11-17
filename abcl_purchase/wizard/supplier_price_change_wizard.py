# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class SupplierPriceChangeWizard(models.TransientModel):
    _name = "supplier.price.change.wizard"
    _description = "Supplier Price Change Request"

    supplierinfo_id = fields.Many2one("product.supplierinfo", string="Supplier Info", required=True)
    new_price = fields.Float("New Price", required=True)
    product_tmpl_id = fields.Many2one(related="supplierinfo_id.product_tmpl_id", string="Product", readonly=True)
    current_price = fields.Float(related="supplierinfo_id.price", string="Current Price", readonly=True)
    remark = fields.Char("Remark", required=True)

    def action_submit_request(self):
        self.ensure_one()
        self.supplierinfo_id.create_approval_log_and_notify(new_price=self.new_price, remark=self.remark)
    
    @api.constrains('new_price')
    def _check_new_price(self):
        for rec in self:
            if rec.new_price <= 0:
                raise ValidationError("New Price must be greater than 0.")
            if rec.new_price == rec.supplierinfo_id.price:
                raise ValidationError(_("New Price must be different from the current price."))
    