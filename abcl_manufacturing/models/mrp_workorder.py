# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError, ValidationError


class MrpProductionWorkcenterLine(models.Model):
    _inherit = 'mrp.workorder'

    # def button_start(self, raise_on_invalid_state=False, bypass=False):
    #     res = super(MrpProductionWorkcenterLine, self).button_start(raise_on_invalid_state=raise_on_invalid_state, bypass=bypass)
    #     for rec in self:
    #         if rec.production_id.quality_check_todo:
    #             raise ValidationError("Please complete the Pre production Quality Checks before starting the Work Order.")
    #         elif rec.production_id.quality_check_fail:
    #             raise ValidationError("You cannot start the Work Order as Pre production Quality Checks have failed")
    #         # elif rec.quality_check_todo:
    #         #     print("In button_start QC todo")
    #         #     raise ValidationError("Please complete the Quality Checks before starting the Work Order.")
    #         elif rec.quality_check_fail:
    #             raise ValidationError("You cannot start the Work Order as Quality Checks for the components have failed")
    #
    #     return res
    ###########workcenter validation########
    def button_start(self, raise_on_invalid_state=False, bypass=False):
        res = super(MrpProductionWorkcenterLine, self).button_start(raise_on_invalid_state=raise_on_invalid_state,
                                                                    bypass=bypass)

        for rec in self:

            # WORKCENTER CATEGORY PRODUCT VALIDATION
            # ------------------------------------------
            # categories = rec.workcenter_id.tag_ids
            # mo_product = rec.product_id
            #
            # allowed_combinations = self.env['workcenter.product.combination'].search([
            #     ('workcenter_category_id', 'in', categories.ids)
            # ])
            #
            # allowed_products = set()
            # for combo in allowed_combinations:
            #     allowed_products.update(combo.product_ids.ids)
            #
            # if mo_product.id not in allowed_products:
            #     raise ValidationError(
            #         f"The product '{mo_product.display_name}' is not allowed for the selected Workcenter.\n\n"
            #         f"Allowed products based on category: "
            #         f"{', '.join(self.env['product.product'].browse(list(allowed_products)).mapped('display_name'))}."
            #     )

            # Work Center Capacity Check
            # qty = rec.qty_producing or rec.production_id.product_qty
            qty = rec.production_id.qty_producing if rec.production_id.qty_producing > 0 else rec.production_id.product_qty
            capacity = rec.workcenter_id.default_capacity or 1
            if qty > capacity:
                raise ValidationError(
                    f"Production quantity ({qty}) exceeds the work center capacity ({capacity}). "
                    "Please split the work order before starting."
                )
            # Quality Checks
            if rec.production_id.quality_check_todo:
                raise ValidationError(
                    "Pre-production quality checks must be completed before starting this work order.")
            if rec.production_id.quality_check_fail:
                raise ValidationError("Cannot start the work order as pre-production quality checks failed.")
            if rec.quality_check_fail:
                raise ValidationError("Cannot start the work order as component quality checks failed.")

        return res

    # def action_mark_as_done(self):
    #     res = super(MrpProductionWorkcenterLine, self).action_mark_as_done()
    #     for rec in self:
    #         if rec.production_id.quality_check_todo:
    #             raise ValidationError("Please complete the Pre production Quality Checks before starting the Work Order.")
    #         elif rec.production_id.quality_check_fail:
    #             raise ValidationError("You cannot start the Work Order as Pre production Quality Checks for the components have failed")
    #         elif rec.quality_check_todo:
    #             raise ValidationError("Please complete the Quality Checks before starting the Work Order.")
    #         elif rec.quality_check_fail:
    #             raise ValidationError("You cannot start the Work Order as Quality Checks for the components have failed")
    #     return res
    ############workcenter validation########
    def action_mark_as_done(self):
        # Validate BEFORE completing
        for rec in self:
            # Work Center Capacity Check FIRST
            qty = rec.production_id.qty_producing if rec.production_id.qty_producing > 0 else rec.production_id.product_qty
            capacity = rec.workcenter_id.default_capacity or 1
            if qty > capacity:
                raise ValidationError(
                    f"Cannot complete Work Order. Production quantity ({qty}) exceeds Work Center capacity ({capacity}). "
                    "Please adjust or split the Work Order."
                )

            # Quality Validations
            if rec.production_id.quality_check_todo:
                raise ValidationError("Complete Pre-production Quality Checks before completing this Work Order.")
            if rec.production_id.quality_check_fail:
                raise ValidationError("Cannot complete Work Order as Pre-production Quality Checks failed.")
            if rec.quality_check_todo:
                raise ValidationError("Complete Component Quality Checks before completing this Work Order.")
            if rec.quality_check_fail:
                raise ValidationError("Cannot complete Work Order as Component Quality Checks failed.")

        return super(MrpProductionWorkcenterLine, self).action_mark_as_done()

    ############workcenter validation########

    def button_finish(self):
        for rec in self:
            if rec.production_id.quality_check_todo:
                raise ValidationError(
                    "Please complete the Pre production Quality Checks before starting the Work Order.")
            elif rec.production_id.quality_check_fail:
                raise ValidationError(
                    "You cannot finish the Work Order as Pre production Quality Checks for the components have failed")
            elif rec.quality_check_todo:
                raise ValidationError("Please complete the Quality Checks before starting the Work Order.")
            elif rec.quality_check_fail:
                raise ValidationError(
                    "You cannot finish the Work Order as Quality Checks for the components have failed")
        res = super(MrpProductionWorkcenterLine, self).button_finish()
        return res
