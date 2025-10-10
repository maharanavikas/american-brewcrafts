# -*- coding: utf-8 -*-

from datetime import datetime
from odoo.fields import Date, Datetime
import re
import base64
from odoo.exceptions import AccessDenied
from odoo.http import request, route, Controller


def validate_access_token(func):
    def wrapper(object, access_token, *args, **kwargs):
        print("access_token ---->", access_token)
        picking = request.env['stock.picking'].sudo()._validate_access_token(access_token)
        print("picking --->", picking)
        if not picking:
            return request.not_found()
        if picking.dispatch_signature and picking.accountant_signature:
            return request.render('abcl_sale.dispatch_checklist_locked', {
                    'picking': picking,
                    'message': "This dispatch checklist has already been signed by both Dispatch and Accountant. Access denied."
                })
        return func(object, picking, *args, **kwargs)
    return wrapper

class DispatchChecklistController(Controller):
    @route('/dispatch_checklist/<string:access_token>',type='http', methods=["GET", "POST"], auth='public', website=True)
    @validate_access_token
    def dispatch_checklist(self, picking, **kw):
        method = request.httprequest.method

        products = picking.move_ids_without_package.product_id
        vehicles = request.env['fleet.vehicle'].sudo().search([])

        user = request.env.user.sudo()
        is_public = user._is_public()
        is_dispatch_user = (not is_public) and bool(picking.user_id and user.id == picking.user_id.id)
        is_accountant_user = (not is_public) and bool(getattr(picking, 'finance_user_id', False) and user.id == picking.finance_user_id.id)

        if method == 'GET':
            return request.render('abcl_sale.dispatch_checklist_template', {'picking':picking, 
                                                                            'products': products, 
                                                                            'vehicles': vehicles, 
                                                                            'access_token': picking.access_token,
                                                                            'is_dispatch_user': is_dispatch_user,
                                                                            'is_accountant_user': is_accountant_user
                                                                            })
        elif method == 'POST':
            vehicle_type = kw.get("vehicle_type", '')
            print("vehicle_type --->", vehicle_type)
            vehicle_no = ''

            dispatch_wizard = request.env['dispatch.checklist.wizard'].sudo().search([])

            if vehicle_type == 'internal':
                vehicle_id = kw.get("select_vehicle_name")
                if vehicle_id:
                    veh = request.env['fleet.vehicle'].sudo().browse(int(vehicle_id))
                    vehicle_no = veh.license_plate or veh.name or ''
            elif vehicle_type == 'external':
                vehicle_no = kw.get("enter_vehicle_details", '')

            answer_values ={
                'dispatch_date': kw.get("dispatch_date", ''),
                'vehicle_type': vehicle_type,
                'vehicle_no': vehicle_no,
                'gp_p_no_date': kw.get("gp_p_no_date_specifications", ''),
                'gp_p_no_date_remarks': kw.get("gp_p_no_date_remarks", ''),
                'gp_p_no_date_status': kw.get("gp_p_no_date_check", False),
                'gp_party_name': kw.get("gp_party_name_specifications", ''),
                'gp_party_name_remarks': kw.get("gp_party_name_remarks", ''),
                'gp_party_name_status': kw.get("gp_party_name_check", False),
                'gp_pack_size': kw.get("gp_pack_size_specifications", ''),
                'gp_pack_size_remarks': kw.get("gp_pack_size_remarks", ''),
                'gp_pack_size_status': kw.get("gp_pack_size_check", False),
                'gp_quantity': kw.get("gp_quantity_specifications", ''),
                'gp_quantity_remarks': kw.get("gp_quantity_remarks", ''),
                'gp_quantity_status': kw.get("gp_quantity_check", False),
                'gp_brand': kw.get("gp_brand_specifications", ''),
                'gp_brand_remarks': kw.get("gp_brand_remarks", ''),
                'gp_brand_status': kw.get("gp_brand_check", False),
                'gp_vehicle_no_date': kw.get("gp_vehicle_no_date_specifications", ''),
                'gp_vehicle_no_date_remarks': kw.get("gp_vehicle_no_date_remarks", ''),
                'gp_vehicle_no_date_status': kw.get("gp_vehicle_no_date_check", False),
                'lrc_lr_no': kw.get("lrc_lr_no_specifications", ''),
                'lrc_lr_no_remarks': kw.get("lrc_lr_no_remarks", ''),
                'lrc_lr_no_status': kw.get("lrc_lr_no_check", False),
                'lrc_lr_date': kw.get("lrc_lr_date_specifications", ''),
                'lrc_lr_date_remarks': kw.get("lrc_lr_date_remarks", ''),
                'lrc_lr_date_status': kw.get("lrc_lr_date_check", False),
                'lrc_lr_vehicle_no_address': kw.get("lrc_lr_vehicle_no_address_specifications", ''),
                'lrc_lr_vehicle_no_address_remarks': kw.get("lrc_lr_vehicle_no_address_remarks", ''),
                'lrc_lr_vehicle_no_address_status': kw.get("lrc_lr_vehicle_no_address_check", False),
                'lrc_lr_quantity': kw.get("lrc_lr_quantity_specifications", ''),
                'lrc_lr_quantity_remarks': kw.get("lrc_lr_quantity_remarks", ''),
                'lrc_lr_quantity_status': kw.get("lrc_lr_quantity_check", False),
                'lrc_lr_invoice_no_date': kw.get("lrc_lr_invoice_no_date_specifications", ''),
                'lrc_lr_invoice_no_date_remarks': kw.get("lrc_lr_invoice_no_date_remarks", ''),
                'lrc_lr_invoice_no_date_status': kw.get("lrc_lr_invoice_no_date_check", False),
                'tp_date': kw.get("tp_date_specifications", ''),
                'tp_date_remarks': kw.get("tp_date_remarks", ''),
                'tp_date_status': kw.get("tp_date_check", False),
                'tp_brand': kw.get("tp_brand_specifications", ''),
                'tp_brand_remarks': kw.get("tp_brand_remarks", ''),
                'tp_brand_status': kw.get("tp_brand_check", False),
                'tp_batch_no': kw.get("tp_batch_no_specifications", ''),
                'tp_batch_no_remarks': kw.get("tp_batch_no_remarks", ''),
                'tp_batch_no_status': kw.get("tp_batch_no_check", False),
                'tp_po_no_date': kw.get("tp_po_no_date_specifications", ''),
                'tp_po_no_date_remarks': kw.get("tp_po_no_date_remarks", ''),
                'tp_po_no_date_status': kw.get("tp_po_no_date_check", False),
                'tp_quantity': kw.get("tp_quantity_specifications", ''),
                'tp_quantity_remarks': kw.get("tp_quantity_remarks", ''),
                'tp_quantity_status': kw.get("tp_quantity_check", False),
                'tp_pack_size': kw.get("tp_pack_size_specifications", ''),
                'tp_pack_size_remarks': kw.get("tp_pack_size_remarks", ''),
                'tp_pack_size_status': kw.get("tp_pack_size_check", False),
                'tp_bulk_litre': kw.get("tp_bulk_litre_specifications", ''),
                'tp_bulk_litre_remarks': kw.get("tp_bulk_litre_remarks", ''),
                'tp_bulk_litre_status': kw.get("tp_bulk_litre_check", False),
                'tp_alcohol_percent': kw.get("tp_alcohol_percent_specifications", ''),
                'tp_alcohol_percent_remarks': kw.get("tp_alcohol_percent_remarks", ''),
                'tp_alcohol_percent_status': kw.get("tp_alcohol_percent_check", False),
                'tp_excise_duty_challan_no_date': kw.get("tp_excise_duty_challan_no_date_specifications", ''),
                'tp_excise_duty_challan_no_date_remarks': kw.get("tp_excise_duty_challan_no_date_remarks", ''),
                'tp_excise_duty_challan_no_date_status': kw.get("tp_excise_duty_challan_no_date_check", False),
                'tp_excise_duty': kw.get("tp_excise_duty_specifications", ''),
                'tp_excise_duty_remarks': kw.get("tp_excise_duty_remarks", ''),
                'tp_excise_duty_status': kw.get("tp_excise_duty_check", False),
                'tp_depot': kw.get("tp_depot_specifications", ''),
                'tp_depot_remarks': kw.get("tp_depot_name_remarks", ''),
                'tp_depot_status': kw.get("tp_depot_check", False),
                'tp_vehicle_route': kw.get("tp_vehicle_route_specifications", ''),
                'tp_vehicle_route_remarks': kw.get("tp_vehicle_route_remarks", ''),
                'tp_vehicle_route_status': kw.get("tp_vehicle_route_check", False),
                'tp_permit_validity_date': kw.get("tp_permit_validity_date_specifications", ''),
                'tp_permit_validity_date_remarks': kw.get("tp_permit_validity_date_remarks", ''),
                'tp_permit_validity_date_status': kw.get("tp_permit_validity_date_check", False),
                'e_pass_permit_no': kw.get("e_pass_permit_no_specifications", ''),
                'e_pass_permit_no_remarks': kw.get("e_pass_permit_no_remarks", ''),
                'e_pass_permit_no_status': kw.get("e_pass_permit_no_check", False),
                'e_pass_dispatch_date_time': kw.get("e_pass_dispatch_date_time_specifications", ''),
                'e_pass_dispatch_date_time_remarks': kw.get("e_pass_dispatch_date_time_remarks", ''),
                'e_pass_dispatch_date_time_status': kw.get("e_pass_dispatch_date_time_check", False),
                'e_pass_import_validity': kw.get("e_pass_import_validity_specifications", ''),
                'e_pass_import_validity_remarks': kw.get("e_pass_import_validity_remarks", ''),
                'e_pass_import_validity_status': kw.get("e_pass_import_validity_check", False),
                'e_pass_quantity': kw.get("e_pass_quantity_specifications", ''),
                'e_pass_quantity_remarks': kw.get("e_pass_quantity_remarks", ''),
                'e_pass_quantity_status': kw.get("e_pass_quantity_check", False),
                'e_pass_brand': kw.get("e_pass_brand_specifications", ''),
                'e_pass_brand_remarks': kw.get("e_pass_brand_remarks", ''),
                'e_pass_brand_status': kw.get("e_pass_brand_check", False),
                'e_pass_size': kw.get("e_pass_size_specifications", ''),
                'e_pass_size_remarks': kw.get("e_pass_size_remarks", ''),
                'e_pass_size_status': kw.get("e_pass_size_check", False),
                'e_pass_alcohol_strength': kw.get("e_pass_alcohol_strength_specifications", ''),
                'e_pass_alcohol_strength_remarks': kw.get("e_pass_alcohol_strength_remarks", ''),
                'e_pass_alcohol_strength_status': kw.get("e_pass_alcohol_strength_check", False),
                'e_pass_route_validity': kw.get("e_pass_route_validity_specifications", ''),
                'e_pass_route_validity_remarks': kw.get("e_pass_route_validity_remarks", ''),
                'e_pass_route_validity_status': kw.get("e_pass_route_validity_check", False),
                'evc_quantity': kw.get("evc_quantity_specifications", ''),
                'evc_quantity_remarks': kw.get("evc_quantity_remarks", ''),
                'evc_quantity_status': kw.get("evc_quantity_check", False),
                'evc_brand': kw.get("evc_brand_specifications", ''),
                'evc_brand_remarks': kw.get("evc_brand_remarks", ''),
                'evc_brand_status': kw.get("evc_brand_check", False),
                'evc_export_permit_no_date': kw.get("evc_export_permit_no_date_specifications", ''),
                'evc_export_permit_no_date_remarks': kw.get("evc_export_permit_no_date_remarks", ''),
                'evc_export_permit_no_date_status': kw.get("evc_export_permit_no_date_check", False),
                'evc_import_permit_no_date': kw.get("evc_import_permit_no_date_specifications", ''),
                'evc_import_permit_no_date_remarks': kw.get("evc_import_permit_no_date_remarks", ''),
                'evc_import_permit_no_date_status': kw.get("evc_import_permit_no_date_check", False),
                'evc_tp_no_date': kw.get("evc_tp_no_date_specifications", ''),
                'evc_tp_no_date_remarks': kw.get("evc_tp_no_date_remarks", ''),
                'evc_tp_no_date_status': kw.get("evc_tp_no_date_check", False),
                'evc_vehicle_no': kw.get("evc_vehicle_no_specifications", ''),
                'evc_vehicle_no_remarks': kw.get("evc_vehicle_no_remarks", ''),
                'evc_vehicle_no_status': kw.get("evc_vehicle_no_check", False),
                'e_permit_ofs_no_date': kw.get("e_permit_ofs_no_date_specifications", ''),
                'e_permit_ofs_no_date_remarks': kw.get("e_permit_ofs_no_date_remarks", ''),
                'e_permit_ofs_no_date_status': kw.get("e_permit_ofs_no_date_check", False),
                'e_permit_lr_copy_no_date': kw.get("e_permit_lr_copy_no_date_specifications", ''),
                'e_permit_lr_copy_no_date_remarks': kw.get("e_permit_lr_copy_no_date_remarks", ''),
                'e_permit_lr_copy_no_date_status': kw.get("e_permit_lr_copy_no_date_check", False),
                'e_permit_vehicle_no': kw.get("e_permit_vehicle_no_specifications", ''),
                'e_permit_vehicle_no_remarks': kw.get("e_permit_vehicle_no_remarks", ''),
                'e_permit_vehicle_no_status': kw.get("e_permit_vehicle_no_check", False),
                'e_permit_deport_name': kw.get("e_permit_deport_name_specifications", ''),
                'e_permit_deport_name_remarks': kw.get("e_permit_deport_name_remarks", ''),
                'e_permit_deport_name_status': kw.get("e_permit_deport_name_check", False),
                'e_permit_brand': kw.get("e_permit_brand_specifications", ''),
                'e_permit_brand_remarks': kw.get("e_permit_brand_remarks", ''),
                'e_permit_brand_status': kw.get("e_permit_brand_check", False),
                'e_permit_batch_qty_size': kw.get("e_permit_batch_qty_size_specifications", ''),
                'e_permit_batch_qty_size_remarks': kw.get("e_permit_batch_qty_size_remarks", ''),
                'e_permit_batch_qty_size_status': kw.get("e_permit_batch_qty_size_check", False),
                'e_permit_no': kw.get("e_permit_no_specifications", ''),
                'e_permit_no_remarks': kw.get("e_permit_no_remarks", ''),
                'e_permit_no_status': kw.get("e_permit_no_check", False),
                'i_permit_no_date': kw.get("i_permit_no_date_specifications", ''),
                'i_permit_no_date_remarks': kw.get("i_permit_no_date_remarks", ''),
                'i_permit_no_date_status': kw.get("i_permit_no_date_check", False),
                'i_permit_validity': kw.get("i_permit_validity_specifications", ''),
                'i_permit_validity_remarks': kw.get("i_permit_validity_remarks", ''),
                'i_permit_validity_status': kw.get("i_permit_validity_check", False),
                'i_permit_brand': kw.get("i_permit_brand_specifications", ''),
                'i_permit_brand_remarks': kw.get("i_permit_brand_remarks", ''),
                'i_permit_brand_status': kw.get("i_permit_brand_check", False),
                'i_permit_size': kw.get("i_permit_size_specifications", ''),
                'i_permit_size_remarks': kw.get("i_permit_size_remarks", ''),
                'i_permit_size_status': kw.get("i_permit_size_check", False),
                'i_permit_qty_sign_stamp': kw.get("i_permit_qty_sign_stamp_specifications", ''),
                'i_permit_qty_sign_stamp_remarks': kw.get("i_permit_qty_sign_stamp_remarks", ''),
                'i_permit_qty_sign_stamp_status': kw.get("i_permit_qty_sign_stamp_check", False),
                'invoice_no_date': kw.get("invoice_no_date_specifications", ''),
                'invoice_no_date_remarks': kw.get("invoice_no_date_remarks", ''),
                'invoice_no_date_status': kw.get("invoice_no_date_check", False),
                'invoice_gate_pass_date': kw.get("invoice_gate_pass_date_specifications", ''),
                'invoice_gate_pass_date_remarks': kw.get("invoice_gate_pass_date_remarks", ''),
                'invoice_gate_pass_date_status': kw.get("invoice_gate_pass_date_check", False),
                'invoice_transport': kw.get("invoice_transport_specifications", ''),
                'invoice_transport_remarks': kw.get("invoice_transport_remarks", ''),
                'invoice_transport_status': kw.get("invoice_transport_check", False),
                'invoice_vehicle_no': kw.get("invoice_vehicle_no_specifications", ''),
                'invoice_vehicle_no_remarks': kw.get("invoice_vehicle_no_remarks", ''),
                'invoice_vehicle_no_status': kw.get("invoice_vehicle_no_check", False),
                'invoice_tp_lr_no': kw.get("invoice_tp_lr_no_specifications", ''),
                'invoice_tp_lr_no_remarks': kw.get("invoice_tp_lr_no_remarks", ''),
                'invoice_tp_lr_no_status': kw.get("invoice_tp_lr_no_check", False),
                'invoice_ofs_no_date': kw.get("invoice_ofs_no_date_specifications", ''),
                'invoice_ofs_no_date_remarks': kw.get("invoice_ofs_no_date_remarks", ''),
                'invoice_ofs_no_date_status': kw.get("invoice_ofs_no_date_check", False),
                'invoice_brand': kw.get("invoice_brand_specifications", ''),
                'invoice_brand_remarks': kw.get("invoice_brand_remarks", ''),
                'invoice_brand_status': kw.get("invoice_brand_check", False),
                'invoice_batch_no': kw.get("invoice_batch_no_specifications", ''),
                'invoice_batch_no_remarks': kw.get("invoice_batch_no_remarks", ''),
                'invoice_batch_no_status': kw.get("invoice_batch_no_check", False),
                'invoice_quantity': kw.get("invoice_quantity_specifications", ''),
                'invoice_quantity_remarks': kw.get("invoice_quantity_remarks", ''),
                'invoice_quantity_status': kw.get("invoice_quantity_check", False),
                'invoice_basic_price': kw.get("invoice_basic_price_specifications", ''),
                'invoice_basic_price_remarks': kw.get("invoice_basic_price_remarks", ''),
                'invoice_basic_price_status': kw.get("invoice_basic_price_check", False),
                'inovice_excise_duty': kw.get("inovice_excise_duty_specifications", ''),
                'inovice_excise_duty_remarks': kw.get("inovice_excise_duty_remarks", ''),
                'inovice_excise_duty_status': kw.get("inovice_excise_duty_check", False),
                'inovice_liter_total_value': kw.get("inovice_liter_total_value_specifications", ''),
                'inovice_liter_total_value_remarks': kw.get("inovice_liter_total_value_remarks", ''),
                'inovice_liter_total_value_status': kw.get("inovice_liter_total_value_check", False),
                'rp_doc_availability': kw.get("rp_doc_availability_specifications", ''),
                'rp_doc_availability_remarks': kw.get("rp_doc_availability_remarks", ''),
                'rp_doc_availability_status': kw.get("rp_doc_availability_check", False),
                'dn_brand': kw.get("dn_brand_specifications", ''),
                'dn_brand_remarks': kw.get("dn_brand_remarks", ''),
                'dn_brand_status': kw.get("dn_brand_check", False),
                'dn_size': kw.get("dn_size_specifications", ''),
                'dn_size_remarks': kw.get("dn_size_remarks", ''),
                'dn_size_status': kw.get("dn_size_check", False),
                'dn_qty': kw.get("dn_qty_specifications", ''),
                'dn_qty_remarks': kw.get("dn_qty_remarks", ''),
                'dn_qty_status': kw.get("dn_qty_check", False),
                'dn_depot_name': kw.get("dn_depot_name_specifications", ''),
                'dn_depot_name_remarks': kw.get("dn_depot_name_remarks", ''),
                'dn_depot_name_status': kw.get("dn_depot_name_check", False),
                'dn_permit_no': kw.get("dn_permit_no_specifications", ''),
                'dn_permit_no_remarks': kw.get("dn_permit_no_remarks", ''),
                'dn_permit_no_status': kw.get("dn_permit_no_check", False),
                'dn_transportor_add': kw.get("dn_transportor_add_specifications", ''),
                'dn_transportor_add_remarks': kw.get("dn_transportor_add_remarks", ''),
                'dn_transportor_add_status': kw.get("dn_transportor_add_check", False),
                'dn_vehicle_godown_add': kw.get("dn_vehicle_godown_add_specifications", ''),
                'dn_vehicle_godown_add_remarks': kw.get("dn_vehicle_godown_add_remarks", ''),
                'dn_vehicle_godown_add_status': kw.get("dn_vehicle_godown_add_check", False),
                'uc_brand': kw.get("uc_brand_specifications", ''),
                'uc_brand_remarks': kw.get("uc_brand_remarks", ''),
                'uc_brand_status': kw.get("uc_brand_check", False),
                'uc_qty_depot': kw.get("uc_qty_depot_specifications", ''),
                'uc_qty_depot_remarks': kw.get("uc_qty_depot_remarks", ''),
                'uc_qty_depot_status': kw.get("uc_qty_depot_check", False),
                'br_availability': kw.get("br_availability_specifications", ''),
                'br_availability_remarks': kw.get("br_availability_remarks", ''),
                'br_availability_status': kw.get("br_availability_check", False),
            }
            picking.write(answer_values)

            move_ids = [int(k.split('_')[-1]) for k in kw.keys() if k.startswith('ml_remark_')]
            for mid in move_ids:
                status = bool(kw.get(f'ml_check_{mid}'))
                remark = kw.get(f'ml_remark_{mid}', '')
                request.env['stock.move'].sudo().browse(mid).write({
                    'product_status': status,
                    'product_remark': remark,
                })

            return request.redirect(f'/dispatch_checklist_success/{picking.access_token}')

    @route('/dispatch_checklist/<string:access_token>/accept/<string:role>',
           type='json', methods=['POST'], auth='public', website=True, csrf=False)
    @validate_access_token
    def dispatch_accept_signature(self, picking, role, **payload):
        # role is already provided by the route; DON'T overwrite it
        print("HIT:", request.httprequest.path, "role=", role)

        name = (payload.get('name') or '').strip()
        signature = payload.get('signature') or ''
        if not signature:
            return {'success': False, 'error': 'Missing signature'}

        if signature.startswith('data:image'):
            signature = signature.split(',', 1)[1]

        if role == 'dispatch':
            vals = {'dispatch_signed_by': name, 'dispatch_signature': signature, 'dispatch_sign_status': 'signed'}
        elif role == 'accountant':
            vals = {'accountant_signed_by': name, 'accountant_signature': signature, 'accountant_sign_status': 'signed'}
        else:
            return {'success': False, 'error': f'Unknown role: {role}'}
        print('vals --->', vals)

        picking.sudo().write(vals)

        if role == 'dispatch':
            picking._send_accountant_mail() 
        elif role == 'accountant':
            picking.message_post(body="Both dispatch and accountant have signed the dispatch checklist.")
    
        return {'success': True, 'redirect_url': request.httprequest.path.rsplit('/accept', 1)[0]}

        
    @route('/dispatch_checklist_success/<string:access_token>', type='http', methods=["GET"], auth='public', website=True)
    def dispatch_checklist_success(self, access_token):
        picking = request.env['stock.picking'].sudo()._validate_access_token(access_token)
        if not picking:
            return request.not_found()
        return request.render('abcl_sale.dispatch_checklist_success',{'picking': picking})
    
    @route('/andaman_nicobar_dispatch_checklist/',type='http', methods=["GET", "POST"], auth='public', website=True)
    # @validate_access_token
    def andaman_nicobar_dispatch_checklist(self, **kw):
        method = request.httprequest.method

        if method == 'GET':
            return request.render('abcl_sale.andaman_nico_dispatch_checklist_template')
        elif method == 'POST':
            return request.redirect(f'/andaman_nicobar_dispatch_checklist_success/')
        
    @route('/andaman_nicobar_dispatch_checklist_success/<string:access_token>', type='http', methods=["GET"], auth='public', website=True)
    def andaman_nicobar_success(self, access_token):
        pass


    @route('/kerala_dispatch_checklist/',type='http', methods=["GET", "POST"], auth='public', website=True)
    # @validate_access_token
    def kerala_dispatch_checklist(self, **kw):
        method = request.httprequest.method

        if method == 'GET':
            return request.render('abcl_sale.kerala_dispatch_checklist_template')
        elif method == 'POST':
            return request.redirect(f'/kerala_dispatch_checklist_success/')
        
    @route('/kerala_dispatch_checklist_success/<string:access_token>', type='http', methods=["GET"], auth='public', website=True)
    def kerala_dispatch_success(self, access_token):
        pass


    @route('/puducherry_dispatch_checklist/',type='http', methods=["GET", "POST"], auth='public', website=True)
    # @validate_access_token
    def puducherry_dispatch_checklist(self, **kw):
        method = request.httprequest.method

        if method == 'GET':
            return request.render('abcl_sale.puducherry_dispatch_checklist_template')
        elif method == 'POST':
            return request.redirect(f'/puducherry_dispatch_checklist_success/')
        
    @route('/puducherry_dispatch_checklist_success/<string:access_token>', type='http', methods=["GET"], auth='public', website=True)
    def puducherry_dispatch_success(self, access_token):
        pass


    @route('/tamilnadu_dispatch_checklist/',type='http', methods=["GET", "POST"], auth='public', website=True)
    # @validate_access_token
    def tamilnadu_dispatch_checklist(self, **kw):
        method = request.httprequest.method

        if method == 'GET':
            return request.render('abcl_sale.tamilnadu_dispatch_checklist_template')
        elif method == 'POST':
            return request.redirect(f'/tamilnadu_dispatch_checklist_success/')
        
    @route('/tamilnadu_dispatch_checklist_success/<string:access_token>', type='http', methods=["GET"], auth='public', website=True)
    def tamilnadu_dispatch_success(self, access_token):
        pass


    @route('/telangana_dispatch_checklist/',type='http', methods=["GET", "POST"], auth='public', website=True)
    # @validate_access_token
    def telangana_dispatch_checklist(self, **kw):
        method = request.httprequest.method

        if method == 'GET':
            return request.render('abcl_sale.telangana_dispatch_checklist_template')
        elif method == 'POST':
            return request.redirect(f'/telangana_dispatch_checklist_success/')
        
    @route('/telangana_dispatch_checklist_success/<string:access_token>', type='http', methods=["GET"], auth='public', website=True)
    def telangana_dispatch_success(self, access_token):
        pass
