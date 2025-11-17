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
    # def button_start(self, raise_on_invalid_state=False, bypass=False):
    #     res = super(MrpProductionWorkcenterLine, self).button_start(raise_on_invalid_state=raise_on_invalid_state,
    #                                                                 bypass=bypass)
    #
    #     for rec in self:
    #
    #         # WORKCENTER CATEGORY PRODUCT VALIDATION
    #         # ------------------------------------------
    #         # categories = rec.workcenter_id.tag_ids
    #         # mo_product = rec.product_id
    #         #
    #         # allowed_combinations = self.env['workcenter.product.combination'].search([
    #         #     ('workcenter_category_id', 'in', categories.ids)
    #         # ])
    #         #
    #         # allowed_products = set()
    #         # for combo in allowed_combinations:
    #         #     allowed_products.update(combo.product_ids.ids)
    #         #
    #         # if mo_product.id not in allowed_products:
    #         #     raise ValidationError(
    #         #         f"The product '{mo_product.display_name}' is not allowed for the selected Workcenter.\n\n"
    #         #         f"Allowed products based on category: "
    #         #         f"{', '.join(self.env['product.product'].browse(list(allowed_products)).mapped('display_name'))}."
    #         #     )
    #
    #         # Work Center Capacity Check
    #         # qty = rec.qty_producing or rec.production_id.product_qty
    #         qty = rec.production_id.qty_producing if rec.production_id.qty_producing > 0 else rec.production_id.product_qty
    #         capacity = rec.workcenter_id.default_capacity or 1
    #         if qty > capacity:
    #             raise ValidationError(
    #                 f"Production quantity ({qty}) exceeds the work center capacity ({capacity}). "
    #                 "Please split the work order before starting."
    #             )
    #         # Quality Checks
    #         if rec.production_id.quality_check_todo:
    #             raise ValidationError(
    #                 "Pre-production quality checks must be completed before starting this work order.")
    #         if rec.production_id.quality_check_fail:
    #             raise ValidationError("Cannot start the work order as pre-production quality checks failed.")
    #         if rec.quality_check_fail:
    #             raise ValidationError("Cannot start the work order as component quality checks failed.")
    #
    #     return res
    def button_start(self, raise_on_invalid_state=False, bypass=False):
        res = super().button_start(raise_on_invalid_state=raise_on_invalid_state, bypass=bypass)

        for wo in self:
            # Product–Category–Capacity Validation
            wo._validate_workorder_category_and_capacity()

            # Quality checks
            if wo.production_id.quality_check_todo:
                raise ValidationError(_("Complete pre-production quality checks before starting."))
            if wo.production_id.quality_check_fail:
                raise ValidationError(_("Pre-production quality checks have failed."))
            if wo.quality_check_fail:
                raise ValidationError(_("Component quality checks have failed."))

        return res

    def _validate_workorder_category_and_capacity(self):
        for wo in self:
            workcenter = wo.workcenter_id
            product = wo.product_id
            qty_needed = wo.qty_producing if wo.qty_producing > 0 else wo.production_id.product_qty

            # 1) Find a valid combination
            combos = self.env['workcenter.product.combination'].search([
                ('workcenter_category_id', 'in', workcenter.tag_ids.ids)
            ])
            selected_combo = next((c for c in combos if product.id in c.product_ids.ids), None)

            # ----------------------------------------------------
            # CASE 1: Product NOT part of any combination → ALLOW
            # ----------------------------------------------------
            if not selected_combo:
                # No combination applies → no restrictions
                return

            # ----------------------------------------------------
            # CASE 2: Combination found → Apply restrictions
            # ----------------------------------------------------
            allowed_products = set(selected_combo.product_ids.ids)

            # 2) Validate other active workorders (in-progress)
            active_wos = self.env['mrp.workorder'].search([
                ('id', '!=', wo.id),
                ('workcenter_id', '=', workcenter.id),
                ('qty_producing', '>', 0),
                ('state', '=', 'progress'),
            ])

            for other in active_wos:
                if other.product_id.id not in allowed_products:
                    raise ValidationError(
                        _(
                            "The product '%s' is not allowed for this workcenter.\n\n"
                            "Allowed products for this workcenter are:\n%s"
                        )
                        % (
                            product.display_name,
                            ", ".join(selected_combo.product_ids.mapped("display_name")),
                        )
                    )

            # 3) Capacity check
            used_capacity = sum(active_wos.mapped('qty_producing'))
            capacity = workcenter.default_capacity or 1
            available = capacity - used_capacity

            if qty_needed > available:
                raise ValidationError(
                    _(
                        "Insufficient capacity in Workcenter '%s'.\n\n"
                        "Available capacity : %s units\n"
                        "Requested quantity : %s units\n\n"
                        "Please reduce the production quantity or wait until capacity is free."
                    ) % (workcenter.name, available, qty_needed)
                )

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
