from odoo import models, fields, api

class SaleReport(models.Model):
    _inherit = 'sale.report'

    import_permit_status = fields.Selection(
        selection=[
            ('applied', 'Applied'),
            ('in_progress', 'In Progress'),
            ('rejected', 'Rejected'),
            ('received', 'Received'),
        ],
        string="Import Permit Status",
        readonly=True,
        aggregator='count_distinct',
    )

    export_permit_status = fields.Selection(
        selection=[
            ('applied', 'Applied'),
            ('in_progress', 'In Progress'),
            ('rejected', 'Rejected'),
            ('received', 'Received'),
        ],
        string="Export Permit Status",
        readonly=True,
        aggregator='count_distinct',
    )

    # def _select_additional_fields(self):
    #     res = super()._select_additional_fields()
    #     # res.update({
    #     #     'import_permit_status': 's.import_permit_status',
    #     #     'export_permit_status': 's.export_permit_status',
    #     # })
    #     return res

