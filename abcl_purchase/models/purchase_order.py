# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import UserError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    min_qty_warning = fields.Json(string="Minimum Quantity Warning", compute="_compute_min_qty_warning", readonly=True,
                                  store=False)
    next_po_id = fields.Many2one('purchase.order', string='Next Purchase Order')
    product_categ_id = fields.Many2one('product.category', string="Product Category", required=True)
    partner_id = fields.Many2one(
        'res.partner',
        domain="[('supplier_rank', '>', 0), ('id', 'in', allowed_vendor_ids)]"
    )
    reason = fields.Char("Reason for PO")

    allowed_vendor_ids = fields.Many2many('res.partner', compute='_compute_allowed_vendors', string="Allowed vendors")
    approval_line_ids = fields.One2many('purchase.approval.line', 'purchase_id', string="Approval Lines")
    state = fields.Selection(selection_add=[('close', 'Closed')], readonly=False)

    close_reason_id = fields.Many2one('purchase.close.reason', string="Close Reason")
    closed_date = fields.Datetime(string="Closed Date")
    all_approvals_done = fields.Boolean(string="All Approvals Done", compute="_compute_all_approvals_done", store=True)
    po_ref_no = fields.Char("PO Reference No.")
    user_is_approver = fields.Boolean("User is Approver ?", compute="_compute_approval_for_current_user")
    approval_status = fields.Selection([
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')], string="Approval Status",
        compute="_compute_approval_status",
        store=True, readonly=False
    )
    # priority = fields.Selection(selection_add=[
    #     ('special', 'Special'),
    # ])
    priority_type = fields.Selection(
        [('normal', 'Normal'),('urgent', 'Urgent'), ('special', 'Special')],
        string="Priority Type",
        default='normal'
    )
    sent_for_approval = fields.Boolean("Sent for Approval", default=False)

    @api.depends('approval_line_ids', 'approval_line_ids.approval_status')
    def _compute_approval_status(self):
        for po in self:
            if not po.approval_line_ids:
                po.approval_status = 'pending'
            elif any([line.approval_status == 'rejected' for line in po.approval_line_ids]):
                po.approval_status = 'rejected'
            elif all(line.approval_status == 'approved' for line in po.approval_line_ids):
                po.approval_status = 'approved'
            else:
                po.approval_status = 'pending'

    @api.depends('approval_line_ids', 'approval_line_ids.approval_status', 'approval_line_ids.approver_id')
    def _compute_approval_for_current_user(self):
        current_user = self.env.user
        for po in self:
            po.user_is_approver = any([line.approval_status == 'pending' and line.approver_id.id == current_user.id for line in po.approval_line_ids])

    def action_close(self):
        self.ensure_one()
        return {
            'name': 'Close Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.close.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_id': self.id,
            },
        }

    def action_open_purchase_analysis(self):
        self.ensure_one()
        action = self.env.ref('purchase.action_purchase_order_report_all').read()[0]
        po_ids = [self.id]
        if self.next_po_id:
            po_ids.append(self.next_po_id.id)
        action['domain'] = [('order_id', 'in', po_ids)]

        return action

    def _compute_min_qty_warning(self):
        for order in self:
            warnings = {}
            lines_to_warn = self.env['purchase.order.line']
            warning_messages = []

            for line in order.order_line:
                product = line.product_id
                uom = line.product_uom
                vendor = order.partner_id

                seller = product._select_seller(
                    partner_id=vendor,
                    quantity=line.product_qty,
                    # date=False,
                    date=order.date_order and order.date_order.date(),
                    uom_id=uom
                )
                print("seller",seller)

                if seller and line.product_qty < seller.minimum_order_qty:
                    lines_to_warn |= line

                    product_name = product.display_name
                    vendor_name = vendor.name
                    min_order_qty = seller.minimum_order_qty
                    uom_name = uom.name

                    warning_messages.append(_(
                        "• Product '%s': Minimum order quantity for vendor '%s' is %s %s" % (
                            product_name, vendor_name, min_order_qty, uom_name)
                    ))

            if lines_to_warn:
                main_message = _("Minimum Order Quantity requirements not met for below products:")
                detailed_message = main_message + "\n\n" + "\n".join(warning_messages)

                supplierinfos = lines_to_warn.mapped(lambda l: l.product_id._select_seller(
                    partner_id=order.partner_id,
                    quantity=l.product_qty,
                    date=order.date_order,
                    uom_id=l.product_uom
                )).filtered(lambda s: s)

                warnings['minimum_order_qty'] = {
                    'message': detailed_message,
                    'action_text': _("View Vendor Pricelist"),
                    'action': supplierinfos._get_records_action(
                        name=_("Vendor Pricelist"),
                        target='current',
                        views=[(self.env.ref('product.product_supplierinfo_tree_view').id, 'list')],
                        domain=[('id', 'in', supplierinfos.ids)],
                    )
                }

            order.min_qty_warning = warnings

    def action_view_next_po(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Next Purchase Order',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'res_id': self.next_po_id.id,
        }

    @api.depends('product_categ_id')
    def _compute_allowed_vendors(self):
        for order in self:
            if order.product_categ_id:
                products = self.env['product.product'].search([('categ_id', '=', order.product_categ_id.id)])
                vendors = products.mapped('seller_ids.partner_id')
                order.allowed_vendor_ids = vendors
            else:
                order.allowed_vendor_ids = self.env['res.partner']

    # @api.onchange('product_categ_id')
    # def _onchange_product_category(self):
    #     self.partner_id = False
    #     self.order_line = [(5, 0, 0)]

    # @api.onchange('partner_id')
    # def _onchange_partner(self):
    #     if self.partner_id and self.product_categ_id:
    #         valid_lines = self.order_line.filtered(
    #             lambda line: line.product_id.categ_id.id == self.product_categ_id.id and
    #                          self.partner_id.id in line.product_id.seller_ids.mapped('partner_id').ids
    #         )
    #
    #         self.order_line = [(5, 0, 0)]
    #         self.order_line = [(0, 0, {
    #             'product_id': line.product_id.id,
    #             'product_qty': line.product_qty,
    #             'price_unit': line.price_unit,
    #             'name': line.name,
    #             'product_uom': line.product_uom.id,
    #             'date_planned': line.date_planned,
    #             'taxes_id': [(6, 0, line.taxes_id.ids)]
    #         }) for line in valid_lines]
    #     else:
    #         self.order_line = [(5, 0, 0)]

    def action_generate_approval_lines(self):
        self.sent_for_approval = True
        for res in self:
            approval_lines = []

            employee = self.env['hr.employee'].search([('user_id', '=', res.create_uid.id)], limit=1)
            dept_mgr = employee.department_id.manager_id.user_id if employee and employee.department_id else None
            categ_mgr = res.product_categ_id.department_manager_id if res.product_categ_id else None

            first_approver = dept_mgr or categ_mgr
            if not first_approver:
                raise UserError("No Department Manager or Category Department Manager found for the creator.")

            if first_approver:
                approval_lines.append((0, 0, {
                    'approver_id': first_approver.id,
                    'sequence': 1
                }))

            plant_group = self.env.ref('abcl_base.group_plant_manager')
            plant_manager = self.env['res.users'].search([('groups_id', 'in', [plant_group.id])], limit=1)
            if not plant_manager:
                raise UserError("No Plant Manager is configured.")


            if plant_manager:
                approval_lines.append((0, 0, {
                    'approver_id': plant_manager.id,
                    'sequence': len(approval_lines) + 1
                }))

            total = res.amount_untaxed
            need_vp = False

            for line in res.order_line:
                product = line.product_id
                category = product.categ_id

                min_qty = product.product_tmpl_id.minimum_qty
                price_limit = category.approval_price_limit
                is_approval_enabled = category.is_approval_enabled
                approval_type = category.approval_condition_type

                if is_approval_enabled:
                    if approval_type == 'quantity_based':
                        base_date = res.date_order.date() if res.date_order else fields.Date.context_today(self)
                        month_start = base_date.replace(day=1)
                        next_month = month_start + relativedelta(months=1)

                        qty_grouped = self.env['purchase.order.line'].read_group(
                            domain=[
                                ('product_id', '=', product.id),
                                ('state', 'in', ['purchase', 'done']),
                                ('date_order', '>=', month_start),
                                ('date_order', '<', next_month)
                            ],
                            fields=['product_qty'],
                            groupby=['product_id']
                        )
                        monthly_qty = qty_grouped[0]['product_qty'] if qty_grouped else 0

                        if min_qty:
                            if monthly_qty + line.product_qty > min_qty:
                                need_vp = True
                                break
                        else:
                            category_qty_limit = category.quantity
                            if category_qty_limit and line.product_qty > category_qty_limit:
                                need_vp = True
                                break

                    # elif approval_type == 'price_based' and price_limit and total > price_limit:
                    elif approval_type == 'price_based' and price_limit and line.price_total > price_limit:
                        print("line.price_total",line.price_total)
                        need_vp = True
                        break

                if category.is_deviation and category.deviation_percentage:
                    seller = product.seller_ids.filtered(lambda s: s.partner_id == res.partner_id)
                    vendor_price = seller[0].price if seller else 0.0

                    if vendor_price > 0:
                        deviation = ((line.price_unit - vendor_price) / vendor_price) * 100
                        if deviation > (category.deviation_percentage * 100):
                            need_vp = True
                            break

            if need_vp:
                vp_group = self.env.ref('abcl_base.group_vice_president')
                vp_user = self.env['res.users'].search([('groups_id', 'in', [vp_group.id])], limit=1)

                if not vp_user:
                    raise UserError("No Vice President is configured.")

                if vp_user:
                    approval_lines.append((0, 0, {
                        'approver_id': vp_user.id,
                        'sequence': len(approval_lines) + 1
                    }))
            res.approval_line_ids = approval_lines

            res.activity_schedule(
                'abcl_purchase.abcl_purchase_mail_act_purchase_order_approval',
                user_id=first_approver.id,
                note='Please review and approve the Purchase Order: %s' % res.name
            )
            template = self.env.ref('abcl_purchase.abcl_purchase_order_approval_mail_template')
            if template and first_approver.partner_id.email:
                template.send_mail(res.id, email_values={
                    'email_to': first_approver.partner_id.email,
                })

    def action_open_approval_form(self):
        self.ensure_one()
        return {
            'name': 'Approve Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.approval.comment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_id': self.id,
                'default_action_type': 'approve'
            }
        }

    def action_open_reject_form(self):
        self.ensure_one()
        return {
            'name': 'Reject Purchase Order',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.approval.comment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_purchase_id': self.id,
                'default_action_type': 'reject',
            }
        }

    @api.depends('approval_line_ids.approval_status')
    def _compute_all_approvals_done(self):
        for order in self:
            if order.approval_line_ids:
                order.all_approvals_done = all(line.approval_status == 'approved' for line in order.approval_line_ids)
            else:
                order.all_approvals_done = True

    # @api.model_create_multi
    # def create(self, vals_list):
    #     default_categ = self.env['product.category'].search([('is_default_category', '=', True)], limit=1).id
    #     for vals in vals_list:
    #         vals.setdefault('product_categ_id', default_categ)
    #
    #     return super().create(vals_list)

    # def action_bulk_po_approve(self):
    #     for order in self:
    #         if order.user_is_approver:
    #             user = self.env.user
    #             approval_lines = order.approval_line_ids.filtered(lambda l: l.approver_id == user and l.approval_status == 'pending')
    #             approval_lines.write({'approval_status': 'approved', 'comment': 'Bulk approved by approver'})
    #             self.activity_feedback( ['abcl_purchase.abcl_purchase_mail_act_purchase_order_approval'],feedback='Approved.')
    #             if order.all_approvals_done:
    #                 mail_template = self.env.ref('abcl_purchase.abcl_purchase_order_approved_mail_template')
    #                 if mail_template:
    #                     mail_template.send_mail(order.id, email_values={'email_to': order.create_uid.email})
    #         else:
    #             raise ValidationError("You are not authorized to approve this order or not assigned to you.")

    def action_bulk_po_approve(self):
        return {
            'name': 'Purchase Order Bulk Approval',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.bulk.approval',
            'view_mode': 'form',
            'target': 'new',
        }
    
    def get_bulk_approve(self, remark):
        user = self.env.user
        invalid_sale_orders = self.filtered(lambda o: not o.user_is_approver)
        if invalid_sale_orders:
            names = ', '.join(invalid_sale_orders.mapped('name'))
            raise ValidationError(f"You are not authorized to approve the following orders: {names}")
        all_approval_lines = self.approval_line_ids.filtered(lambda l: l.approver_id == user and l.approval_status == 'pending')
        all_approval_lines.write({'approval_status': 'approved', 'comment': remark})
        self.activity_feedback(['abcl_purchase.abcl_purchase_mail_act_purchase_order_approval'], feedback='Approved.')
        if self.all_approvals_done:
            mail_template = self.env.ref('abcl_purchase.abcl_purchase_order_approved_mail_template')
    
        if mail_template:
            mail_template.send_mail(self.id, email_values={'email_to': self.user_id.email})
        else:
            raise ValidationError("You are not authorized to approve this order.")

    def action_get_alternative_vendors(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Alternative Vendors',
            'view_mode': 'form',
            'res_model': 'alternative.vendor.wizard',
            'context': {'default_purchase_order': self.id},
            'target': 'new',
        }

    @api.model
    def action_split_po(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError("You cannot Split the PO unless it's in draft state.")
        return{
            'type': 'ir.actions.act_window',
            'name': 'Split Purchase Order',
            'view_mode': 'form',
            'res_model': 'split.po.wizard',
            'context': {'default_purchase_order': self.id, 'default_vendor_ids': [(5, 0, 0)]},
            'target': 'new',
        }
    