# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PurchaseApprovalReasonWizard(models.TransientModel):
    _name = 'purchase.approval.comment.wizard'
    _description = 'Purchase Approve Reason Wizard'

    comment = fields.Text(string="Comment", required=True)
    purchase_id = fields.Many2one('purchase.order', string="Purchase Order", required=True)
    action_type = fields.Selection([
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ], default='approve', string="Action Type")

    @api.constrains('comment')
    def _check_comment_not_empty_or_spaces(self):
        for record in self:
            if not record.comment or not record.comment.strip():
                raise ValidationError("The comment cannot be empty or contain only spaces.")

    def action_submit(self):
        self.ensure_one()
        user = self.env.user

        line = self.purchase_id.approval_line_ids.filtered(
            lambda l: l.approver_id == user and l.approval_status == 'pending'
        ).sorted(key=lambda l: l.sequence)[:1]

        if not line:
            raise UserError("You are not assigned as a pending approver for this Purchase Order.")
        line = line[0]

        if any(l.approval_status != 'approved' for l in
               self.purchase_id.approval_line_ids.filtered(lambda l: l.sequence < line.sequence)):
            raise UserError("Previous level approvals must be completed before you can act.")

        if self.action_type == 'approve':
            line.write({'approval_status': 'approved', 'comment': self.comment})
            feedback, title, message, msg_type = 'Approved.', "Approval Successful", "Thank you! The Purchase Order has been approved from your side.", 'success'
            self.purchase_id.activity_feedback(['abcl_purchase.abcl_purchase_mail_act_purchase_order_approval'],
                                               feedback=feedback)

            all_approved = all(approval_line.approval_status == 'approved'
                               for approval_line in self.purchase_id.approval_line_ids)

            if all_approved:
                template = self.env.ref('abcl_purchase.abcl_purchase_order_approved_mail_template')
                if template and self.purchase_id.create_uid.partner_id.email:
                    template.send_mail(self.purchase_id.id,
                                       email_values={'email_to': self.purchase_id.create_uid.partner_id.email})
            else:
                next_line = self.purchase_id.approval_line_ids.filtered(
                    lambda l: l.sequence > line.sequence and l.approval_status == 'pending'
                ).sorted(key=lambda l: l.sequence)[:1]

                if next_line:
                    next_user = next_line.approver_id
                    self.purchase_id.activity_schedule(
                        'abcl_purchase.abcl_purchase_mail_act_purchase_order_approval',
                        user_id=next_user.id,
                        note=f'Please review and approve the Purchase Order: {self.purchase_id.name}'
                    )

                    template = self.env.ref('abcl_purchase.abcl_purchase_order_approval_mail_template')
                    if template and next_user.partner_id.email:
                        template.send_mail(self.purchase_id.id, email_values={'email_to': next_user.partner_id.email})

        elif self.action_type == 'reject':
            if line.approval_status == 'approved':
                raise UserError("You have already approved this step. Cannot reject.")
            line.write({'approval_status': 'rejected', 'comment': self.comment})
            feedback, title, message, msg_type = 'Rejected.', "Rejection Successful", "You have rejected this Purchase Order.", 'danger'
            self.purchase_id.activity_feedback(['abcl_purchase.abcl_purchase_mail_act_purchase_order_approval'],
                                               feedback=feedback)

            template = self.env.ref('abcl_purchase.abcl_purchase_order_rejected_mail_template')
            if template and self.purchase_id.create_uid.partner_id.email:
                template.send_mail(self.purchase_id.id,
                                   email_values={'email_to': self.purchase_id.create_uid.partner_id.email})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': msg_type,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }