# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    dispatch_checklist_id = fields.Many2one('sign.template', string="Dispatch Check List", related="sale_id.dispatch_checklist_id", copy=False)
    sign_request_id = fields.Many2one('sign.request', string="Sign Request", readonly=True, tracking=True, copy=False)
    sign_request_state = fields.Selection(
        related='sign_request_id.state',
        string='Sign Request State',
        store=True, copy=False
    )

    signature_state = fields.Selection(selection=[('darft', 'Draft'), ('signed', 'Fully Signed')], string=' State', default="darft")

    signer_ids = fields.One2many(
        related='sign_request_id.request_item_ids',
        string='Signers',
        readonly=False,
        store=False, copy=False
    )
    total_qty = fields.Float("Total Quantity", compute='_compute_total_qty', store=False)
    total_bulk_liter = fields.Float("Total Bulk Liter", compute='_compute_bulk_beer_qty', store=False)

    import_permit_id = fields.Many2one("import.permit",string="Import Permit", domain="[('order_id','=',sale_id)]")
    import_permit_date = fields.Date(related="import_permit_id.import_permit_date", string="Import Permit Date", store=True)
    import_permit_doc = fields.Binary("Import Permit Document", store=True, compute="_compute_import_permit_doc")
    import_permit_doc_name = fields.Char(related="import_permit_id.import_permit_doc_name", string="Import Permit Doc Name", store=True)
    export_permit_id = fields.Many2one("export.permit",string="Export Permit", domain="[('order_id','=',sale_id)]")
    export_permit_date = fields.Date(related="export_permit_id.export_permit_date", string="Export Permit Date", store=True)
    export_permit_doc = fields.Binary("Export Permit Document", store=True, compute="_compute_export_permit_doc")
    export_permit_doc_name = fields.Char(related="export_permit_id.export_permit_doc_name", string="Export Permit Doc Name", store=True)

    excise_leaf_no = fields.Char("Excise Leaf No.")
    transporter = fields.Char("Transporter")
    vehicle_type =fields.Selection(selection=[('internal','Internal'),('external','External')],string="Vehicle Type")
    vehicle_no = fields.Char("Vehicle No.")
    vehicle_detail_id = fields.Many2one('fleet.vehicle', string="Select Vehicle")
    transport_permit_no = fields.Char("Transport Permit No.")
    lr_gc_lwb_no = fields.Char("LR/GC/LWB No.")
    lr_gc_lwb_date = fields.Date("LR/GC/LWB Date")
    po_no = fields.Char("PO No.")
    po_date = fields.Date("PO Date")
    lr_no = fields.Char("LR No.")
    state = fields.Selection(readonly=False)

    finance_user_id = fields.Many2one('res.users', string='Accountant')
    access_token = fields.Char("Access Token", copy=False, required=True, default=lambda s: uuid.uuid4().hex, size=43)
    dispatch_signed_by = fields.Char()
    dispatch_signature = fields.Binary()
    accountant_signed_by = fields.Char()
    accountant_signature = fields.Binary()
    is_dispatch_sent = fields.Boolean(default=False)
    
    dispatch_date = fields.Char("Dispatch Date")
    remarks = fields.Char('Remarks')
    status = fields.Boolean('Status')

    partner_state_code = fields.Char(
        string="Partner State Code",
        related='partner_id.state_id.code',
        store=True, readonly=True,
    )
    delivery_route = fields.Text("Delivery Route")
    validity_from_date = fields.Date("Export Valid From")
    validity_to_date = fields.Date("Export Valid Upto")
    alcohol_strength_id = fields.Many2one('alcohol.strength', "Alcohol Strength")
    days_for_validity_expiry = fields.Integer("Days for Validity Expiry", compute='_compute_days_for_validity_expiry')

    invoice_count = fields.Integer(
        string="Invoice Count",
        compute="_compute_invoice_count"
    )

    def _compute_invoice_count(self):
        for picking in self:
            invoice_count = self.env['account.move'].search_count([('stock_picking_id', '=', picking.id), ('move_type', '=', 'out_invoice')])
            picking.invoice_count = invoice_count

    @api.depends('scheduled_date','validity_to_date')
    def _compute_days_for_validity_expiry(self):
        for record in self:
            if record.validity_to_date and record.scheduled_date:
                delta = record.validity_to_date - record.scheduled_date.date()
                record.days_for_validity_expiry = delta.days
            else:
                record.days_for_validity_expiry = 0

    # Gate Pass Fields
    gp_p_no_date = fields.Char("TP No.")
    gp_p_no_date_remarks = fields.Char('Remarks')
    gp_p_no_date_status = fields.Boolean('Status')
    gp_tp_date = fields.Date("TP Date")
    gp_tp_date_remarks = fields.Char('Remarks')
    gp_tp_date_status = fields.Boolean('Status')
    gp_party_name = fields.Char("Party Name")
    gp_party_name_remarks = fields.Char('Remarks')
    gp_party_name_status = fields.Boolean('Status')
    gp_pack_size = fields.Selection([('', 'Select Size'),
                                ('330', '330 ml'), 
                                    ('500', '500 ml'), 
                                    ('650', '650 ml')], string="Pack Size")
    gp_pack_size_remarks = fields.Char('Remarks')
    gp_pack_size_status = fields.Boolean('Status')
    gp_quantity = fields.Char("Quantity")
    gp_quantity_remarks = fields.Char('Remarks')
    gp_quantity_status = fields.Boolean('Status')
    gp_brand = fields.Char("Brand")
    gp_brand_remarks = fields.Char('Remarks')
    gp_brand_status = fields.Boolean('Status')
    gp_vehicle_no_date = fields.Char("Vehicle No & Date")
    gp_vehicle_no_date_remarks = fields.Char('Remarks')
    gp_vehicle_no_date_status = fields.Boolean('Status')

    # LR Copy fields
    lrc_lr_no = fields.Char("LR No")
    lrc_lr_no_remarks = fields.Char('Remarks')
    lrc_lr_no_status = fields.Boolean('Status')
    lrc_lr_date = fields.Char("LR Date")
    lrc_lr_date_remarks = fields.Char('Remarks')
    lrc_lr_date_status = fields.Boolean('Status')
    lrc_lr_vehicle_no_address = fields.Char("Vehicle no. To address")
    lrc_lr_vehicle_no_address_remarks = fields.Char('Remarks')
    lrc_lr_vehicle_no_address_status = fields.Boolean('Status')
    lrc_lr_quantity = fields.Char("Quantity")
    lrc_lr_quantity_remarks = fields.Char('Remarks')
    lrc_lr_quantity_status = fields.Boolean('Status')
    lrc_lr_invoice_no_date = fields.Char("Invoice no & Invoice date")
    lrc_lr_invoice_no_date_remarks = fields.Char('Remarks')
    lrc_lr_invoice_no_date_status = fields.Boolean('Status')

    # Transport Permit
    tp_date = fields.Char("Date")
    tp_date_remarks = fields.Char('Remarks')
    tp_date_status = fields.Boolean('Status')
    tp_brand = fields.Char("Brand")
    tp_brand_remarks = fields.Char('Remarks')
    tp_brand_status = fields.Boolean('Status')
    tp_batch_no = fields.Char("Batch No.")
    tp_batch_no_remarks = fields.Char('Remarks')
    tp_batch_no_status = fields.Boolean('Status')
    tp_po_no_date = fields.Char("PO No. & Date")
    tp_po_no_date_remarks = fields.Char('Remarks')
    tp_po_no_date_status = fields.Boolean('Status')
    tp_quantity = fields.Char("Quantity")
    tp_quantity_remarks = fields.Char('Remarks')
    tp_quantity_status = fields.Boolean('Status')
    tp_pack_size = fields.Selection([('', 'Select Size'),
                                ('330', '330 ml'), 
                                    ('500', '500 ml'), 
                                    ('650', '650 ml')], string="Pack Size")
    tp_pack_size_remarks = fields.Char('Remarks')
    tp_pack_size_status = fields.Boolean('Status')
    tp_bulk_litre = fields.Char("Bulk Litre")
    tp_bulk_litre_remarks = fields.Char('Remarks')
    tp_bulk_litre_status = fields.Boolean('Status')
    tp_alcohol_percent = fields.Char("Alcohol %")
    tp_alcohol_percent_remarks = fields.Char('Remarks')
    tp_alcohol_percent_status = fields.Boolean('Status')
    tp_excise_duty_challan_no_date = fields.Char("Excise duty challan No.& Date")
    tp_excise_duty_challan_no_date_remarks = fields.Char('Remarks')
    tp_excise_duty_challan_no_date_status = fields.Boolean('Status')
    tp_excise_duty = fields.Char("Excise Duty")
    tp_excise_duty_remarks = fields.Char('Remarks')
    tp_excise_duty_status = fields.Boolean('Status')
    tp_depot = fields.Char("Depot")
    tp_depot_remarks = fields.Char('Remarks')
    tp_depot_status = fields.Boolean('Status')
    tp_vehicle_route = fields.Char("Vehicle No. Route")
    tp_vehicle_route_remarks = fields.Char('Remarks')
    tp_vehicle_route_status = fields.Boolean('Status')
    tp_permit_validity_date = fields.Char("Permit validity date & BO signature.")
    tp_permit_validity_date_remarks = fields.Char('Remarks')
    tp_permit_validity_date_status = fields.Boolean('Status')

    # Export Pass Fields
    e_pass_permit_no = fields.Char("Export permit No.")
    e_pass_permit_no_remarks = fields.Char('Remarks')
    e_pass_permit_no_status = fields.Boolean('Status')
    e_pass_dispatch_date_time = fields.Char("Dispatch date & time")
    e_pass_dispatch_date_time_remarks = fields.Char('Remarks')
    e_pass_dispatch_date_time_status = fields.Boolean('Status')
    e_pass_import_validity = fields.Char("Import permit Validity days")
    e_pass_import_validity_remarks = fields.Char('Remarks')
    e_pass_import_validity_status = fields.Boolean('Status')
    e_pass_quantity = fields.Char("Quantity")
    e_pass_quantity_remarks = fields.Char('Remarks')
    e_pass_quantity_status = fields.Boolean('Status')
    e_pass_brand = fields.Char("Brand")
    e_pass_brand_remarks = fields.Char('Remarks')
    e_pass_brand_status = fields.Boolean('Status')
    e_pass_size = fields.Selection([('', 'Select Size'),
                                ('330', '330 ml'), 
                                    ('500', '500 ml'), 
                                    ('650', '650 ml')], string="Size 330/650/500 ml")
    e_pass_size_remarks = fields.Char('Remarks')
    e_pass_size_status = fields.Boolean('Status')
    e_pass_alcohol_strength = fields.Char("Alcohol Strength")
    e_pass_alcohol_strength_remarks = fields.Char('Remarks')
    e_pass_alcohol_strength_status = fields.Boolean('Status')
    e_pass_route_validity = fields.Char("Route & Validity of Export Permit")
    e_pass_route_validity_remarks = fields.Char('Remarks')
    e_pass_route_validity_status = fields.Boolean('Status')

    #EVC Fields
    evc_quantity = fields.Char("Quantity")
    evc_quantity_remarks = fields.Char('Remarks')
    evc_quantity_status = fields.Boolean('Status')
    evc_brand = fields.Char("Brand")
    evc_brand_remarks = fields.Char('Remarks')
    evc_brand_status = fields.Boolean('Status')
    evc_export_permit_no_date = fields.Char("Export Permit No. & date")
    evc_export_permit_no_date_remarks = fields.Char('Remarks')
    evc_export_permit_no_date_status = fields.Boolean('Status')
    evc_import_permit_no_date = fields.Char("Import permit No. & date")
    evc_import_permit_no_date_remarks = fields.Char('Remarks')
    evc_import_permit_no_date_status = fields.Boolean('Status')
    evc_tp_no_date = fields.Char("TP no. & date")
    evc_tp_no_date_remarks = fields.Char('Remarks')
    evc_tp_no_date_status = fields.Boolean('Status')
    evc_vehicle_no = fields.Char("Vehicle No.")
    evc_vehicle_no_remarks = fields.Char('Remarks')
    evc_vehicle_no_status = fields.Boolean('Status')

    # Export Permit Fields
    e_permit_ofs_no_date = fields.Char("OFS No. & Date")
    e_permit_ofs_no_date_remarks = fields.Char('Remarks')
    e_permit_ofs_no_date_status = fields.Boolean('Status')
    e_permit_lr_copy_no_date = fields.Char("LR copy No. & date")
    e_permit_lr_copy_no_date_remarks = fields.Char('Remarks')
    e_permit_lr_copy_no_date_status = fields.Boolean('Status')
    e_permit_vehicle_no = fields.Char("Vehicle No.")
    e_permit_vehicle_no_remarks = fields.Char('Remarks')
    e_permit_vehicle_no_status = fields.Boolean('Status')
    e_permit_deport_name = fields.Char("Depot name")
    e_permit_deport_name_remarks = fields.Char('Remarks')
    e_permit_deport_name_status = fields.Boolean('Status')
    e_permit_brand = fields.Char("Brand")
    e_permit_brand_remarks = fields.Char('Remarks')
    e_permit_brand_status = fields.Boolean('Status')
    e_permit_batch_qty_size = fields.Char("Batch No. Quantity & size 330/650/500ml")
    e_permit_batch_qty_size_remarks = fields.Char('Remarks')
    e_permit_batch_qty_size_status = fields.Boolean('Status')
    e_permit_no = fields.Char("Export permit No.")
    e_permit_no_remarks = fields.Char('Remarks')
    e_permit_no_status = fields.Boolean('Status')

    # Import Permit Fields
    i_permit_no_date = fields.Char("Import Permit No. & date")
    i_permit_no_date_remarks = fields.Char('Remarks')
    i_permit_no_date_status = fields.Boolean('Status')
    i_permit_validity = fields.Char("Permit validity")
    i_permit_validity_remarks = fields.Char('Remarks')
    i_permit_validity_status = fields.Boolean('Status')
    i_permit_brand = fields.Char("Brand")
    i_permit_brand_remarks = fields.Char('Remarks')
    i_permit_brand_status = fields.Boolean('Status')
    i_permit_size = fields.Selection([('', 'Select Size'),
                                ('330', '330 ml'), 
                                    ('500', '500 ml'), 
                                    ('650', '650 ml')], string="Size 330/650/500 ml")
    i_permit_size_remarks = fields.Char('Remarks')
    i_permit_size_status = fields.Boolean('Status')
    i_permit_qty_sign_stamp = fields.Char("Quantity & BO signature & Stamp")
    i_permit_qty_sign_stamp_remarks = fields.Char('Remarks')
    i_permit_qty_sign_stamp_status = fields.Boolean('Status')

    # Invoice Fields
    invoice_no_date = fields.Char("Invoice No & date")
    invoice_no_date_remarks = fields.Char('Remarks')
    invoice_no_date_status = fields.Boolean('Status')
    invoice_gate_pass_date = fields.Char("Gate pass date")
    invoice_gate_pass_date_remarks = fields.Char('Remarks')
    invoice_gate_pass_date_status = fields.Boolean('Status')
    invoice_transport = fields.Char("Transport name")
    invoice_transport_remarks = fields.Char('Remarks')
    invoice_transport_status = fields.Boolean('Status')
    invoice_vehicle_no = fields.Char("Vehicle No")
    invoice_vehicle_no_remarks = fields.Char('Remarks')
    invoice_vehicle_no_status = fields.Boolean('Status')
    invoice_tp_lr_no = fields.Char("TP No. LR No.")
    invoice_tp_lr_no_remarks = fields.Char('Remarks')
    invoice_tp_lr_no_status = fields.Boolean('Status')
    invoice_ofs_no_date = fields.Char("OFS No. & date")
    invoice_ofs_no_date_remarks = fields.Char('Remarks')
    invoice_ofs_no_date_status = fields.Boolean('Status')
    invoice_brand = fields.Char("Brand")
    invoice_brand_remarks = fields.Char('Remarks')
    invoice_brand_status = fields.Boolean('Status')
    invoice_batch_no = fields.Char("Batch No.")
    invoice_batch_no_remarks = fields.Char('Remarks')
    invoice_batch_no_status = fields.Boolean('Status')
    invoice_quantity = fields.Char("Quantity")
    invoice_quantity_remarks = fields.Char('Remarks')
    invoice_quantity_status = fields.Boolean('Status')
    invoice_basic_price = fields.Char("Basic Price")
    invoice_basic_price_remarks = fields.Char('Remarks')
    invoice_basic_price_status = fields.Boolean('Status')
    inovice_excise_duty = fields.Char("Excise Duty")
    inovice_excise_duty_remarks = fields.Char('Remarks')
    inovice_excise_duty_status = fields.Boolean('Status')
    inovice_liter_total_value = fields.Char("Bulk Litre & Invoice Total Value in Rs.")
    inovice_liter_total_value_remarks = fields.Char('Remarks')
    inovice_liter_total_value_status = fields.Boolean('Status')

    # Road Permit
    rp_doc_availability = fields.Char("Document availability")
    rp_doc_availability_remarks = fields.Char('Remarks')
    rp_doc_availability_status = fields.Boolean('Status')

    # Dispatch Note
    dn_brand = fields.Char("Brand")
    dn_brand_remarks = fields.Char('Remarks')
    dn_brand_status = fields.Boolean('Status')
    dn_size = fields.Selection([('', 'Select Size'),
                                ('330', '330 ml'), 
                                ('500', '500 ml'), 
                                ('650', '650 ml')], string="Size 330/650/500 ml")
    dn_size_remarks = fields.Char('Remarks')
    dn_size_status = fields.Boolean('Status')
    dn_qty = fields.Char("Quantity")
    dn_qty_remarks = fields.Char('Remarks')
    dn_qty_status = fields.Boolean('Status')
    dn_depot_name = fields.Char("Depot name")
    dn_depot_name_remarks = fields.Char('Remarks')
    dn_depot_name_status = fields.Boolean('Status')
    dn_permit_no = fields.Char("Permit No.")
    dn_permit_no_remarks = fields.Char('Remarks')
    dn_permit_no_status = fields.Boolean('Status')
    dn_transportor_add = fields.Char("Transporter Address")
    dn_transportor_add_remarks = fields.Char('Remarks')
    dn_transportor_add_status = fields.Boolean('Status')
    dn_vehicle_godown_add = fields.Char("Vehicle No. Driver name & Godown address")
    dn_vehicle_godown_add_remarks = fields.Char('Remarks')
    dn_vehicle_godown_add_status = fields.Boolean('Status')

    # Unloading Challan
    uc_brand = fields.Char("Brand")
    uc_brand_remarks = fields.Char('Remarks')
    uc_brand_status = fields.Boolean('Status')
    uc_qty_depot = fields.Char("Quantity & Depot")
    uc_qty_depot_remarks = fields.Char('Remarks')
    uc_qty_depot_status = fields.Boolean('Status')

    # Brand Registration
    br_availability = fields.Char("Ensure availability")
    br_availability_remarks = fields.Char('Remarks')
    br_availability_status = fields.Boolean('Status')

    checklist_ids = fields.One2many('dispatch.checklist', 'picking_id', string='Dispatch Checklists')
    product_qty_uom_summary = fields.Char(
        string="Products (Qty/UoM)",
        compute="_compute_product_qty_uom_summary",
    )
    export_pass_doc = fields.Binary("Export Pass", attachment=True, copy=False, exportable=False)
    export_pass_doc_name = fields.Char("Export Pass Name")
    issue_slip_doc = fields.Binary("Issue Slip", attachment=True, copy=False, exportable=False)
    issue_slip_doc_name = fields.Char("Issue Slip Name")

    @api.depends('move_ids_without_package.product_id','move_ids_without_package.product_uom_qty','move_ids_without_package.product_uom')
    def _compute_product_qty_uom_summary(self):
        for picking in self:
            lines = []
            for move in picking.move_ids_without_package:
                name = move.product_id.display_name or ''
                qty = move.product_uom_qty or 0
                uom = move.product_uom.name or ''
                lines.append(f"{name} / {qty} / {uom}")
            picking.product_qty_uom_summary = ", ".join(lines)

    def _compute_total_qty(self):
        all_goods_lines = self.move_ids_without_package.filtered(lambda move: move.product_id.type == 'consu')
        total_goods_qty = sum(product.quantity for product in all_goods_lines)
        self.total_qty = total_goods_qty

    def _compute_bulk_beer_qty(self):
        all_goods_lines = self.move_ids_without_package.filtered(lambda move: move.product_id.type == 'consu')
        bulk_liter = sum(product.product_bulk_liter for product in all_goods_lines)
        self.total_bulk_liter = bulk_liter

    @api.model
    def _validate_access_token(self, access_token):
        return self.sudo().search([('access_token', '=', access_token)], limit=1)

    def _get_dispatch_checklist_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/dispatch_checklist/{self.access_token}"

    @api.onchange('vehicle_detail_id')
    def change_vehicle(self):
        for record in self:
            vehicle_detail_id = record.vehicle_detail_id
            if vehicle_detail_id:
                record.vehicle_no = vehicle_detail_id.license_plate
            else:
                record.vehicle_no = False

    # def open_sign_wizard(self):
    #     self.ensure_one()
    #     signer_lines = []
    #     if self.dispatch_checklist_id:
    #         for signer in self.dispatch_checklist_id.signer_ids:
    #             if not signer.role_id:
    #                 continue
    #             signer_lines.append((0, 0, {
    #                 'role_id': signer.role_id.id,
    #                 'partner_id': signer.partner_id.id,
    #                 'mail_sent_order': signer.mail_sent_order or 1,
    #             }))

    #     wizard = self.env['stock.picking.sign.request.wizard'].create({
    #         'stock_picking_id': self.id,
    #         'signer_request_ids': signer_lines,
    #     })

    #     return {
    #         'name': "Stock Picking Sign Request",
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'stock.picking.sign.request.wizard',
    #         'res_id': wizard.id,
    #         'target': 'new',
    #         'view_id': self.env.ref('abcl_sale.stock_picking_sign_request_wizard_form_view').id,
    #     }
    
    def open_sign_wizard(self):
        self.ensure_one()
        wizard = self.env['dispatch.checklist.wizard'].create({
            'stock_picking_id': self.id,
            'dispatch_user_id': self.user_id.id or False,
            'accountant_user_id': self.finance_user_id.id or False,
            'order_responsible': 1,
            'order_accountant': 2,
        })
        return {
            'name': _("Stock Picking Dispatch Request"),
            'type': 'ir.actions.act_window',
            'res_model': 'dispatch.checklist.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'view_id': self.env.ref('abcl_sale.dispatch_checklist_wizard_form_view').id,
        }
    
    def action_review_dispatch_checkilist_template(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self._get_review_url()
        }

    def _get_review_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        dispatch_review_url = f"{base_url}/dispatch_checklist/preview/{self.access_token}"
        return dispatch_review_url

    def download_dispatch_checklist_pdf(self):
        return self.env.ref('abcl_sale.report_dispatch_checklist_details').report_action(self)
    
    @api.depends('import_permit_id')
    def _compute_import_permit_doc(self):
        for record in self:
            record.import_permit_doc = record.import_permit_id.import_permit_doc

    @api.depends('export_permit_id')
    def _compute_export_permit_doc(self):
        for record in self:
            record.export_permit_doc = record.export_permit_id.export_permit_doc
    
    def action_view_invoices(self):
        self.ensure_one()
        if self.invoice_count == 1:
            return {
                'name': 'Invoices',
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'domain': [('stock_picking_id', '=', self.id)],
                'res_id': self.env['account.move'].search([('stock_picking_id', '=', self.id)], limit=1).id,
            }
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('stock_picking_id', '=', self.id)],
            'context': dict(self._context, create=False),
        }

class StockMove(models.Model):
    _inherit = 'stock.move'

    product_status = fields.Boolean(string='Status')
    product_remark = fields.Char(string='Remarks')
    batch_number = fields.Char("Batch No")
    # related='product_id.product_tmpl_id.bulk_beer_per_litre'
    product_bulk_liter = fields.Float( string="Bulk Liter", store=True, compute='_compute_bulk_liter')

    @api.depends('quantity')
    def _compute_bulk_liter(self):
        print("**********_compute_bulk_liter**********")
        for move in self:
            move.product_bulk_liter = move.product_id.bulk_beer_per_liter * move.quantity

    