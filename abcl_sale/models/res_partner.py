# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    allowed_products = fields.Many2many('product.product',string="Allowed Products",domain=[('sale_ok', '=', True)])
    sign_template_id = fields.Many2one('sign.template',string="Dispatch Check List")
    # contact_type = fields.Selection([('customer','Customer'),('vendor','Vendor')], string="Type")
    excise_approver_allias = fields.Char(String="Excise Approver")
    