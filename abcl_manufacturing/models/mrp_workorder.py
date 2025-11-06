# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from datetime import date
from odoo.exceptions import UserError, ValidationError

class MrpProductionWorkcenterLine(models.Model):
    _inherit = 'mrp.workorder'

    def button_start(self, raise_on_invalid_state=False, bypass=False):
        res = super(MrpProductionWorkcenterLine, self).button_start(raise_on_invalid_state=raise_on_invalid_state, bypass=bypass)
        for rec in self:
            if rec.production_id.quality_check_todo:
                raise ValidationError("Please complete the Pre production Quality Checks before starting the Work Order.")
            elif rec.production_id.quality_check_fail:
                raise ValidationError("You cannot start the Work Order as Pre production Quality Checks have failed")
            # elif rec.quality_check_todo:
            #     print("In button_start QC todo")
            #     raise ValidationError("Please complete the Quality Checks before starting the Work Order.")
            elif rec.quality_check_fail:
                raise ValidationError("You cannot start the Work Order as Quality Checks for the components have failed")
        return res

    def action_mark_as_done(self):
        res = super(MrpProductionWorkcenterLine, self).action_mark_as_done()
        for rec in self:
            if rec.production_id.quality_check_todo:
                raise ValidationError("Please complete the Pre production Quality Checks before starting the Work Order.")
            elif rec.production_id.quality_check_fail:
                raise ValidationError("You cannot start the Work Order as Pre production Quality Checks for the components have failed")
            elif rec.quality_check_todo:
                raise ValidationError("Please complete the Quality Checks before starting the Work Order.")
            elif rec.quality_check_fail:
                raise ValidationError("You cannot start the Work Order as Quality Checks for the components have failed")
        return res

    def button_finish(self):
        for rec in self:
            if rec.production_id.quality_check_todo:
                raise ValidationError("Please complete the Pre production Quality Checks before starting the Work Order.")
            elif rec.production_id.quality_check_fail:
                raise ValidationError("You cannot finish the Work Order as Pre production Quality Checks for the components have failed")
            elif rec.quality_check_todo:
                raise ValidationError("Please complete the Quality Checks before starting the Work Order.")
            elif rec.quality_check_fail:
                raise ValidationError("You cannot finish the Work Order as Quality Checks for the components have failed")
        res = super(MrpProductionWorkcenterLine, self).button_finish()
        return res