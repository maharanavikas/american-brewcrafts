# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class SaleQuotationApprovalLineWizard(models.TransientModel):
    _name = 'sale.quotation.approval.line.wizard'
    _description = 'Sale Quotation Approve Line Wizard'

    comment = fields.Text(string="Comment", required=True)
    sale_id = fields.Many2one('sale.order', string="Sale Order", required=True)
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

        line = self.sale_id.approval_line_ids.filtered(
            lambda l: l.user_id == user and l.state in ['pending', 'waiting']
        )[:1]

        if not line:
            raise UserError("You are not a valid approver for this Sale Order.")

        if any(l.state not in ['approved','rejected'] for l in
               self.sale_id.approval_line_ids.filtered(lambda l: l.sequence < line.sequence)):
            raise UserError("Previous level approvals must be completed before you can act.")

        if self.action_type == 'approve':
            if line.state == 'approved':
                raise UserError("You have already approved this step.")

            line.write({'state': 'approved', 'comment': self.comment})

            self.sale_id.activity_feedback(
                ['abcl_sale.abcl_sale_mail_act_sale_quotation_approval'],
                feedback='Approved.'
            )

            # all_approved = all(approval_line.state == 'approved' for approval_line in self.sale_id.approval_line_ids)
            # if all_approved:
            last_line = max(self.sale_id.approval_line_ids, key=lambda l: l.sequence, default=False)

            if last_line and line.id == last_line.id and line.state == 'approved':
                template = self.env.ref('abcl_sale.abcl_sale_order_approved_mail_template')
                if template and self.sale_id.user_id.partner_id.email:
                    template.send_mail(self.sale_id.id,
                                       email_values={'email_to': self.sale_id.user_id.partner_id.email})
            else:
                next_line = self.sale_id.approval_line_ids.filtered(
                    lambda l: l.sequence > line.sequence and l.state == 'pending'
                )[:1]

                if next_line:
                    next_user = next_line.user_id
                    # next_line.write({'state': 'pending'})

                    self.sale_id.activity_schedule(
                        'abcl_sale.abcl_sale_mail_act_sale_quotation_approval',
                        user_id=next_user.id,
                        note=f'Please review and approve the Sale Order: {self.sale_id.name}'
                    )

                    template = self.env.ref('abcl_sale.abcl_sale_order_approval_mail_template')
                    if template and next_user.partner_id.email:
                        template.send_mail(
                            self.sale_id.id,
                            email_values={'email_to': next_user.partner_id.email}
                        )

        elif self.action_type == 'reject':
            if line.state == 'approved':
                raise UserError("You have already approved this step. Cannot reject again.")
            if line.state == 'rejected':
                raise UserError("You have already rejected this step.")

            line.write({'state': 'rejected', 'comment': self.comment})
            next_line = self.sale_id.approval_line_ids.filtered(
                lambda l: l.sequence > line.sequence and l.state == 'waiting'
            ).sorted(key=lambda l: l.sequence)[:1]
            if next_line:
                next_line.write({'state': 'pending'})

            self.sale_id.activity_feedback(
                ['abcl_sale.abcl_sale_mail_act_sale_quotation_approval'],
                feedback='Rejected.'
            )
            template = self.env.ref('abcl_sale.abcl_sale_order_rejected_mail_template')
            if template and self.sale_id.user_id.partner_id.email:
                template.send_mail(self.sale_id.id,
                                   email_values={'email_to': self.sale_id.user_id.partner_id.email})

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Approval Submitted",
                'message': "Your action has been recorded.",
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'}
            }
        }
