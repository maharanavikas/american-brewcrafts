# -*- coding: utf-8 -*-
import re
from odoo import _
from odoo.http import request, Controller, route
from odoo.exceptions import AccessDenied
from odoo.addons.portal.controllers.portal import CustomerPortal, pager


class ABCLPurchaseController(Controller):


    @route(['/purchase_order_list/', '/purchase_order/<string:po_id>', '/purchase_order/<int:po_id>'],
           auth='user', methods=['GET', 'POST'], website=True, csrf=True)
    def handle_purchase_orders(self, po_id=None, **kw):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            raise request.not_found()
        method = request.httprequest.method

        if method == "GET":
            template_context = {'page_name': 'purchase_order_form'}
            template = 'abcl_purchase.purchase_order_create_template'

            if not po_id:
                template = 'abcl_purchase.purchase_order_list_template'
                template_context['purchase_orders'] = request.env['purchase.order'].sudo().search(
                    [('create_uid', '=', user.id)])
            elif isinstance(po_id, int):
                purchase_order = request.env['purchase.order'].sudo().browse(po_id).exists()
                if not purchase_order:
                    return request.not_found()

                template_context.update({
                    'record': purchase_order,
                    'vendor_data': self.get_vendor_products(),
                    'category_data': request.env['product.category'].search_read(
                        domain=[('enable_internal_po', '=', True)], fields=['id', 'name']
                    ),
                })
            return request.render(template, template_context)


        elif method == "POST":
            vendor_data = self.get_vendor_products()
            product_names = {data['product_id']: data['product_name'] for data in vendor_data}
            po_line_ids = [re.search(r'\d+', key).group(0) for key in kw.keys() if key.startswith('product_id_')]
            po_lines = []
            product_categ_id = False

            for line_id in po_line_ids:

                product_id = int(kw[f'product_id_{line_id}'])
                product = request.env['product.product'].sudo().browse(product_id)
                if product.exists():
                    product_categ_id = product.categ_id.id
                po_lines.append(
                    [0, 0, {
                        'product_id': product_id,
                        'product_qty': kw[f'product_qty_{line_id}'],
                        'name': product_names.get(product_id, product.display_name)
                    }]
                )

            if isinstance(po_id, int):
                purchase_order = request.env['purchase.order'].sudo().browse(po_id).exists()

                if not purchase_order:
                    return request.not_found()
                if purchase_order.state not in ['purchase', 'done']:
                    purchase_order.write({
                        'partner_id': int(kw['partner_id']),
                        'reason': kw['reason'],
                        'product_categ_id': product_categ_id,
                        'order_line': [[5, 0, 0]] + po_lines
                    })
            else:
                purchase_order = request.env['purchase.order'].sudo().create({
                    'partner_id': int(kw.get('partner_id')),
                    'reason': kw['reason'],
                    'product_categ_id': product_categ_id,
                    'order_line': po_lines
                })

            return request.redirect(f"/purchase_order/{purchase_order.id}")

    # @route(['/purchase_order_list/', '/purchase_order/<string:po_id>', '/purchase_order/<int:po_id>'],
    #        auth='user', methods=['GET', 'POST'], website=True, csrf=True)
    # def handle_purchase_orders(self, po_id=None, **kw):
    #     user = request.env.user
    #     employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
    #     if not employee:
    #         raise request.not_found()
    #     method = request.httprequest.method
    #
    #     if method == "GET":
    #         template_context = {'page_name': 'purchase_order_form'}
    #         template = 'abcl_purchase.purchase_order_create_template'
    #
    #         if not po_id:
    #             template = 'abcl_purchase.purchase_order_list_template'
    #             template_context['purchase_orders'] = request.env['purchase.order'].sudo().search(
    #                 [('create_uid', '=', user.id)])
    #
    #         elif isinstance(po_id, int):
    #             purchase_order = request.env['purchase.order'].sudo().browse(po_id).exists()
    #             if not purchase_order:
    #                 return request.not_found()
    #
    #             template_context.update({
    #                 'record': purchase_order,
    #                 'vendor_data': self.get_vendor_products(purchase_order.product_categ_id.id),
    #                 'category_data': request.env['product.category'].search_read(
    #                     domain=[('enable_internal_po', '=', True)], fields=['id', 'name']
    #                 ),
    #             })
    #
    #         return request.render(template, template_context)
    #
    #     elif method == "POST":
    #         vendor_data = self.get_vendor_products()
    #         product_names = {
    #             data['product_id']: data['name'] for vendor in vendor_data for data in vendor['product_ids']
    #         }
    #
    #         po_line_ids = [re.search(r'\d+', key).group(0) for key in kw.keys() if key.startswith('product_id_')]
    #         po_lines = []
    #         for line_id in po_line_ids:
    #             po_lines.append(
    #                 [0, 0, {
    #                     'product_id': int(kw[f'product_id_{line_id}']),
    #                     'product_qty': kw[f'product_qty_{line_id}'],
    #                     'name': product_names[int(kw[f'product_id_{line_id}'])]
    #                 }]
    #             )
    #
    #         if isinstance(po_id, int):
    #             purchase_order = request.env['purchase.order'].sudo().browse(po_id).exists()
    #             if not purchase_order:
    #                 return request.not_found()
    #
    #             if purchase_order.state not in ['purchase', 'done']:
    #                 purchase_order.write({
    #                     **{
    #                         'partner_id': int(kw['partner_id']),
    #                         'reason': kw['reason'],
    #                         'product_categ_id': int(kw['product_category_id']),
    #                     },
    #                     **{'order_line': [[5, 0, 0, ]] + po_lines}
    #                 })
    #         else:
    #             # create a new purchase order record
    #             purchase_order = request.env['purchase.order'].sudo().create({
    #                 'partner_id': int(kw.get('partner_id')),
    #                 'reason': kw['reason'],
    #                 'product_categ_id': int(kw['product_category_id']),
    #                 **{'order_line': po_lines}
    #             })
    #         return request.redirect(f"/purchase_order/{purchase_order.id}")

    @route('/purchase_order/<int:order_id>/send_for_approval', type='http', auth="user", website=True)
    def purchase_order_send_for_approval(self, order_id, **post):
        order = request.env['purchase.order'].sudo().browse(order_id)
        if order and order.state == 'draft':
            order.action_generate_approval_lines()
            request.session['success_message'] = "Purchase order sent for approval successfully."

        return request.redirect('/purchase_order/' + str(order_id))


    @route('/purchase_order/get_products_list', type='json', auth='user')
    def get_vendor_products(self, category_id=False):
        domain = [("categ_id.enable_internal_po", "=", True)]
        if category_id:
            domain.append(("categ_id", "=", category_id))

        products = request.env["product.product"].sudo().search(domain)
        return [{
            "product_id": p.id,
            "product_name": p.name,
            "uom_name": p.uom_id.name,
            "category_id": p.categ_id.id or False,
            "vendors": [{
                "partner_id": s.partner_id.id,
                "partner_name": s.partner_id.name
            } for s in p.seller_ids]
        } for p in products]

    # @route('/purchase_order/get_products_list', type='json', auth='user')
    # def get_vendor_products(self, category_id=False):
    #     domain = [("product_id.categ_id.enable_internal_po", "=", True)]
    #     if category_id:
    #         domain.append(('product_id.categ_id', '=', category_id))
    #     products_grouped = request.env['product.supplierinfo'].sudo().search_fetch(
    #         domain=domain,
    #         field_names=['partner_id', 'product_id']
    #     ).grouped('partner_id')
    #     return [{
    #         'partner_id': partner.id,
    #         'partner_name': partner.name,
    #         'product_ids': [{
    #             'product_id': product.id,
    #             'name': product.name,
    #             'uom_name': product.uom_id.name,
    #             'category_id': product.categ_id.id or False
    #         } for product in products_grouped[partner].product_id]
    #     } for partner in products_grouped]

