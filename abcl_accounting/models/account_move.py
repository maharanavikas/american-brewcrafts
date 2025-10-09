# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    # import_permit_no = fields.Char("Import Permit No.")
    # import_permit_date = fields.Date("Import Permit Date")
    # export_permit_no = fields.Char("Export Permit Application No.")
    # export_permit_date = fields.Date("Export Permit Application Date")
    excise_leaf_no = fields.Char("Excise Leaf No.")
    transporter = fields.Char("Transporter")
    vehicle_no = fields.Char("Vehicle No.")
    transport_permit_no = fields.Char("Transport Permit No.")
    lr_gc_lwb_no = fields.Char("LR/GC/LWB No.")
    lr_gc_lwb_date = fields.Date("LR/GC/LWB Date")
    po_no = fields.Char("PO No.")
    po_date = fields.Date("PO Date")
    lr_no = fields.Char("LR No.")
    prepared_by_signature = fields.Char(string='Prepared By', help="Name of the person who prepared this document")
    checked_by_signature = fields.Char(string='Checked By', help="Name of the person who verified this document")
    abcl_invoice_sequence = fields.Char(string="Invoice Sequence")
    related_sale_order_ids = fields.Many2many(
        'sale.order',
        string='Related Sale Orders',
        compute='_compute_related_sale_orders',
        store=False
    )

    import_permit_id = fields.Many2one("import.permit", string="Import Permit")
    import_permit_date = fields.Date(string="Import Permit Date",)
    export_permit_id = fields.Many2one("export.permit", string="Export Permit")
    export_permit_date = fields.Date(string="Export Permit Date")
    vehicle_type = fields.Selection([('owned', 'Owned'), ('rented', 'Rented')], "Vehicle Type")
    vehicle_detail_id = fields.Many2one('fleet.vehicle', string="Our Vehicle Details")

    stock_picking_id = fields.Many2one('stock.picking', string='Delivery Order', help="Related Delivery Order for this Invoice", domain="[('sale_id', 'in', related_sale_order_ids)]")

    @api.depends('invoice_line_ids.sale_line_ids.order_id')
    def _compute_related_sale_orders(self):
        for invoice in self:
            invoice.related_sale_order_ids = invoice.invoice_line_ids.mapped('sale_line_ids.order_id')


    # @api.onchange('stock_picking_id')
    # def _onchange_stock_picking_id(self):
    #     if self.stock_picking_id:
    #         picking = self.stock_picking_id
    #
    #         self.import_permit_id = picking.import_permit_id.id
    #         self.export_permit_id = picking.export_permit_id.id
    #         self.excise_leaf_no = picking.excise_leaf_no
    #         self.transporter = picking.transporter
    #         self.vehicle_type = picking.vehicle_type
    #         self.vehicle_no = picking.vehicle_no
    #         self.vehicle_detail_id = picking.vehicle_detail_id.id
    #         self.transport_permit_no = picking.transport_permit_no
    #         self.lr_gc_lwb_no = picking.lr_gc_lwb_no
    #         self.lr_gc_lwb_date = picking.lr_gc_lwb_date
    #         self.lr_no = picking.lr_no
    #         self.import_permit_date = picking.import_permit_date
    #         self.export_permit_date = picking.export_permit_date
    #         self.po_no = picking.po_no
    #         self.po_date = picking.po_date
    @api.onchange('stock_picking_id')
    def _onchange_stock_picking_id(self):
        if self.stock_picking_id:
            picking = self.stock_picking_id

            self.import_permit_id = picking.import_permit_id.id or False
            self.export_permit_id = picking.export_permit_id.id or False
            self.excise_leaf_no = picking.excise_leaf_no or ''
            self.transporter = picking.transporter or ''
            self.vehicle_type = picking.vehicle_type or ''
            self.vehicle_no = picking.vehicle_no or ''
            self.vehicle_detail_id = picking.vehicle_detail_id.id or False
            self.transport_permit_no = picking.transport_permit_no or ''
            self.lr_gc_lwb_no = picking.lr_gc_lwb_no or ''
            self.lr_gc_lwb_date = picking.lr_gc_lwb_date or False
            self.lr_no = picking.lr_no or ''
            self.import_permit_date = picking.import_permit_date or False
            self.export_permit_date = picking.export_permit_date or False
            self.po_no = picking.po_no or ''
            self.po_date = picking.po_date or False
        else:
            # Reset all fields if stock_picking_id is cleared
            self.import_permit_id = False
            self.export_permit_id = False
            self.excise_leaf_no = ''
            self.transporter = ''
            self.vehicle_type = ''
            self.vehicle_no = ''
            self.vehicle_detail_id = False
            self.transport_permit_no = ''
            self.lr_gc_lwb_no = ''
            self.lr_gc_lwb_date = False
            self.lr_no = ''
            self.import_permit_date = False
            self.export_permit_date = False
            self.po_no = ''
            self.po_date = False








