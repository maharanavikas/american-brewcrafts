# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class Company(models.Model):
    _inherit = 'res.company'

    recurring_po_agreement = fields.Boolean(string="Recurring PO Agreement")
    module_po_recurring = fields.Boolean("module po recurring")
