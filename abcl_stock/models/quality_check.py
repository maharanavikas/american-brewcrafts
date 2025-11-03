# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class QualityCheck(models.Model):
    _inherit = "quality.check"

    plant_manager_comment = fields.Text('Plant Manager Comment', help="Comment added by Plant Manager for reapproval")
    is_check_failed = fields.Boolean("Initial Approval")
    approver_id = fields.Many2one('res.users', string='Approval Responsible', readonly=True, tracking=True)
    buyer_id = fields.Many2one('res.users', string='Buyer')
    sent_for_approval = fields.Boolean("Sent for Approval", default=False)

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            # You can set the buyer based on your business logic
            # For example, if the picking has a related purchase order:
            if hasattr(self.picking_id, 'purchase_id') and self.picking_id.purchase_id:
                self.buyer_id = self.picking_id.purchase_id.user_id
            # Or you can set it based on other criteria
            # self.buyer_id = self.picking_id.user_id  # if picking has a responsible user
        else:
            self.buyer_id = False


    def do_pass(self):
        is_plant_manager = self.env.user.has_group('abcl_base.group_plant_manager')
        is_quality_manager = self.env.user.has_group('quality.group_quality_manager')
        if not (is_quality_manager or is_plant_manager):
            raise UserError("Only a Quality Manager and Plant Manager can approve quality checks.")
        print("is_plant_manager", is_plant_manager)

        activity = self.env['mail.activity'].search([
                ('res_id', '=', self.id), 
                ('res_model', '=', 'quality.check'), 
                ('activity_type_id', '=', self.env.ref('abcl_stock.quality_check_notification').id)])
        if activity:
            self.activity_feedback(['abcl_stock.quality_check_notification'], feedback='Quality Failed.')

        for check in self:
            # If there is no related production, run default behavior
            if not check.production_id:
                super(QualityCheck, check).do_pass()
                continue

            if check.quality_state == 'fail':
                print("is_plant_manager",is_plant_manager)
                if not is_plant_manager:
                    raise UserError("Only a Plant Manager can reapprove a failed quality check.")

                if not check.plant_manager_comment:
                    raise UserError("A comment is required for Plant Manager reapproval of a failed quality check.")

                check.approver_id = self.env.user

                if check.user_id and check.user_id.partner_id.email:
                    template = self.env.ref('abcl_stock.abcl_quality_check_pass_mail_template')
                    if template:
                        template.send_mail(check.id, email_values={
                            'email_to': check.user_id.partner_id.email,
                        })

                return super(QualityCheck, check).do_pass()

            return super(QualityCheck, check).do_pass()

    ############for historical data import#######
    # def do_pass(self):
    #     is_plant_manager = self.env.user.has_group('abcl_base.group_plant_manager')
    #
    #     for check in self:
    #         if not check.production_id:
    #             if check.quality_state != 'pass':
    #                 check.write({
    #                     'quality_state': 'pass',
    #                     'user_id': self.env.user.id,
    #                 })
    #             continue
    #
    #         if not is_plant_manager:
    #             raise UserError(_("Only a Plant Manager can reapprove a failed quality check."))
    #
    #         if not check.plant_manager_comment:
    #             raise UserError(_("A comment is required for Plant Manager reapproval of a failed quality check."))
    #
    #         check.approver_id = self.env.user
    #         if check.quality_state != 'pass':
    #             check.write({
    #                 'quality_state': 'pass',
    #                 'user_id': self.env.user.id,
    #             })
    #
    #         if check.user_id and check.user_id.partner_id.email:
    #             template = self.env.ref('abcl_stock.abcl_quality_check_pass_mail_template')
    #             if template:
    #                 template.send_mail(check.id, email_values={
    #                     'email_to': check.user_id.partner_id.email,
    #                 })
    #
    #     return True

    def do_fail(self):
        res = super().do_fail()
        is_plant_manager = self.env.user.has_group('abcl_base.group_plant_manager')
        is_quality_manager = self.env.user.has_group('quality.group_quality_manager')
        if not (is_quality_manager or is_plant_manager):
            raise UserError("Only a Quality Manager and Plant Manager can approve quality checks.")

        activity = self.env['mail.activity'].search([
                ('res_id', '=', self.id), 
                ('res_model', '=', 'quality.check'), 
                ('activity_type_id', '=', self.env.ref('abcl_stock.quality_check_notification').id)])
        if activity:
            self.activity_feedback(['abcl_stock.quality_check_notification'], feedback='Quality Failed.')

        for check in self.filtered(lambda c: c.production_id):
            users = self.env.ref('abcl_base.group_plant_manager').users
            managers= users.filtered(lambda r: r.partner_id.email)
            check.is_check_failed = True

            if not managers:
                raise UserError("No Plant Manager is configured with a valid email address.")

            template = self.env.ref('abcl_stock.abcl_quality_check_fail_mail_template')

            for manager in managers:
                template.send_mail(check.id, email_values={
                    'email_to': manager.partner_id.email,
                })
        return res


    def write(self, vals):
        res = super().write(vals)

        if self.production_id:
            if 'quality_state' in vals:
                for rec in self:
                    if rec.quality_state == 'fail':
                        rec._check_quality_state()
        return res    

    def _check_quality_state(self):
        for check in self.filtered(lambda c: c.production_id):
            users = self.env.ref('abcl_base.group_plant_manager').users
            managers= users.filtered(lambda r: r.partner_id.email)
            check.sent_for_approval = True

            if not managers:
                raise UserError("No Plant Manager is configured with a valid email address.")

            self.activity_schedule(
                'abcl_stock.abcl_quality_fail_approval',
                user_id=managers[0].id,
                note=f'Quality Check {check.name} has failed and requires your approval.',
            )

    def action_quality_approval_wizard(self):
        self.ensure_one()
        return {
            'name': 'Quality Approve',
            'type': 'ir.actions.act_window',
            'res_model': 'quality.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_quality_check_id': self.id,
                'default_action_type': 'pass'
            }
        }

    def action_quality_reject_wizard(self):
        self.ensure_one()
        return {
            'name': 'Quality Approve',
            'type': 'ir.actions.act_window',
            'res_model': 'quality.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_quality_check_id': self.id,
                'default_action_type': 'fail'
            }
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = super(QualityCheck, self).create(vals_list)
        
        manger_group_id = 'quality.group_quality_manager'
        group = self.env.ref(manger_group_id, raise_if_not_found=False)
        if not group:
            return records

        managers = group.users.filtered(lambda u: u.login != 'admin') # Exclude admin user
        if not managers:
            return records

        for record in records:
            for manager in managers:
                print("manager", manager.name)
                record.activity_schedule('abcl_stock.quality_check_notification', user_id=manager.id, note=f'New Quality Check {record.name} has been created.')
                print("activity scheduled")
                template = self.env.ref('abcl_stock.template_quality_check_mail')
                if template:
                    template.with_context(manager_name=manager.name,
                                        reference=(record.production_id.name
                                                    or record.picking_id.name
                                                    or record.inventory_id.name
                                                    or 'Manual'),
                                        ).send_mail(record.id, email_values={'email_to': manager.email})
                
        return records