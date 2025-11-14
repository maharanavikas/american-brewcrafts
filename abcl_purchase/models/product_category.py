# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = "product.category"

    enable_internal_po = fields.Boolean("Enable For Internal PO.")
    department_manager_id = fields.Many2one('res.users', string="Department Manager")
    approval_price_limit = fields.Float(string="Price Approval Limit")
    quantity = fields.Float(string="Quantity")
    approval_condition_type = fields.Selection([('price_based', 'Price Based'),
                             ('quantity_based', 'Quantity Based'),
                            ], string='Approval Condition Type')
    is_approval_enabled = fields.Boolean("Enable Approval Condition")
    is_deviation = fields.Boolean("Price Deviation")
    deviation_percentage = fields.Float("Deviation Percentage")
    is_default_category = fields.Boolean("Is Default Category")
    is_fg = fields.Boolean("Is FG",help="Is Finished Goods")
    is_wort = fields.Boolean("Is Wort", help="Is Wort Beer")
    is_bbs = fields.Boolean("Is BBS", help="Is Bulk Beer Stock")
    is_yb = fields.Boolean("Is YB", help="Is Young Beer")
    enable_internal_consumption = fields.Boolean("Internal Consumption", help="Is Internal Consumption Enabled for this Category")

    @api.constrains('is_fg', 'is_wort', 'is_bbs', 'is_yb')
    def _check_unique_flags(self):

        flag_mapping = {'is_fg': _("Finished Goods (Is FG)"), 'is_wort': _("Wort Beer"), 'is_bbs': _("Bulk Beer Stock"), 'is_yb': _("Young Beer"),}

        for rec in self:
            for field, label in flag_mapping.items():
                if getattr(rec, field):
                    duplicate = self.search_count([(field, '=', True), ('id', '!=', rec.id)])
                    if duplicate:
                        raise ValidationError(
                            _("Only one category can be marked as %s.") % label
                        )





