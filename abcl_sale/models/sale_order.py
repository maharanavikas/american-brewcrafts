# -*- coding: utf-8 -*-

import uuid
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    dispatch_checklist_id = fields.Many2one(
        'sign.template', "Dispatch Check List", related='partner_id.sign_template_id', copy=False)
    dispatch_checklist_id_warning = fields.Json(
        string="Dispatch Checklist Warning", compute="_compute_dispatch_checklist_id_warning")
    evc_doc = fields.Binary("EVC Document", attachment=True, copy=False, exportable=False)
    evc_doc_name = fields.Char("EVC Doc Name")
    # import_permit_doc = fields.Binary("Import Permit", attachment=True, copy=False, exportable=False)
    # import_permit_doc_name = fields.Char("Import Permit Doc Name")
    # export_permit_doc = fields.Binary("Export Permit", attachment=True, copy=False, exportable=False)
    # export_permit_doc_name = fields.Char("Export Permit Doc Name")

    # import_permit_no = fields.Char("Import Permit No.")
    # import_permit_date = fields.Date("Import Permit Date")
    # export_permit_no = fields.Char("Export Permit Application No.")
    # export_permit_date = fields.Date("Export Permit Application Date")
    excise_leaf_no = fields.Char("Excise Leaf No.")
    transporter = fields.Char("Transporter")
    vehicle_no = fields.Char("Vehicle No.")
    transport_permit_no = fields.Char("Transport Permit No.")
    lr_gc_lwb_no = fields.Char("LR/GC/LWB No.")
    lr_gc_lwb_date = fields.Date("LR/GC/LWB Date")
    po_no = fields.Char("PO No.")
    po_date = fields.Date("PO Date")
    lr_no = fields.Char("LR No.")

    approval_line_ids = fields.One2many('sale.quotation.approval.line', 'order_id', string='Approval Lines')
    user_is_approver = fields.Boolean("User is Approver ?", compute="_compute_approval_for_current_user")
    # approval_status = fields.Selection([
    #     ('pending', 'Pending Approval'),
    #     ('approved', 'Approved'),
    #     ('rejected', 'Rejected')], string="Approval Status",
    #     compute="_compute_approval_status",
    #     store=True, readonly=False
    # )
    # import_permit_status = fields.Selection([
    #     ('applied', 'Applied'),
    #     ('in_progress', 'In Progress'),
    #     ('rejected', 'Rejected'),
    #     ('received', 'Received'),
    # ], string="Import Permit Status")
    # export_permit_status = fields.Selection([
    #     ('applied', 'Applied'),
    #     ('in_progress', 'In Progress'),
    #     ('rejected', 'Rejected'),
    #     ('received', 'Received'),], string="Export Permit Status")
    # import_status_display = fields.Char(string="Import Permit Status", compute='_compute_import_status_display')
    # export_status_display = fields.Char(string="Export Permit Status", compute='_compute_import_status_display')
    allowed_template_ids = fields.Many2many('product.template', compute='_compute_allowed_template_ids', store=False)
    import_permit_lines = fields.One2many('import.permit', inverse_name='order_id', string="Import Permit", copy=False,
                                          auto_join=True)
    export_permit_lines = fields.One2many('export.permit', inverse_name='order_id', string="Export Permit", copy=False,
                                          auto_join=True)
    all_approvals_done = fields.Boolean(string="All Approvals Done", compute="_compute_all_approvals_done", store=False,
                                        copy=False)
    can_resend_approval = fields.Boolean(
        compute="_compute_can_resend_approval", store=False
    )
    latest_approval_state = fields.Selection(
        selection=[('waiting', 'Waiting'),
                   ('pending', 'To Approve'),
                   ('approved', 'Approved'),
                   ('rejected', 'Rejected')],
        compute="_compute_latest_approval_state",
        store=False
    )
    sent_for_approval = fields.Boolean("Sent for Approval", default=False)
    move_line_count = fields.Integer(string="Stock Move Lines", compute="_compute_move_line_count")

    @api.depends("approval_line_ids.state", "approval_line_ids.sequence")
    def _compute_latest_approval_state(self):
        for order in self:
            latest_line = order.approval_line_ids.sorted(lambda l: l.sequence, reverse=True)[:1]
            order.latest_approval_state = latest_line.state if latest_line else False

    @api.depends("approval_line_ids.state")
    def _compute_can_resend_approval(self):
        for po in self:
            po.can_resend_approval = False
            if po.approval_line_ids:
                latest_line = po.approval_line_ids.sorted(key=lambda l: l.create_date)[-1]
                if latest_line.state == "rejected":
                    po.can_resend_approval = True

    @api.depends('approval_line_ids.state')
    def _compute_all_approvals_done(self):
        for order in self:
            order.all_approvals_done = all(line.state == 'approved' for line in order.approval_line_ids)

    @api.depends('partner_id')
    def _compute_allowed_template_ids(self):
        for order in self:
            order.allowed_template_ids = order.partner_id.allowed_products.mapped('product_tmpl_id')

    @api.onchange('partner_id', 'order_line')
    def _onchange_partner_or_lines(self):
        for order in self:
            if order.partner_id and order.partner_id.allowed_products:
                allowed_variants = order.partner_id.allowed_products
                disallowed_lines = order.order_line.filtered(lambda l: l.product_id not in allowed_variants)
                if disallowed_lines:
                    order.order_line -= disallowed_lines

    # def _compute_import_status_display(self):
    #     for order in self:
    #         order.import_status_display = order.import_permit_status.capitalize() if order.import_permit_status else 'N/A'
    #         order.export_status_display = order.export_permit_status.capitalize() if order.export_permit_status else 'N/A'

    # def open_import_permit_status_wizard(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Update Import Permit Status',
    #         'view_mode': 'form',
    #         'res_model': 'permit.status.wizard',
    #         'target': 'new',
    #         'context': {
    #             'default_sale_id': self.id,
    #             'default_import_permit_status': self.import_permit_status,
    #             'default_import_permit_no': self.import_permit_no,
    #             'default_import_permit_date': self.import_permit_date,
    #             'default_permit_type': 'import'
    #         }
    #     }
    # def open_export_permit_status_wizard(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Update Export Permit Status',
    #         'view_mode': 'form',
    #         'res_model': 'permit.status.wizard',
    #         'target': 'new',
    #         'context': {
    #             'default_sale_id': self.id,
    #             'default_export_permit_no': self.export_permit_no,
    #             'default_export_permit_date': self.export_permit_date,
    #             'default_export_permit_status': self.export_permit_status,
    #             'default_permit_type': 'export'
    #         }
    #     }

    # _sql_constraints = [
    #     ("export_permit_number_code_unique", "unique(export_permit_number)", "Export code must be unique")]

    @api.constrains("order_line")
    def check_order_line_products(self):
        for order in self:
            allowed_products = order.partner_id.allowed_products
            for line in order.order_line:
                if line.product_id not in allowed_products:
                    raise ValidationError(
                        f"The product '{line.product_id.name}' is not included in the list of approved products for the customer '{order.partner_id.name}'; hence, it cannot be sold to this customer")

    # @api.depends('partner_id')
    # def _compute_dispatch_checklist_id(self):
    #     for record in self:
    #         record.dispatch_checklist_id = record.partner_id.sign_template_id

    def _compute_dispatch_checklist_id_warning(self):
        warnings = {}
        for record in self:
            if not record.dispatch_checklist_id:
                message = _(f"No Dispatch Checklist is set for this Customer  '{record.partner_id.display_name}'")
                warnings['warning_message'] = {
                    'message': message,
                    'action_text': _("View Customer"),
                    'action': {
                        'type': 'ir.actions.act_window',
                        'name': _('Cutomer Form'),
                        'res_model': 'res.partner',
                        'res_id': self.partner_id.id,
                        'view_mode': 'form',
                        'target': 'current',
                    }
                }
            record.dispatch_checklist_id_warning = warnings



    # def _prepare_invoice(self):
    #     invoice_vals = super()._prepare_invoice()
    #     invoice_vals.update({
    #         'vehicle_no': self.vehicle_no,
    #         'transporter': self.transporter,
    #         # 'import_permit_no': self.import_permit_no,
    #         # 'import_permit_date': self.import_permit_date,
    #         # 'export_permit_no': self.export_permit_no,
    #         # 'export_permit_date': self.export_permit_date,
    #         'excise_leaf_no': self.excise_leaf_no,
    #         'transport_permit_no': self.transport_permit_no,
    #         'lr_gc_lwb_no': self.lr_gc_lwb_no,
    #         'lr_gc_lwb_date': self.lr_gc_lwb_date,
    #         'po_no': self.po_no,
    #         'po_date': self.po_date,
    #         'lr_no': self.lr_no
    #     })
    #     return invoice_vals

    # To get the total number of quantity of all products
    # def total_goods(self):
    #     all_goods_lines = self.env['sale.order.line'].search([('product_id.type', '=', 'consu')])
    #     total_goods_qty = sum(product.qty_delivered for product in all_goods_lines)
    #     return total_goods_qty

    # Excise report
    # def action_excise_report(self):
    #     return self.env.ref('abcl_sale.action_excise_report_sale_order').report_action(self)

    ##Approval Methods

    @api.depends('approval_line_ids.state', 'approval_line_ids.user_id')
    def _compute_approval_for_current_user(self):
        current_user = self.env.user
        for order in self:
            order.user_is_approver = order.approval_line_ids.filtered(
                lambda r: r.user_id == current_user and r.state == 'pending')

    # def action_send_for_approval(self):
    #     self.ensure_one()
    #
    #     approvers = self.env['sale.quotation.approvers'].search([], order='sequence asc')
    #     if not approvers:
    #         raise ValidationError("There is no approver configured for SO approval. Please reach out Administrator.")
    #
    #     # approval_lines = [[5,0,0]]
    #     approval_lines = []
    #     for index, record in enumerate(approvers, start=1):
    #         approval_lines.append([0, 0, {
    #             'sequence': index,
    #             'user_id': record.user_id.id,
    #             'state': 'pending' if index == 1 else 'waiting'
    #         }])
    #
    #     self.approval_line_ids = approval_lines
    #     first_approver = approvers[0]
    #     user = first_approver.user_id
    #
    #     self.activity_schedule(
    #         'abcl_sale.abcl_sale_mail_act_sale_quotation_approval',
    #         user_id=user.id,
    #         note='Please review and approve the Sale Quotation Order: %s' % self.name
    #     )
    #
    #     template = self.env.ref('abcl_sale.abcl_sale_order_approval_mail_template')
    #     template.send_mail(self.id, email_values={'email_to': user.email})

    def action_send_for_approval(self):
        self.ensure_one()
        self.sent_for_approval = True

        approvers = self.env['sale.quotation.approvers'].sudo().search([], order='sequence asc')
        if not approvers:
            raise ValidationError("There is no approver configured for SO approval. Please reach out Administrator.")

        # find last sequence number
        last_sequence = max(self.approval_line_ids.mapped('sequence') or [0])

        approval_lines = []
        for index, record in enumerate(approvers, start=last_sequence + 1):
            approval_lines.append((0, 0, {
                'sequence': index,
                'user_id': record.user_id.id,
                'state': 'pending' if index == last_sequence + 1 else 'waiting'
            }))
        self.approval_line_ids = [(4, line.id, 0) for line in self.approval_line_ids] + approval_lines

        # notify first approver (newly added)
        first_approver = approvers[0].user_id
        self.activity_schedule(
            'abcl_sale.abcl_sale_mail_act_sale_quotation_approval',
            user_id=first_approver.id,
            note=f'Please review and approve the Sale Quotation Order: {self.name}'
        )
        template = self.env.ref('abcl_sale.abcl_sale_order_approval_mail_template')
        template.send_mail(self.id, email_values={'email_to': first_approver.email})

    def action_open_approval_wizard(self):
        self.ensure_one()
        return {
            'name': 'Approve Sale Quotation',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.quotation.approval.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_id': self.id,
                'default_action_type': 'approve'
            }
        }

    def action_open_reject_form(self):
        self.ensure_one()
        return {
            'name': 'Reject Sale Quotation',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.quotation.approval.line.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_id': self.id,
                'default_action_type': 'reject',
            }
        }

    # @api.depends('approval_line_ids', 'approval_line_ids.state')
    # def _compute_approval_status(self):
    #     for po in self:
    #         if not po.approval_line_ids:
    #             po.approval_status = 'pending'
    #         elif any([line.state == 'rejected' for line in po.approval_line_ids]):
    #             po.approval_status = 'rejected'
    #         elif all(line.state == 'approved' for line in po.approval_line_ids):
    #             po.approval_status = 'approved'
    #         else:
    #             po.approval_status = 'pending'

    @api.onchange('partner_invoice_id', 'partner_shipping_id')
    def _onchange_partner_invoive_shipping(self):
        for order in self:
            if order.partner_shipping_id:
                order.partner_invoice_id = order.partner_shipping_id
            elif order.partner_invoice_id:
                order.partner_shipping_id = order.partner_invoice_id

    # def action_bulk_approve(self):
    #     for order in self:
    #         if order.user_is_approver:
    #             user = self.env.user
    #             approval_lines = order.approval_line_ids.filtered(lambda l: l.user_id == user and l.state == 'pending')
    #             approval_lines.write({'state': 'approved', 'comment': 'Bulk approved by approver'})
    #             self.activity_feedback( ['abcl_sale.abcl_sale_mail_act_sale_quotation_approval'],feedback='Approved.')
    #             mail_template = self.env.ref('abcl_sale.abcl_sale_order_approved_mail_template')
    #             if mail_template:
    #                 mail_template.send_mail(order.id, email_values={'email_to': order.user_id.email})
    #         else:
    #             raise ValidationError("You are not authorized to approve this order.")

    def action_bulk_approve(self):
        return {
            'name': 'Sale Order Bulk Approval',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.bulk.approval',
            'view_mode': 'form',
            'target': 'new',
        }
    
    def get_bulk_approve(self, remark):
        user = self.env.user
        invalid_sale_orders = self.filtered(lambda o: not o.user_is_approver)
        if invalid_sale_orders:
            names = ', '.join(invalid_sale_orders.mapped('name'))
            raise ValidationError(f"You are not authorized to approve the following orders: {names}")
        all_approval_lines = self.approval_line_ids.filtered(lambda l: l.user_id == user and l.state == 'pending')
        all_approval_lines.write({'state': 'approved', 'comment': remark})
        self.activity_feedback(['abcl_sale.abcl_sale_mail_act_sale_quotation_approval'], feedback='Approved.')
        mail_template = self.env.ref('abcl_sale.abcl_sale_order_approved_mail_template')
    
        if mail_template:
            mail_template.send_mail(self.id, email_values={'email_to': self.user_id.email})
        else:
            raise ValidationError("You are not authorized to approve this order.")

    def _compute_move_line_count(self):
        for order in self:
            order.move_line_count = self.env['stock.move.line'].search_count([
                ('picking_id', 'in', order.picking_ids.ids)
            ])

    def action_view_stock_moves(self):
        self.ensure_one()
        move_lines = self.env['stock.move.line'].search([
            ('picking_id', 'in', self.picking_ids.ids)
        ])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Move Lines',
            'res_model': 'stock.move.line',
            'view_mode': 'list,form',
            'domain': [('id', 'in', move_lines.ids)],
            'context': {'default_picking_id': self.picking_ids[:1].id if self.picking_ids else False},
        }
class DispatchChecklistQstnnr(models.Model):
    _name = "sale.order.dispatch.checklist"
    _rec_name = 'order_id'
    _description = "Dispatch Checklist Questionnaire"
    _inherit = ['mail.thread']

    order_id = fields.Many2one("sale.order", string="Lead", required=True)
    picking_id = fields.Many2one("stock.picking", string="Delivery Order", required=True)
    access_token = fields.Char("Access Token", required=True, default=lambda s: uuid.uuid4().hex, size=43) 
    state = fields.Selection([('draft', 'Draft'),
                              ('submitted', 'Submitted')], 
                              string="Status", default="draft" , tracking=True)
    
    @api.model
    def _validate_access_token(self, access_token):
        return self.sudo().search([('access_token', '=', access_token)], limit=1)
    
    def _get_dispatch_checklist_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        dispatch_checklist_url = f"{base_url}/jharkhand_dispatch_checklist/{self.access_token}"
        return dispatch_checklist_url 
