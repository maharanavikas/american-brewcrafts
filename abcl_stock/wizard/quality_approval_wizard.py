# -*- coding: utf-8 -*-

from odoo import models, fields, api

class QualityApproval(models.TransientModel):
    _name = 'quality.approval.wizard'
    _description = 'Quality Approval Wizard'

    quality_check_id = fields.Many2one('quality.check', string="Quality Check", required=True)
    action_type = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string="Action Type", required=True)
    remark = fields.Text(string="Remark", store=True, required=True)
    
    def apply_remark(self):
        self.ensure_one()
        self.quality_check_id.plant_manager_comment = self.remark
        self.quality_check_id.sent_for_approval = False
        if self.action_type == 'fail':
            # self.quality_check_id.do_fail()
            self.quality_check_id.activity_feedback(['abcl_stock.abcl_quality_fail_approval'], feedback='Rejected.')
        else:
            self.quality_check_id.do_pass()
            self.quality_check_id.activity_feedback(['abcl_stock.abcl_quality_fail_approval'], feedback='Approved.')