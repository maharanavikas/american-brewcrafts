# -*- coding: utf-8 -*-
{
    'name': "ABCL Accounting",
    'summary': "American Brew Crafts Accounting Module",
    'description': """ABCL accounting module and partner customization to adapt the invoicing format and layout.""",

    'author': "Linkfields Innovations",
    'website': "https://www.linkfields.com",
    'maintainer': 'Linkfields Innovations',

    'sequence': 120,
    'category': 'Accounting/Accounting',
    'version': '18.0',

    'depends': ['l10n_in','account', 'stock', 'abcl_sale', 'web'],
    'data': [
        'data/sequence.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/report_invoice.xml',
    ],
    'license': 'LGPL-3',
    'images': ['description/icon.svg']
}
