# -*- coding: utf-8 -*-
import base64
from odoo.http import request, Controller, route


class VendorDocumentUpload(Controller):

    @route('/vendor/document_upload', type='http', auth='public', website=True)
    def vendor_document_upload(self, **kwargs):
        token = kwargs.get('t')
        # user = request.env.user
        if not token:
            return "Access Declined."
        partner = request.env['res.partner'].sudo().search([('upload_access_key', '=', token)], limit=1)
        print("partner", partner.name)

        if partner.document_recevied:
            return request.render('abcl_purchase.link_expired', status=404)

        if not partner:
            return "Invalid access key."
        return request.render('abcl_purchase.document_upload_form_template', {'partner': partner , 'token': token})


    @route('/vendor/document_submit', type='http', auth='public', methods=['POST'], website=True, )
    def vendor_form_submit(self, **post):
        token = post.get('token')
        if not token:
            return "Access Declined."
        
        partner = request.env['res.partner'].sudo().search([('upload_access_key', '=', token)], limit=1)
        if not partner:
            return "Invalid access key."
        
        customer_workspace = request.env.ref('abcl_purchase.document_customer_document_folder')
        
        if not customer_workspace:
            print("Not found: ",customer_workspace)
        print("customer_workspace : ", customer_workspace.name)

        # Check if the vendor folder already exists
        existing_vendor_folder = customer_workspace.children_ids.filtered(lambda x: x.partner_id == partner)[0:1]
        if not existing_vendor_folder:
            existing_vendor_folder = request.env['documents.document'].sudo().create({
                'name': partner.name,
                'partner_id': partner.id,
                'type': 'folder',
                'folder_id': customer_workspace.id,
            })
            print("Vendor folder created:", existing_vendor_folder.name)
        
        def save_attachment(partner, file, filename):
            print('document called for field:', filename)
            if file:
                return request.env['documents.document'].sudo().create({
                    'name': filename,
                    'res_model': 'res.partner',
                    'partner_id': partner.id,
                    'type': 'binary',
                    'datas': base64.b64encode(file.read()).decode('utf-8'),
                    'mimetype': file.content_type,
                    'folder_id': existing_vendor_folder.id,
                })

        save_attachment(partner, post.get('gst_document'), 'GST Certificate')
        save_attachment(partner, post.get('pan_card'), 'PAN Card')
        save_attachment(partner, post.get('msme_certificate'), 'MSME Certificate')
        save_attachment(partner, post.get('cancel_cheque'), 'Cancelled Cheque')

        print("Document upload successful", partner.name)
        partner.document_recevied = True

        #After Uploading the documents by vendor to notify this information to group_purchase_manager
        group = request.env.ref('purchase.group_purchase_manager')
        users = group.users

        for user in users:
            subject = f"Vendor Documents Uploaded: {partner.name}"
            body_html = f"""
            <p>Hello {user.name},</p>
            <p>The vendor <strong>{partner.name}</strong> has uploaded their documents for verification.</p>
            <p>You can view the documents under their profile.</p>
            <p>With Regards,<br/>{user.company_id.name}</p>"""
            print("Mail send to : ", user.name)
            if user.email:
                request.env['mail.mail'].sudo().create({
                    'subject': subject,
                    'body_html': body_html,
                    'email_to': user.email,
                }).send()
                print("mail : ",user.email)

                

        return request.render('abcl_purchase.thank_you', {'partner': partner})