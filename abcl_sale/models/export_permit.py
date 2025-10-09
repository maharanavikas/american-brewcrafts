# -*- coding: utf-8 -*-

from odoo import  models, fields, api , _


class ExportPermit(models.Model):
    _name = "export.permit"
    _description = 'Export Permit Line'
    _rec_name = 'export_permit_no'

    export_permit_doc = fields.Binary("Export Permit", attachment=True, copy=False, exportable=False)
    export_permit_doc_name = fields.Char("Export Permit Doc Name")
    order_id = fields.Many2one(
                comodel_name='sale.order',
                string="Order Reference",
                required=True, ondelete='cascade', index=True, copy=False)
    export_permit_no = fields.Char("Export Permit Application No.", copy=False)
    export_permit_date = fields.Date("Export Permit Application Date", copy=False)
    export_permit_status = fields.Selection([
        ('applied', 'Applied'),
        ('in_progress', 'In Progress'),
        ('rejected', 'Rejected'),
        ('received', 'Received'),], string="Export Permit Status")
    export_status_display = fields.Char(string="Export Permit Status", compute='_compute_export_status_display')
    
    def _compute_export_status_display(self):
        for line in self:
            # line.import_status_display = line.import_permit_status.capitalize() if line.import_permit_status else 'N/A'
            line.export_status_display = line.export_permit_status.capitalize() if line.export_permit_status else 'N/A'

    def open_export_permit_status_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Update Export Permit Status',
            'view_mode': 'form',
            'res_model': 'permit.status.wizard',
            'target': 'new',
            'context': {
                'default_export_permit_line_id': self.id,
                'default_export_permit_no': self.export_permit_no,
                'default_export_permit_date': self.export_permit_date,
                'default_export_permit_status': self.export_permit_status,
                'default_permit_type': 'export'
            }
        }

    
    _sql_constraints = [("export_permit_number_code_unique", "unique(export_permit_number)","Export code must be unique")]
    