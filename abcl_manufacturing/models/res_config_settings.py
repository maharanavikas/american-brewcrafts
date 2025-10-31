# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_manual_mo_creation = fields.Boolean(
        string="Restrict Manual Manufacturing Orders",
        config_parameter='mrp.restrict_manual_mo_creation',
        help="Restricts manual Manufacturing Orders for BOM products; allows creation only via MPS.."
    )
    restrict_manual_po_creation = fields.Boolean(
        string="Restrict Manual Purchase Orders",
        config_parameter='purchase.restrict_manual_po_creation',
        help="Restricts manual Purchase Orders for BOM products; allows creation only via MPS."
    )

