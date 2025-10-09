# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class PurchaseCloseReasonWizard(models.TransientModel):
    _name = 'purchase.close.reason.wizard'
    _description = 'Purchase Close Reason Wizard'

    purchase_id = fields.Many2one('purchase.order', String="Purchase Order")
    close_reason_id = fields.Many2one('purchase.close.reason', string="Reason to Close", required=True)

    def action_confirm_close(self):
        self.purchase_id.write({
            'state': 'close',
            'close_reason_id': self.close_reason_id.id,
            'closed_date': datetime.now(),
        })
        return {'type': 'ir.actions.act_window_close'}
