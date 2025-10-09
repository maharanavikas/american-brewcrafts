# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    # @api.constrains('invoice_line_ids')
    # def check_invoice_line_products(self):
    #     for move in self:
    #         if move.move_type == 'out_invoice':
    #             allowed_products = move.partner_id.allowed_products
    #             for line in move.invoice_line_ids:
    #                 if line.product_id not in allowed_products:
    #                     raise ValidationError(
    #                         f"The product '{line.product_id.name}' is not included in the list of approved products for the customer '{move.partner_id.name}'; hence, it cannot be billed to this customer")





