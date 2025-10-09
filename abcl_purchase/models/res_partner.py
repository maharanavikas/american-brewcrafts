# -*- coding: utf-8 -*-
from odoo import models, fields, api
import uuid

class ResPartner(models.Model):
    _inherit = 'res.partner'

    verification_state = fields.Selection([('draft','Draft'),('pending_verification', 'Pending Verification'), ('verified', 'Verified')], string="Verification status", default='draft')
    gst_document = fields.Binary(string="GST Document", attachment=True)
    pan_card = fields.Binary(string="PAN Card" , attachment=True)
    msme_certificate = fields.Binary(string="MSME Certificate", attachment=True)
    cancel_cheque = fields.Binary(string="Cancelled Cheque", attachment=True)
    contact_person = fields.Char(string="Contact Person", attachment=True)
    mailing_address = fields.Char(string="Mailing Address", attachment=True)
    upload_access_key = fields.Char(string="Upload Access Key", default=lambda self: str(uuid.uuid4()), required=True ,readonly=True)
    supplier_pricelist_count = fields.Integer(string="Supplier Pricelists", compute="_compute_supplier_pricelist_count")
    contact_type = fields.Selection([('customer','Customer'),('vendor','Vendor')], string="Type")
    document_recevied = fields.Boolean(string="Document Received")
    supplier_pricelist_ids = fields.One2many(
        "product.supplierinfo", "partner_id", string="Vendor Pricelists"
    )

    def action_verified(self):
        self.verification_state = 'verified'
    
    def action_send_document_upload_link(self):
        self.verification_state = 'pending_verification'
        self.document_recevied = False
        template = self.env.ref('abcl_purchase.email_template_document_upload_link')
        template.send_mail(self.id)


    def _compute_supplier_pricelist_count(self):
        for partner in self:
            partner.supplier_pricelist_count = self.env['product.supplierinfo'].search_count([
                ('partner_id', '=', partner.id)
            ])

    def action_open_supplier_pricelist(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Pricelists',
            'res_model': 'product.supplierinfo',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': dict(self.env.context, default_name=self.id, visible_product_tmpl_id=False)
        }