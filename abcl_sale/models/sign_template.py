# -*- coding: utf-8 -*-
from odoo import models,fields, api, _

class SignTemplateSigner(models.Model):
    _name = "sign.template.signer"
    _description = 'Sign Template Signers'

    role_id = fields.Many2one('sign.item.role', required=True)
    partner_id = fields.Many2one('res.partner', string="Contact")
    mail_sent_order = fields.Integer(string='Sign Order', default=1)
    sign_template_id = fields.Many2one('sign.template', 'Sign Template', required=True, ondelete="cascade")


class SignTemplate(models.Model):
    _inherit = 'sign.template'

    set_sign_order = fields.Boolean("Set Sign Order")
    signer_ids = fields.One2many('sign.template.signer', 'sign_template_id', string="Signers",
                                 readonly=False, compute="_compute_signers", store=True, precompute=True)

    @api.depends('sign_item_ids','sign_item_ids.responsible_id')
    def _compute_signers(self):
        for template in self:
            sign_roles = template.sign_item_ids.responsible_id.sorted()
            existing_signers = template.signer_ids
            template.signer_ids = False
            template.signer_ids = [[0, 0, {
                "role_id": role.id,
                "partner_id": existing_signers[index].partner_id if (existing_signers and index <= len(existing_signers) -1) else False,
                "mail_sent_order": index + 1,
            }] for index,role in enumerate(sign_roles)]
