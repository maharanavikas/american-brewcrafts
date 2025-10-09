# -*- coding: utf-8 -*-

from odoo import  models, fields, api , _


class ImportPermit(models.Model):
    _name = "import.permit"
    _description = 'Import Permit Line'
    _rec_name = 'import_permit_no'

    import_permit_doc = fields.Binary("Import Permit", attachment=True, copy=False, exportable=False)
    import_permit_doc_name = fields.Char("Import Permit Doc Name")
    order_id = fields.Many2one(
                comodel_name='sale.order',
                string="Order Reference",
                required=True, ondelete='cascade', index=True, copy=False)
    import_permit_no = fields.Char("Import Permit No.", copy=False)
    import_permit_date = fields.Date("Import Permit Date", copy=False)
    import_permit_status = fields.Selection([
                            ('applied', 'Applied'),
                            ('in_progress', 'In Progress'),
                            ('rejected', 'Rejected'),
                            ('received', 'Received'),
                        ], string="Import Permit Status")
    import_status_display = fields.Char(string="Import Permit Status", compute='_compute_import_status_display')

    def _compute_import_status_display(self):
        for line in self:
            line.import_status_display = line.import_permit_status.capitalize() if line.import_permit_status else 'N/A'
            # order.export_status_display = order.export_permit_status.capitalize() if order.export_permit_status else 'N/A'

    def open_import_permit_status_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Update Import Permit Status',
            'view_mode': 'form',
            'res_model': 'permit.status.wizard',
            'target': 'new',
            'context': {
                'default_import_permit_line_id': self.id,
                'default_import_permit_status': self.import_permit_status,
                'default_import_permit_no': self.import_permit_no,
                'default_import_permit_date': self.import_permit_date,
                'default_permit_type': 'import'
            }
        }
    