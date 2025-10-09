# -*- coding: utf-8 -*-
{
    'name': "ABCL Stock",
    'summary': "American Brew Crafts Stock Module",
    'description': """ABCL stock module customization for Gate entry details.""",

    'author': "Linkfields Innovations",
    'website': "https://www.linkfields.com",
    'maintainer': 'Linkfields Innovations',

    'sequence': 121,
    'category': 'Inventory/Inventory',
    'version': '18.0',

    'depends': ['stock', 'quality', 'spreadsheet', 'quality_control', 'fleet','website','quality_mrp', 'mrp', 'stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'data/abcl_stock_activity_data.xml',
        'data/delivery_approval_template.xml',
        'data/delivery_order_approved_template.xml',
        'data/quality_check_fail_template.xml',
        'data/quality_check_pass_template.xml',
        'data/fleet_tracking_mail.xml',
        'wizard/quality_approval_wizard_views.xml',
        'views/stock_picking_views.xml',
        'views/portal_delivery_template.xml',
        'views/stock_warehouse_views.xml',
        'views/quality_point_views.xml',
        'views/quality_check_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/abcl_excise_report.xml',
        'data/fleet_tracking_form.xml',
        'views/stock_lot_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_valuation_layer_views.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'abcl_stock/static/src/js/portal_delivery_order.js',
        ],
    },
    'license': 'LGPL-3',
    'images': ['description/icon.svg']
}
