# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError

class StockPickingSignRequest(models.TransientModel):
    _name = 'stock.picking.sign.request.wizard'
    _description = "Stock Picking Sign Request"

    stock_picking_id = fields.Many2one("stock.picking", "Stock", required=True, ondelete="cascade")
    dispatch_checklist_id = fields.Many2one('sign.template', string="Dispatch Check List",related='stock_picking_id.dispatch_checklist_id')
    set_sign_order = fields.Boolean(string="Set Sign Order", related='dispatch_checklist_id.set_sign_order', readonly=False)
    signer_request_ids = fields.One2many('stock.picking.sign.request.role.wizard', 'wizard_id', string="Signers Wizard")

    def send_sign_request(self):
        self.ensure_one()
        picking = self.stock_picking_id
        template = self.dispatch_checklist_id

        if not picking.sale_id:
            raise ValidationError(_("No Sale Order is linked to this record."))

        roles_without_partner = self.signer_request_ids.filtered(lambda l: not l.partner_id)
        if roles_without_partner:
            raise ValidationError(_("Please Assign signers to the following roles: %s") %
                                  ", ".join(roles_without_partner.mapped('role_id.name')))
        signer_data = [
            (0, 0, {
                'role_id': line.role_id.id,
                'partner_id': line.partner_id.id,
                'mail_sent_order': line.mail_sent_order,
            }) for line in self.signer_request_ids
        ]

        send_request = self.env['sign.send.request'].with_user(picking.user_id.id).with_context(
            default_template_id=template.id
        ).create({
            'set_sign_order': template.set_sign_order,
            'signer_ids': signer_data,
        })

        sign_request = send_request.with_context(sign_directly_without_mail=False).create_request()
        if sign_request:
            picking.sign_request_id = sign_request.id


class StockPickingSignRequestRole(models.TransientModel):
    _name = 'stock.picking.sign.request.role.wizard'
    _description = "Stock Picking Sign Request Role Wizard"

    wizard_id = fields.Many2one('stock.picking.sign.request.wizard', required=True, ondelete='cascade')
    role_id = fields.Many2one('sign.item.role', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string="Contact")
    mail_sent_order = fields.Integer(string='Sign Order', default=1)
