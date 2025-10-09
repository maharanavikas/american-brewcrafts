from odoo import models, fields, api


class BulkApproval(models.TransientModel):
    _name = 'sale.order.bulk.approval'
    _description = 'Bulk Approval Wizard'

    remark = fields.Text(string="Remark", store=True)

    def apply_remark(self):
        user = self.env.user
        remark = self.remark and self.remark.strip() or f"Bulk Approved by {user.name}"
        for rec in self:
            active_ids = self.env.context.get('active_ids', [])
        orders = self.env['sale.order'].browse(active_ids)
        for order in orders:
            order.get_bulk_approve(remark)