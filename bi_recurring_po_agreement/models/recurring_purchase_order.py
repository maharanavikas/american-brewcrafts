# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import date, timedelta
import calendar
import datetime
from dateutil.relativedelta import relativedelta
from markupsafe import Markup

class RecurringPurchaseOrder(models.Model):
    _name = "recurring.purchase.order"
    _description = "Recurring Purchase Order Agreement"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", required=True)
    order_id = fields.Many2one("purchase.order",string="Purchase Order", required=True)
    partner_id = fields.Many2one(related="order_id.partner_id")
    notify_id = fields.Many2one("res.users",string="Get Notification", required=True)
    execute_every = fields.Integer(string="Execute After", default=1, required=True)
    repeat_after = fields.Selection([("days","Day"),
                                    ("weeks","Week"),
                                    ("months","Month"),],string="Repeat at Every", required=True)
    start_date = fields.Date("Start Date", required=True)
    stop_date = fields.Date("Stop Date", required=True)
    recurring_purchase_order_line_ids = fields.One2many('recurring.purchase.order.line', 'recurring_order_id', string='Order Lines')
    state = fields.Selection([('new', 'New'),
                              ('process', 'Process')],
                             string='State', default="new", readonly=True, index=True, copy=False, tracking=True)
    cron_id = fields.Many2one('ir.cron', 'Cron Ref')
   
    @api.onchange('order_id')
    def onchange_order_id(self):
        if self.order_id:
            self.recurring_purchase_order_line_ids = [(5, 0, 0)]
            order_lines = []
            for line in self.order_id.order_line:
                order_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_qty':line.product_qty,
                    'product_uom_quantity' : line.product_uom_qty,
                    'price_unit': line.price_unit,
                    'product_uom' : line.product_id.uom_id.id
                }))
            self.recurring_purchase_order_line_ids = order_lines
            self.partner_id = self.order_id.partner_id.id

    def send_mail_values(self, recurring = ''):
        order_lines= []
        recurring_id = self.browse(recurring)
        cron_id = recurring_id.cron_id
        if recurring_id.stop_date <= date.today() :
            cron_id.update({'active': False})
        if recurring_id.stop_date >= date.today():
            for recurring_line in recurring_id.recurring_purchase_order_line_ids:
                order_lines.append((0, 0, {
                    'product_id': recurring_line.product_id.id,                                   
                    'product_qty':recurring_line.product_qty,
                    'product_uom_qty': recurring_line.product_uom_quantity,
                    'price_unit': recurring_line.price_unit,
                }))
            new_order_id = recurring_id.order_id.copy({ 'order_line': order_lines, 'po_name': recurring_id.name})
            template = self.env.ref('bi_recurring_po_agreement.recurring_purchase_order_email_template', raise_if_not_found=False)
            if template:
                email_values = {'email_from':self.env.user.email,
                                'email_to':  recurring_id.notify_id.email}
                
                template.with_context(data = new_order_id).send_mail(recurring_id.id, email_values=email_values)
                recurring_id.message_post(body=Markup(template.body_html))



    def button_new(self):
        self.state ='new'

    def button_process(self):
        self.state = 'process'
        date_today = fields.Date.today()
        if self.repeat_after == 'days':
            end_date = date_today + datetime.timedelta(days=self.execute_every)
        if self.repeat_after == 'weeks':
            repeat_after_days = 7
            end_date = date_today + datetime.timedelta(days=repeat_after_days)

        if self.repeat_after == 'months':
            time = date_today + relativedelta(months=1)
            end_date = time
       
        cron = self.env['ir.cron']
        order_model = self.env.ref('bi_recurring_po_agreement.model_recurring_purchase_order').id
        vals = {
            'name': 'Recurring Purchase Order Agreement',
            'model_id': order_model,
            'interval_number': self.execute_every,
            'interval_type': self.repeat_after,
            'nextcall': end_date,
            'priority': 11,
            'user_id': self.env.user.id,
            'state': 'code',
            'code': 'model.send_mail_values('+str(self.id)+')',
            'active': True
        }

        if end_date == date.today():
            vals['active'] = False
        ir_cron = cron.create(vals)
        if ir_cron:
            self.update({'cron_id': ir_cron.id})