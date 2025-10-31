# -*- coding: utf-8 -*-
{
    'name': "ABCL Manufacturing",
    'summary': "American Brew Crafts Manufacturing Module",
    'description': """ABCL stock module customization for Manufacturing orders.""",

    'author': "Linkfields Innovations",
    'website': "https://www.linkfields.com",
    'maintainer': 'Linkfields Innovations',

    'sequence': 121,
    'category': 'Manufacturing/Manufacturing',
    'version': '18.0',

    'depends': ['base','mrp', 'mrp_mps', 'stock','purchase'],
    'data': [
        "security/ir.model.access.csv",
        "wizard/extra_production_wizard_views.xml",
        'views/mrp_production_views.xml',
        "views/mrp_bom_views.xml",
        'views/mrp_production_schedule.xml',
        'views/stock_quant_views.xml',
        'views/res_config_settings_views.xml',

    ],
    'assets': {
        'web.assets_backend': [
            'abcl_manufacturing/static/src/widgets/lots_dialog.js',
            'abcl_manufacturing/static/src/widgets/lots_dialog.xml',
        ],
    },
    'license': 'LGPL-3',
    'images': ['description/icon.svg']
}
