from odoo import models, fields, api


class ApprovalRemarkWizard(models.TransientModel):
    _name = 'pricelist.approval.remark.wizard'
    _description = 'Approval Remark Wizard'

    remark = fields.Text(string="Remark", required=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True)
    status = fields.Selection([('hold','Hold'),('reject','Rejected')], "Status", required=True)

    def apply_remark(self):
        self.ensure_one()
        pricelist = self.pricelist_id
        pricelist.approval_remark = self.remark
        if self.status == 'reject':
            pricelist.status = 'reject'
            reject_mail_template = self.env.ref('abcl_sale.email_template_pricelist_rejected')
            if reject_mail_template:
                reject_mail_template.with_context(action_user=self.env.user).send_mail(pricelist.id)

        elif self.status == 'hold':
            pricelist.status = 'hold'
            hold_mail_template = self.env.ref('abcl_sale.email_template_pricelist_hold')
            if hold_mail_template:
                hold_mail_template.with_context(action_user=self.env.user).send_mail(pricelist.id)
        
        return {'type': 'ir.actions.act_window_close'}