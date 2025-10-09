# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	group_is_recurring_po = fields.Boolean(string="Recurring PO Agreement", implied_group='bi_recurring_po_agreement.group_is_recurring_po',default=False)
	module_po_recurring = fields.Boolean("module po recurring",related="company_id.module_po_recurring",readonly=False)