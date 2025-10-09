# -*- coding: utf-8 -*-
import re
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied


class ABCLStockController(http.Controller):


    @http.route(['/delivery_order_list/', '/delivery_order/<string:do_id>', '/delivery_order/<int:do_id>'],
                auth='user', methods=['GET', 'POST'], website=True, csrf=True)
    def handle_delivery_orders(self, do_id=None, **kw):
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('work_contact_id', '=', user.partner_id.id)], limit=1)
        if not employee:
            raise AccessDenied()

        method = request.httprequest.method
        template_context = {'page_name': 'delivery_order_form'}
        template = 'abcl_stock.delivery_order_template'

        company = request.env.company
        warehouse = request.env['stock.warehouse'].sudo().search([('company_id', '=', company.id)], limit=1)
        picking_type_id = warehouse.out_type_id or request.env.ref('stock.picking_type_out')
        default_location = picking_type_id.default_location_src_id

        if method == "GET":
            if not do_id:
                template = 'abcl_stock.delivery_order_list_template'
                template_context['delivery_orders'] = request.env['stock.picking'].sudo().search(
                    [('picking_type_id.code', '=', 'outgoing'), ('create_uid', '=', user.id)])
            elif isinstance(do_id, int):
                delivery_order = request.env['stock.picking'].sudo().browse(do_id).exists()
                if not delivery_order:
                    return request.not_found()
                template_context.update({
                    'record': delivery_order,
                    'product_data': self.get_product_data(),
                })
            else:
                template_context.update({
                    'record': None,
                    'product_data': self.get_product_data(),
                    'operation_types': picking_type_id,
                    'location_id': default_location,
                })

            return request.render(template, template_context)

        elif method == "POST":
            product_data = self.get_product_data()
            product_names = {data['id']: data['display_name'] for data in product_data}

            do_line_ids = [re.search(r'\d+', key).group(0) for key in kw.keys() if key.startswith('product_id_')]
            move_lines = []

            for line_id in do_line_ids:
                product_id = int(kw[f'product_id_{line_id}'])
                product = request.env['product.product'].sudo().browse(product_id)
                move_lines.append((0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': float(kw[f'product_qty_{line_id}']),
                    'name': product_names[product.id],
                    'product_uom': product.uom_id.id,
                }))

            values = {
                'picking_type_id': picking_type_id.id,
                'location_id': default_location.id,
                'move_ids_without_package': [(5, 0, 0)] + move_lines,
                'purpose':kw['purpose'],
                'requested_user_id': request.env.user.id
            }

            if isinstance(do_id, int):
                delivery_order = request.env['stock.picking'].sudo().browse(do_id).exists()
                if not delivery_order:
                    return request.not_found()
                if delivery_order.state not in ['done', 'cancel']:
                    delivery_order.write(values)
            else:
                delivery_order = request.env['stock.picking'].sudo().create(values)
                responsible_user = warehouse.responsible_user_id
                if responsible_user:
                    delivery_order.activity_schedule(
                        'abcl_stock.abcl_stock_mail_act_delivery_order_approval',
                        user_id=responsible_user.id,
                        note=f'New Delivery Order {delivery_order.name} has been created and requires your action.',
                    )

                    template = request.env.ref('abcl_stock.abcl_delivery_order_approval_mail_template')
                    if template and responsible_user.partner_id.email:
                        template.send_mail(delivery_order.id, email_values={
                            'email_to': responsible_user.partner_id.email,
                        })

            return request.render('abcl_stock.delivery_order_template', {
                'record': delivery_order,
                'page_name': 'delivery_order_form',
                'product_data': self.get_product_data(),
                'operation_types': picking_type_id,
                'location_id': default_location,
            })

    @http.route('/delivery_order/get_product_data', type='json', auth='user')
    def get_product_data(self):
        products = request.env['product.product'].sudo().search_read(
            domain=[('type', '=', 'consu'), ('sale_ok', '=', True)],
            fields=['id', 'display_name', 'uom_id'],
            limit=100
        )

        product_data = [{
            'id': product['id'],
            'display_name': product['display_name'],
            'uom_name': product['uom_id'][1] if product['uom_id'] else ''
        } for product in products]


        return product_data

