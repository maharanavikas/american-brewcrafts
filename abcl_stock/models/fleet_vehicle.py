from odoo import api, fields, models, _

class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    vehicle_type = fields.Selection(selection_add=[('dcm', 'DCM'), ('mini_goods_van', 'Mini Goods Van'), ('tractor', 'Tractor')],ondelete={
        'dcm': 'set default',
        'mini_goods_van': 'set default',
        'tractor': 'set default',
    })