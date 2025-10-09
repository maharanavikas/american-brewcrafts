from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError,ValidationError
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare
from odoo.addons.stock.models.stock_rule import ProcurementException
from odoo.tools import groupby


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    from_mps = fields.Boolean(string="From MPS", readonly=True)

#     def write(self, vals):
#         if "product_qty" in vals:
#             for line in self:
#                 print("line.from_mps",line.from_mps)
#                 if line.from_mps:
#                     raise UserError(
#                         "You cannot change the quantity of this line because it was created from the MPS."
#                     )
#         return super().write(vals)


class StockRule(models.Model):
    _inherit = "stock.rule"

    @api.model
    def _run_buy(self, procurements):
        procurements_by_po_domain = defaultdict(list)
        errors = []
        for procurement, rule in procurements:
            # Get the schedule date in order to find a valid seller
            procurement_date_planned = fields.Datetime.from_string(procurement.values['date_planned'])

            supplier = False
            company_id = rule.company_id or procurement.company_id
            if procurement.values.get('supplierinfo_id'):
                supplier = procurement.values['supplierinfo_id']
            elif procurement.values.get('orderpoint_id') and procurement.values['orderpoint_id'].supplier_id:
                supplier = procurement.values['orderpoint_id'].supplier_id
            else:
                supplier = procurement.product_id.with_company(company_id.id)._select_seller(
                    partner_id=self._get_partner_id(procurement.values, rule),
                    quantity=procurement.product_qty,
                    date=max(procurement_date_planned.date(), fields.Date.today()),
                    uom_id=procurement.product_uom)

            # Fall back on a supplier for which no price may be defined. Not ideal, but better than
            # blocking the user.
            supplier = supplier or procurement.product_id._prepare_sellers(False).filtered(
                lambda s: not s.company_id or s.company_id == company_id
            )[:1]

            if not supplier:
                msg = _(
                    'There is no matching vendor price to generate the purchase order for product %s (no vendor defined, minimum quantity not reached, dates not valid, ...). Go on the product form and complete the list of vendors.',
                    procurement.product_id.display_name)
                errors.append((procurement, msg))

            partner = supplier.partner_id
            # we put `supplier_info` in values for extensibility purposes
            procurement.values['supplier'] = supplier
            procurement.values['propagate_cancel'] = rule.propagate_cancel
            procurement.values['product_id'] = procurement.product_id

            # Add product category to the PO domain
            domain = rule._make_po_get_domain(company_id, procurement.values, partner)

            procurements_by_po_domain[tuple(domain)].append((procurement, rule))

        if errors:
            raise ProcurementException(errors)

        for domain, procurements_rules in procurements_by_po_domain.items():
            procurements, rules = zip(*procurements_rules)

            origins = set([p.origin for p in procurements if p.origin])
            po = self.env['purchase.order'].sudo().search(list(domain), limit=1)
            company_id = rules[0].company_id or procurements[0].company_id
            if not po:
                positive_values = [p.values for p in procurements if
                                   float_compare(p.product_qty, 0.0, precision_rounding=p.product_uom.rounding) >= 0]
                if positive_values:
                    vals = rules[0]._prepare_purchase_order(company_id, origins, positive_values)
                    # 🔹 Store category on PO
                    vals['product_categ_id'] = procurements[0].product_id.categ_id.id
                    po = self.env['purchase.order'].with_company(company_id).with_user(SUPERUSER_ID).create(vals)
            else:
                if po.origin:
                    missing_origins = origins - set(po.origin.split(', '))
                    if missing_origins:
                        po.write({'origin': po.origin + ', ' + ', '.join(missing_origins)})
                else:
                    po.write({'origin': ', '.join(origins)})

            procurements_to_merge = self._get_procurements_to_merge(procurements)
            procurements = self._merge_procurements(procurements_to_merge)

            #Group PO lines by product + category
            po_lines_by_key = {}
            grouped_po_lines = groupby(
                po.order_line.filtered(lambda l: not l.display_type and l.product_uom == l.product_id.uom_po_id),
                key=lambda l: (l.product_id.id, l.product_id.categ_id.id)
            )
            for key, po_lines in grouped_po_lines:
                po_lines_by_key[key] = self.env['purchase.order.line'].concat(*po_lines)

            po_line_values = []
            for procurement in procurements:
                key = (procurement.product_id.id, procurement.product_id.categ_id.id)
                po_lines = po_lines_by_key.get(key, self.env['purchase.order.line'])
                po_line = po_lines._find_candidate(*procurement)

                if po_line:
                    vals = self._update_purchase_order_line(procurement.product_id,
                                                            procurement.product_qty, procurement.product_uom,
                                                            company_id,
                                                            procurement.values, po_line)
                    po_line.sudo().write(vals)
                else:
                    if float_compare(procurement.product_qty, 0,
                                     precision_rounding=procurement.product_uom.rounding) <= 0:
                        continue
                    partner = procurement.values['supplier'].partner_id
                    po_line_values.append(self.env['purchase.order.line']._prepare_purchase_order_line_from_procurement(
                        *procurement, po))
                    order_date_planned = procurement.values['date_planned'] - relativedelta(
                        days=procurement.values['supplier'].delay)
                    if fields.Date.to_date(order_date_planned) < fields.Date.to_date(po.date_order):
                        po.date_order = order_date_planned
            self.env['purchase.order.line'].sudo().create(po_line_values)

    def _prepare_purchase_order(self, company_id, origins, values):
        vals = super()._prepare_purchase_order(company_id, origins, values)

        first_value = values[0] if isinstance(values, list) else values
        product = first_value.get('product_id') if first_value else False

        if product:
            vals['product_categ_id'] = product.categ_id.id

        return vals


    def _make_po_get_domain(self, company_id, values, partner):
        domain = super()._make_po_get_domain(company_id, values, partner)
        product = values.get('product_id')
        print("product",product)
        if product:
            domain += (('product_categ_id', '=', product.categ_id.id),)

        return domain


#
#     def _run_buy(self, procurements):
#         # Call original
#         res = super()._run_buy(procurements)
#         # Update PO lines created from MPS
#         for procurement, rule in procurements:
#             if procurement.origin and "MPS" in procurement.origin:
#                 po_lines = self.env['purchase.order.line'].search([('order_id.origin', '=', procurement.origin)])
#                 po_lines.write({'from_mps': True})
#         return res

