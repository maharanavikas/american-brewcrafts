# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    survey_no = fields.Char("Survey No.")
    village = fields.Char("Village")
    mandal = fields.Char("Mandal")
    cin_no = fields.Char("CIN No.")
    cst_no = fields.Char("CST No.")
    excise_regn_no = fields.Char("Excise Regn No.")

