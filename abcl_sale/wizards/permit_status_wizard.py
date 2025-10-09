# -*- coding: utf-8 -*-
from odoo import models, fields, api

class PermitStatusWizard(models.TransientModel):
    _name = 'permit.status.wizard'
    _description = 'Permit Status Wizard'

    import_permit_line_id = fields.Many2one('import.permit', string="Import Permit Line", readonly=True)
    export_permit_line_id = fields.Many2one('export.permit', string="Export Permit Line", readonly=True)
    import_permit_status = fields.Selection([
        ('applied', 'Applied'),
        ('in_progress', 'In Progress'),
        ('rejected', 'Rejected'),
        ('received', 'Received'),
    ], string="Import Permit Status")
    export_permit_status = fields.Selection([
        ('applied', 'Applied'),
        ('in_progress', 'In Progress'),
        ('rejected', 'Rejected'),
        ('received', 'Received'),
    ], string="Export Permit Status")
    import_permit_no = fields.Char("Import Permit No.")
    import_permit_date = fields.Date("Import Permit Date")
    export_permit_no = fields.Char("Export Permit Application No.")
    export_permit_date = fields.Date("Export Permit Application Date")
    permit_type = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export')
    ], required=True)

    def action_update_permit_status(self):
        if self.import_permit_line_id and self.permit_type == 'import':
            self.import_permit_line_id.write({
                'import_permit_status': self.import_permit_status,
                'import_permit_no': self.import_permit_no,
                'import_permit_date': self.import_permit_date
            })
        if self.permit_type == 'export' and self.export_permit_line_id:
            self.export_permit_line_id.write({
                'export_permit_status': self.export_permit_status,
                'export_permit_no': self.export_permit_no,
                'export_permit_date': self.export_permit_date
            })
