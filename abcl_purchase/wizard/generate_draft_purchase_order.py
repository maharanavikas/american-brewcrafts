from odoo import models, fields, api

class GenerateDraftPOWizard(models.TransientModel):
    _name = 'generate.draft.po.wizard'
    _description = 'Generate Draft Purchase Order Wizard'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    categ_id = fields.Many2one('product.category', string="Product Category", related="product_id.categ_id")
    # unit_price = fields.Float(string="Unit Price", compute="_compute_unit_price")
    vendor_id = fields.Many2one('res.partner', string="Vendor", domain="[('id', 'in', allowed_vendor_ids)]")
    allowed_vendor_ids = fields.Many2many('res.partner', string="Allowed Vendors", compute="_compute_allowed_vendors")
    supplierinfo_ids = fields.Many2many(
        'product.supplierinfo',
        string='Vendor Pricelists',
        readonly=True,
        compute='_compute_supplierinfo_ids'
    )

    @api.depends('product_id')
    def _compute_supplierinfo_ids(self):
        for wizard in self:
            if wizard.product_id:
                supplierinfos = self.env['product.supplierinfo'].search([
                    ('product_tmpl_id', '=', wizard.product_id.product_tmpl_id.id)
                ])
                wizard.supplierinfo_ids = supplierinfos
            else:
                wizard.supplierinfo_ids = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.allowed_vendor_ids = self.product_id.seller_ids.mapped('partner_id')

    # @api.depends('product_id', 'vendor_id')
    # def _compute_unit_price(self):
    #     for line in self:
    #         price = 0.0
    #         if line.product_id and line.vendor_id:
    #             seller = line.product_id.seller_ids.filtered(lambda s: s.partner_id.id == line.vendor_id.id)
    #             if seller:
    #                 price = seller[0].price
    #         line.unit_price = price

    @api.depends('product_id')
    def _compute_allowed_vendors(self):
        for rec in self:
            rec.allowed_vendor_ids = rec.product_id.seller_ids.mapped('partner_id')

    def action_generate_po(self):
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor_id.id,
            'product_categ_id': self.categ_id.id,
            'order_line': [(0, 0, {
                'product_id': self.product_id.id,
                'product_qty': 1,
                # 'price_unit': self.product_id.standard_price,
                'name': self.product_id.name,
                # 'date_planned': fields.Datetime.now(),
            })]
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Draft Purchase Order',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': po.id,
        }
