from datetime import datetime
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError


class StockPickingSignRequestRole(models.TransientModel):
    _name = 'dispatch.checklist.wizard'
    _description = "Dispatch Checklist Wizard"

    partner_id = fields.Many2one('res.partner', string="Contact")
    mail_sent_order = fields.Integer(string='Sign Order', default=1)
    stock_picking_id = fields.Many2one('stock.picking', required=True, readonly=True)
    dispatch_user_id = fields.Many2one('res.users', string="Responsible (User)")
    accountant_user_id  = fields.Many2one('res.users', string="Accountant (User)")

    order_responsible = fields.Integer(string="Responsible Order", default=1)
    order_accountant  = fields.Integer(string="Accountant Order", default=2)
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted')],
                             string='State', tracking=True, default='draft')


    def send_sign_request(self):
        self.ensure_one()
        picking = self.stock_picking_id

        vals = {}
        if self.dispatch_user_id:
            vals['user_id'] = self.dispatch_user_id.id
        if self.accountant_user_id:
            vals['finance_user_id'] = self.accountant_user_id.id
        if vals:
            picking.write(vals)

        entries = []
        if self.dispatch_user_id and self.dispatch_user_id.partner_id and self.dispatch_user_id.partner_id.email:
            entries.append({
                'role_code': 'dispatch',
                'role_label': 'Responsible',
                'partner': self.dispatch_user_id.partner_id,
                'order': self.order_responsible or 0,
            })
        if self.accountant_user_id and self.accountant_user_id.partner_id and self.accountant_user_id.partner_id.email:
            entries.append({
                'role_code': 'accountant',
                'role_label': 'Accountant',
                'partner': self.accountant_user_id.partner_id,
                'order': self.order_accountant or 0,
            })
        if not entries:
            raise UserError(_("No recipients with an email address."))

        entries.sort(key=lambda e: (e['order'], e['role_code']))

        template = self.env.ref('abcl_sale.email_template_stock_picking_sign_request', raise_if_not_found=True)
        base_url = picking._get_dispatch_checklist_url()

        for idx, e in enumerate(entries, start=1):
            if e['role_code'] == 'dispatch':
                ctx = {
                    'recipient_name': e['partner'].name,
                    'dispatch_role_label': e['role_label'],
                    'dispatch_role_code': e['role_code'],
                    'dispatch_sign_order': idx,
                    'dispatch_checklist_url': f"{base_url}#{e['role_code']}",
                }
                email_values = {
                    'email_to': e['partner'].email,
                    'recipient_ids': [(6, 0, [e['partner'].id])],
                }
                template.with_context(ctx).send_mail(picking.id, email_values=email_values)
        
        if picking.is_dispatch_sent != True:
            picking.is_dispatch_sent = True

        return {'type': 'ir.actions.act_window_close'}
