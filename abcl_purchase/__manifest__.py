# -*- coding: utf-8 -*-
{
    'name': "ABCL Purchase",
    'summary': "American Brew Crafts Purchase Module",
    'description': """ABCL purchase module customization for creating purchase orders from portal.""",

    'author': "Linkfields Innovations",
    'website': "https://www.linkfields.com",
    'maintainer': 'Linkfields Innovations',

    'sequence': 121,
    'category': 'Inventory/Purchase',
    'version': '18.0',

    'depends': ['purchase', 'portal', 'website', 'product', 'abcl_base', 'l10n_in_purchase','stock','mail','product'],
    'data': [
        "security/ir.model.access.csv",
        'data/rejected_approved_mail_template.xml',
        'data/approval_mail_template.xml',
        "data/documents_folder_data.xml",
        'data/activity_data.xml',
        'data/vendor_pricelist_approval_template.xml',
        'data/vendor_pricelist_approve_or_rejected_template.xml',
        "wizard/purchase_close_reason_wizard_views.xml",
        "wizard/purchase_approval_comment_wizard_views.xml",
        "wizard/generate_draft_purchase_order.xml",
        "wizard/purchase_order_bulk_approval_wizard_views.xml",
        "wizard/vendor_pricelist_approve_wizard.xml",
        "views/res_partner_views.xml",
        "views/uom_uom_views.xml",
        "views/abcl_vendor_registration_mail.xml",
        "views/abcl_vendor_upload_template.xml",
        'views/product_category_views.xml',
        'views/portal_purchase_template.xml',
        'views/purchase_order_views.xml',
        'views/product_supplierinfo.xml',
        'views/product_views.xml',
        'views/purchase_close_reason_views.xml',
        'wizard/supplier_price_change_wizard_view.xml',
        'wizard/alternate_vendor_wizard_views.xml',
        'wizard/split_po_wizard_views.xml',
        # 'reports/purchase_order_template.xml',
        "views/pricelist_approval_log_views.xml",
    ],

    'assets': {
        'web.assets_frontend': [
            'abcl_purchase/static/src/js/portal_purchase.js',
        ],
        'web.assets_backend': [
            'abcl_purchase/static/src/js/draft_po_button.js',
            'abcl_purchase/static/src/xml/po_list_controller.xml',
        ],
    },
    'license': 'LGPL-3',
    'images': ['description/icon.svg'],
}
