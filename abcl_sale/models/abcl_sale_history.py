# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AbclSaleHistory(models.Model):
    _name = 'abcl.sale.history'
    _description = 'ABCL Sale History'
    _inherit = ['mail.thread.main.attachment', 'mail.activity.mixin']

    godown_id = fields.Many2one('abcl.sale.godown','Godown Name')
    vendor_id = fields.Many2one('res.partner','Supplier Name')
    licence_id = fields.Many2one('abcl.sale.licence','Licence Name')
    licence_no = fields.Char('Licence No.', related='licence_id.licence_no')
    state_id = fields.Many2one(comodel_name='res.country.state', string='State', domain="[('country_id.code', '=', 'IN')]")
    district = fields.Char('District')
    product_id = fields.Many2one('product.product', 'Label Name')
    pack_id = fields.Many2one('abcl.sale.pack', 'Pack Size')
    quantity = fields.Float('Sale Qty')


class ABCLSaleGoDown(models.Model):
    _name = 'abcl.sale.godown'
    _description = 'ABCL Sale Godown'

    name = fields.Char(string='Name')

class ABCLSaleLicence(models.Model):
    _name = 'abcl.sale.licence'
    _description = 'ABCL Sale Licence'

    name = fields.Char(string='Name')
    licence_no = fields.Char('Licence No.')


class ABCLSalePack(models.Model):
    _name = 'abcl.sale.pack'
    _description = 'ABCL Sale Pack'

    name = fields.Char(string='Name')




